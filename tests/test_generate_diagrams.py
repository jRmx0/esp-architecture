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
    "context": {"actors": [{"id": "user", "kind": "person", "description": "presses buttons"},
                           {"id": "cloud", "kind": "system", "description": "backend"}],
                "flows": [{"from": "user", "to": "system", "data": 'says "hi"'},
                          {"from": "user", "to": "cloud"}]},
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
        self.assertEqual(self.text.count("```mermaid"), 6)  # block: levels 1a, 1b and 2

    def test_quotes_escaped_and_ids_prefixed(self):
        self.assertIn("says #quot;hi#quot;", self.text)
        self.assertIn("n_user -->|", self.text)

    def test_context_names_only_and_optional_label(self):
        ctx = self.text.split("## Context")[1].split("## Block")[0]
        self.assertIn('n_user(["user"])', ctx)
        self.assertNotIn("presses buttons", ctx)
        self.assertIn('n_system[["<b>demo</b>"]]', ctx)
        self.assertIn("n_user --> n_cloud", ctx)

    def test_block_level1_is_hardware_only(self):
        block = self.text.split("## Block")[1].split("## Organigram")[0]
        self.assertIn("flowchart LR", block)
        self.assertIn('cpu_box["<b>demo</b>"]', block)  # no processor: the system name
        self.assertIn('n_nor["nor"]', block)
        self.assertIn('cpu_box ---|"SPI"| n_nor', block)  # no peripheral: the kind in capitals
        self.assertNotIn("n_spi2", block.split("### Level 1b")[0])  # hardware: buses are lines, not boxes
        self.assertNotIn("n_ui", block)
        self.assertNotIn("n_flash", block)
        self.assertNotIn("Amber:", self.text)
        org = self.text.split("## Organigram")[1].split("## Layering")[0]
        self.assertIn("| `ui_task` | ui | 3 | 4096 |", org)

    def test_block_sides_holds_and_shared_bus(self):
        m = copy.deepcopy(FULL)
        m["hardware"] = {
            "processor": "ESP32-S3",
            "buses": [{"id": "spi2", "kind": "spi", "description": "s"},
                      {"id": "i2c0", "kind": "i2c", "description": "i"}],
            "devices": [{"id": "nor", "bus": "spi2", "description": "n", "holds": ["fonts", "images"]},
                        {"id": "lcd", "bus": "spi2", "description": "l"},
                        {"id": "imu", "bus": "i2c0", "description": "i"}]}
        text = gd.render(m, "x")
        block = text.split("## Block")[1].split("```")[1]
        self.assertIn('cpu_box["<b>ESP32-S3</b>"]', block)
        self.assertIn('n_nor["nor"]', block)  # holds are not shown at the hardware level
        # 1a has no layout hint: every line runs from the processor out
        edges = [l.strip() for l in block.splitlines() if "---|" in l]
        self.assertEqual(edges, ['cpu_box ---|"SPI"| n_nor', 'cpu_box ---|"SPI"| n_lcd', 'cpu_box ---|"I2C"| n_imu'])
        self.assertNotIn("~~~", block)
        self.assertIn("linkStyle 0,1 stroke:#d98e04", block)
        self.assertIn("Amber: a bus shared by several devices (spi2); check contention", text)

    def test_block_hardware_description_in_text_not_in_diagram(self):
        m = copy.deepcopy(FULL)
        m["hardware"]["processor"] = "ESP32-WROVER-E"
        m["hardware"]["description"] = "Integrated flash and PSRAM."
        block = gd.render(m, "x").split("## Block")[1].split("## Organigram")[0]
        note, diagram = block.split("```mermaid")[:2]
        self.assertIn("one line per bus. Integrated flash and PSRAM.", note)
        self.assertNotIn("Integrated", diagram)
        self.assertIn('cpu_box["<b>ESP32-WROVER-E</b>"]', diagram)

    def test_block_multi_bus_device_and_peripheral(self):
        m = copy.deepcopy(FULL)
        m["hardware"] = {
            "buses": [{"id": "u1", "kind": "uart", "peripheral": "UART1", "description": "u"},
                      {"id": "u2", "kind": "uart", "description": "u"},
                      {"id": "pins", "kind": "gpio", "description": "g"}],
            "devices": [{"id": "modem", "bus": ["u1", "pins"], "description": "m"},
                        {"id": "led", "bus": "pins", "description": "l"},
                        {"id": "mcu", "bus": "u2", "description": "p"}]}
        block = gd.render(m, "x").split("## Block")[1].split("```")[1]
        self.assertIn('cpu_box ---|"UART1"| n_modem', block)
        self.assertIn('cpu_box ---|"GPIO"| n_modem', block)
        self.assertIn('cpu_box ---|"GPIO"| n_led', block)
        self.assertIn('cpu_box ---|"UART"| n_mcu', block)
        self.assertIn("class n_modem,n_led,n_mcu device", block)
        self.assertNotIn("linkStyle", block)  # two devices on GPIO pins do not contend

    def test_block_software_buses_inside_the_processor(self):
        m = copy.deepcopy(FULL)
        m["hardware"] = {
            "processor": "ESP32-S3",
            "buses": [{"id": "spi2", "kind": "spi", "peripheral": "SPI2", "description": "s"},
                      {"id": "pins", "kind": "gpio", "description": "g"}],
            "devices": [{"id": "nor", "bus": "spi2", "description": "n"},
                        {"id": "lcd", "bus": ["spi2", "pins"], "description": "l"},
                        {"id": "btn", "bus": "pins", "description": "b"}]}
        text = gd.render(m, "x")
        self.assertLess(text.index("### Level 1a: hardware"), text.index("### Level 1b: software"))
        soft = text.split("### Level 1b: software")[1].split("```")[1]
        chip = soft.split('subgraph cpu_box["<b>ESP32-S3</b>"]')[1].split("\n  end")[0]
        self.assertIn('n_spi2["SPI2"]', chip)
        self.assertIn('n_pins["GPIO"]', chip)  # no peripheral: the kind in capitals
        self.assertNotIn("n_nor", chip)  # devices sit outside the processor
        edges = [l.strip() for l in soft.splitlines() if " --- " in l]
        self.assertEqual(edges, ["n_nor --- n_spi2", "n_lcd --- n_spi2", "n_lcd --- n_pins", "n_pins --- n_btn"])
        self.assertIn("class n_spi2 shared", soft)
        self.assertIn("linkStyle 0,1 stroke:#d98e04", soft)
        self.assertIn("classDef shared stroke:#d98e04", soft)

    def test_block_shared_only_where_devices_share_lines(self):
        m = copy.deepcopy(FULL)
        kinds = ["uart", "i2c", "gpio", "adc", "pwm"]
        m["hardware"] = {
            "buses": [{"id": k, "kind": k, "description": k} for k in kinds],
            "devices": [{"id": f"{k}{i}", "bus": k, "description": k} for k in kinds for i in (1, 2)]}
        _, soft, shared = gd.block(m)
        self.assertEqual(shared, ["uart", "i2c"])  # GPIO, ADC and PWM devices use their own pins
        self.assertIn("class n_uart,n_i2c shared", soft)

    def test_block_device_name_falls_back_to_id(self):
        m = copy.deepcopy(FULL)
        m["hardware"]["devices"][0]["name"] = "NOR flash"
        block = gd.render(m, "x").split("## Block")[1].split("```")[1]
        self.assertIn('n_nor["NOR flash"]', block)

    def test_block_without_hardware_still_names_the_processor(self):
        m = copy.deepcopy(FULL)
        del m["hardware"]
        block = gd.render(m, "x").split("## Block")[1].split("```")[1]
        self.assertIn('cpu_box["<b>demo</b>"]', block)
        self.assertNotIn("classDef", block)

    def test_block_level2_subsystems(self):
        self.assertNotIn("~~~", self.text)  # FULL's only subsystem drives a bus: no invisible links
        m = copy.deepcopy(FULL)
        m["subsystems"].append({"id": "storage", "description": "keeps data"})
        m["components"][1].update(subsystem="storage", hardware=["nor"])  # a device stands for its bus
        m["components"].append({"id": "log", "subsystem": "core", "layer": "app", "description": "l",
                                "depends_on": ["flash"]})
        l2 = gd.render(m, "x").split("### Level 2: subsystems")[1].split("## Organigram")[0]
        self.assertIn('n_core["<b>core</b>"]', l2)
        self.assertNotIn("-->", l2)  # no arrows between subsystems: the organigram shows calls
        self.assertIn("n_storage --- n_spi2", l2)
        self.assertIn("n_spi2 --- n_nor", l2)
        self.assertNotIn("n_ui", l2)  # components come in level 3
        self.assertIn("| `core` | ui, log | everything |", l2)
        self.assertNotIn("classDef shared", l2)
        m["hardware"]["devices"].append({"id": "lcd", "bus": "spi2", "description": "display"})
        l2 = gd.render(m, "x").split("### Level 2: subsystems")[1].split("## Organigram")[0]
        self.assertIn("class n_spi2 shared", l2)  # amber, as in 1b

    def test_block_level2_lines_join_connected_subsystems(self):
        m = copy.deepcopy(FULL)
        m["subsystems"] += [{"id": "storage", "description": "s"}, {"id": "logic", "description": "l"}]
        m["components"][1]["subsystem"] = "storage"
        m["components"] += [{"id": "rules", "subsystem": "logic", "layer": "app", "description": "r",
                             "depends_on": [m["components"][1]["id"]]},
                            {"id": "back", "subsystem": "storage", "layer": "app", "description": "b",
                             "depends_on": ["rules"]}]  # both ways: still one line
        l2 = gd.render(m, "x").split("### Level 2: subsystems")[1].split("## Organigram")[0]
        lines = [l.strip() for l in l2.split("```")[1].splitlines()]
        self.assertEqual([l for l in lines if " --- n_" in l and "n_logic" in l], ["n_logic --- n_storage"])
        self.assertNotIn("n_core --- n_core", lines)

    def test_block_level2_busless_subsystems_sit_inside(self):
        m = copy.deepcopy(FULL)
        m["subsystems"] += [{"id": "storage", "description": "keeps data"}, {"id": "logic", "description": "l"}]
        m["components"][1]["subsystem"] = "storage"
        m["components"].append({"id": "rules", "subsystem": "logic", "layer": "app", "description": "r"})
        l2 = gd.render(m, "x").split("### Level 2: subsystems")[1].split("## Organigram")[0]
        lines = [l.strip() for l in l2.split("```")[1].splitlines()]
        self.assertIn("n_core --- n_storage", lines)  # a real line places core, so only logic needs one
        self.assertEqual([l for l in lines if "~~~" in l], ["n_logic ~~~ n_storage"])
        self.assertTrue(all("~~~" in l for l in lines[lines.index("n_logic ~~~ n_storage"):]
                            if "---" in l or "-->" in l))  # declared after every visible line
        m["components"][1]["subsystem"] = "core"  # two edge subsystems, one inner: each edge one gets a link
        m["subsystems"].append({"id": "radio", "description": "r"})
        m["hardware"]["buses"].append({"id": "uart1", "kind": "uart", "description": "u"})
        m["components"].append({"id": "lte", "subsystem": "radio", "layer": "drivers", "description": "l",
                                "hardware": ["uart1"]})
        m["subsystems"] = [x for x in m["subsystems"] if x["id"] != "storage"]
        l2 = gd.render(m, "x").split("### Level 2: subsystems")[1].split("## Organigram")[0]
        self.assertEqual([l.strip() for l in l2.splitlines() if "~~~" in l], ["n_logic ~~~ n_core", "n_logic ~~~ n_radio"])
        for c in m["components"]:
            c.pop("hardware", None)  # no subsystem drives a bus: no invisible links
        self.assertNotIn("~~~", gd.render(m, "x"))

    def test_layers_stacked_in_manifest_order(self):
        layering = self.text.split("## Layering")[1]
        self.assertIn("block-beta", layering)
        self.assertLess(layering.index("block:r_app"), layering.index("block:r_drivers"))
        self.assertIn("columns 2", layering)  # title cell + at most one component per layer

    def test_long_layer_wraps(self):
        m = copy.deepcopy(FULL)
        m["components"] += [{"id": f"svc{i}", "subsystem": "core", "layer": "app", "description": "s"} for i in range(7)]
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

    def test_shared_amber_and_upward_red(self):
        m = copy.deepcopy(FULL)
        m["components"].append({"id": "log", "subsystem": "core", "layer": "app", "description": "log", "depends_on": ["flash"]})
        m["components"][1]["depends_on"] = ["ui"]  # upward: drivers -> app
        org = gd.render(m, "x").split("## Organigram")[1]
        self.assertIn("class n_flash shared", org)
        self.assertIn("classDef shared stroke:#d98e04", org)  # shared: check contention
        self.assertIn("Amber boxes: used by more than one component (flash); check contention", org)
        self.assertIn("linkStyle 1 stroke:#d33", org)  # breaks a rule  # edges: ui->flash (0), flash->ui (1), log->flash (2)
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
