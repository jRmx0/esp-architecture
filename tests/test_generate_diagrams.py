"""Run: python -m unittest discover -s tests"""
import contextlib
import copy
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "tools"))
import generate_diagrams as gd  # noqa: E402
from test_check_architecture import FILES, MANIFEST, Project  # noqa: E402

FULL = dict(copy.deepcopy(MANIFEST), **{
    "context": {"actors": [{"id": "user", "kind": "person", "description": 'says "hi"'}],
                "flows": [{"from": "user", "to": "system", "data": "button press"}]},
    "hardware": {"buses": [{"id": "spi2", "kind": "spi", "description": "SPI"}],
                 "devices": [{"id": "nor", "bus": "spi2", "description": "NOR flash"}]},
    "tasks": [{"id": "ui_task", "component": "ui", "priority": 3, "stack": 4096}],
})
FULL["components"][1]["hardware"] = ["spi2"]


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gd.main(["generate_diagrams.py", *args])
    return code, out.getvalue(), err.getvalue()


class Render(unittest.TestCase):
    def setUp(self):
        self.text = gd.render(copy.deepcopy(FULL), "arch/architecture.yaml")

    def test_four_diagrams_in_order(self):
        heads = [l for l in self.text.splitlines() if l.startswith("## ")]
        self.assertEqual(heads, ["## Context", "## Block", "## Organigram", "## Layering"])
        self.assertEqual(self.text.count("```mermaid"), 4)

    def test_quotes_escaped_and_ids_prefixed(self):
        self.assertIn("says #quot;hi#quot;", self.text)
        self.assertIn("n_user -->|", self.text)

    def test_block_puts_devices_outside_the_chip(self):
        block = self.text.split("## Block")[1].split("## Organigram")[0]
        self.assertIn("block-beta", block)
        inside = block.split("block:chip")[1].split("\n  end")[0]
        self.assertIn("n_spi2[/", inside)
        self.assertIn("n_ui[", inside)
        self.assertNotIn("n_nor", inside)
        self.assertIn("n_nor[", block.split("block:chip")[1].split("\n  end")[1])
        self.assertIn("n_spi2 --- n_nor", block)
        self.assertIn("n_flash --> n_spi2", block)
        self.assertIn("| `ui_task` | ui | 3 | 4096 |", block)

    def test_block_rows_follow_layers_then_buses(self):
        inside = self.text.split("block:chip")[1].split("\n  end")[0]
        self.assertLess(inside.index("n_ui["), inside.index("n_flash["))
        self.assertLess(inside.index("n_flash["), inside.index("n_spi2[/"))

    def test_bus_and_device_sit_under_their_driver(self):
        m = copy.deepcopy(FULL)
        m["components"][1]["hardware"] = []
        m["components"] += [
            {"id": "a", "layer": "drivers", "description": "a"},
            {"id": "b", "layer": "drivers", "description": "b", "hardware": ["spi2"]},
        ]
        block = gd.render(m, "x").split("## Block")[1].split("```")[1]
        cells = [l.strip() for l in block.splitlines()
                 if l.startswith(("    n_", "    space", "  n_", "  space")) and "--" not in l]
        width = 3  # drivers row: flash, a, b
        # row 0: ui + 2 space; row 1: flash a b; bus row: spi2 under b (column 2); device row: nor under spi2
        self.assertEqual(cells[6:9], ["space", "space", cells[8]])
        self.assertTrue(cells[8].startswith("n_spi2[/"))
        self.assertEqual(cells[9:12][:2], ["space", "space"])
        self.assertTrue(cells[11].startswith("n_nor["))
        self.assertEqual(len(cells), 4 * width)

    def test_layers_stacked_in_manifest_order(self):
        layering = self.text.split("## Layering")[1]
        self.assertIn("block-beta", layering)
        self.assertLess(layering.index("block:r_app"), layering.index("block:r_drivers"))
        self.assertIn("columns 2", layering)  # title cell + at most one component per layer

    def test_long_layer_wraps(self):
        m = copy.deepcopy(FULL)
        m["components"] += [{"id": f"svc{i}", "layer": "app", "description": "s"} for i in range(7)]
        row = gd.render(m, "x").split("block:r_app")[1].split("\n  end")[0]
        self.assertIn("columns 7", row)  # title + 6 per line
        cells = [l.strip() for l in row.splitlines()[2:]]
        self.assertEqual(len(cells), 14)  # 2 lines of 7: title + ui + svc0..4, then space + svc5, svc6 + 4 space
        self.assertEqual(cells[7], "space")

    def test_empty_layer_padded(self):
        m = copy.deepcopy(FULL)
        m["layers"].append({"id": "hal", "description": "nothing yet"})
        layering = gd.render(m, "x").split("## Layering")[1]
        self.assertIn("t_hal[", layering.split("block:r_hal")[1].split("end")[0])
        self.assertIn("space", layering.split("block:r_hal")[1].split("end")[0])

    def test_heading_level(self):
        self.assertIn("\n### Context\n", gd.render(copy.deepcopy(FULL), "x", level=3))

    def test_shared_and_upward_marked_red(self):
        m = copy.deepcopy(FULL)
        m["components"].append({"id": "log", "layer": "app", "description": "log", "depends_on": ["flash"]})
        m["components"][1]["depends_on"] = ["ui"]  # upward: drivers -> app
        org = gd.render(m, "x").split("## Organigram")[1]
        self.assertIn("class n_flash shared", org)
        self.assertIn("linkStyle 1 stroke:#d33", org)  # edges: ui->flash (0), flash->ui (1), log->flash (2)
        self.assertIn("1 upward", org)


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "arch").mkdir()
        (self.root / "arch/architecture.yaml").write_text(yaml.safe_dump(FULL), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_then_check_passes(self):
        self.assertEqual(run("--project", str(self.root))[0], 0)
        self.assertEqual(run("--project", str(self.root), "--check")[0], 0)

    def test_check_fails_when_missing(self):
        code, out, _ = run("--project", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("stale or missing", out)

    def test_check_fails_after_manifest_edit(self):
        run("--project", str(self.root))
        m = copy.deepcopy(FULL)
        m["components"][0]["description"] = "changed"
        m["layers"][0]["description"] = "changed"
        (self.root / "arch/architecture.yaml").write_text(yaml.safe_dump(m), encoding="utf-8")
        self.assertEqual(run("--project", str(self.root), "--check")[0], 1)

    def test_keeps_text_outside_the_markers(self):
        page = self.root / "page.md"
        page.write_text("# Page\n\nIntro.\n\n## 9. After\n", encoding="utf-8")
        run("--project", str(self.root), "--out", str(page), "--level", "3")
        run("--project", str(self.root), "--out", str(page), "--level", "3")  # second run replaces, not appends
        text = page.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Page\n\nIntro.\n"))
        self.assertIn("## 9. After", text)
        self.assertEqual(text.count(gd.END), 1)

    def test_schema_error_refused(self):
        (self.root / "arch/architecture.yaml").write_text("version: 1\n", encoding="utf-8")
        code, out, _ = run("--project", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("Fix the manifest first", out)

    def test_rule_error_drawn_with_warning(self):
        m = copy.deepcopy(FULL)
        m["components"][1]["depends_on"] = ["ui"]
        (self.root / "arch/architecture.yaml").write_text(yaml.safe_dump(m), encoding="utf-8")
        code, _, err = run("--project", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("warning:", err)


class AsIs(unittest.TestCase):
    def test_undeclared_include_red(self):
        with Project(files=dict(FILES, **{"components/flash/flash.c": '#include "ui.h"\n', "main/ui.h": ""})) as p:
            code, out, _ = run("--project", str(p.root), "--as-is")
            self.assertEqual(code, 0)
            self.assertIn("2 edges, 1 not in the manifest (red), 1 upward", out)
            self.assertIn("linkStyle 0 stroke:#d33", out)  # sorted: flash->ui first


if __name__ == "__main__":
    unittest.main()
