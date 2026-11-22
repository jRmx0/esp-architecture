"""Run: python -m unittest discover -s tests"""
import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "tools"))
import check_architecture as ca  # noqa: E402

MANIFEST = {
    "version": 1,
    "system": {"name": "demo", "description": "demo"},
    "subsystems": [{"id": "core", "description": "everything"}],
    "layers": [{"id": "app", "description": "top"}, {"id": "drivers", "description": "bottom"}],
    "components": [
        {"id": "ui", "subsystem": "core", "layer": "app", "path": "main", "description": "UI",
         "depends_on": ["flash"], "idf_requires": ["esp_timer"]},
        {"id": "flash", "subsystem": "core", "layer": "drivers", "path": "components/flash", "description": "flash",
         "idf_requires": ["esp_driver_spi"]},
    ],
}

FILES = {
    "main/CMakeLists.txt": 'idf_component_register(SRCS "ui.c" INCLUDE_DIRS "." PRIV_REQUIRES flash esp_timer)\n',
    "main/ui.c": '#include "flash.h"\n#include "esp_timer.h"\n',
    "components/flash/CMakeLists.txt": 'idf_component_register(SRCS "flash.c" INCLUDE_DIRS "include"\n  REQUIRES esp_driver_spi)\n',
    "components/flash/include/flash.h": "void flash_read(void);\n",
    "components/flash/flash.c": '#include "flash.h"\n',
}


class Project:
    """A throwaway ESP-IDF project on disk."""

    def __init__(self, manifest=MANIFEST, files=FILES):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.write(".esp-architecture/architecture.yaml", yaml.safe_dump(manifest))
        for path, text in files.items():
            self.write(path, text)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def violations(self):
        return ca.find_violations(self.root, yaml.safe_load((self.root / ".esp-architecture/architecture.yaml").read_text()))

    def run(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ca.main(["check_architecture.py", "--project", str(self.root), *args])
        return code, out.getvalue()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.tmp.cleanup()


def with_components(*comps):
    return dict(MANIFEST, components=list(comps))


class Violations(unittest.TestCase):
    def test_clean_project(self):
        with Project() as p:
            self.assertEqual(p.violations(), {})
            self.assertEqual(p.run()[0], 0)

    def test_undeclared_include_is_upward(self):
        with Project() as p:
            p.write("components/flash/flash.c", '#include "flash.h"\n\n#include "ui.h"\n')
            p.write("main/ui.h", "")
            v = p.violations()
            self.assertEqual(v["include flash -> ui"], "components/flash/flash.c:3 (upward)")

    def test_requires_not_allowed(self):
        with Project() as p:
            p.write("components/flash/CMakeLists.txt", 'idf_component_register(SRCS "flash.c" REQUIRES esp_driver_spi esp_wifi)\n')
            self.assertIn("requires flash -> esp_wifi", p.violations())

    def test_managed_dependency_counts_as_requirement(self):
        with Project() as p:
            p.write("main/idf_component.yml", "dependencies:\n  idf: '>=6.0'\n  espressif/mqtt: '^1.1.0'\n")
            self.assertEqual(list(p.violations()), ["requires main -> espressif/mqtt"])

    def test_managed_dependency_allowed_in_either_spelling(self):
        m = with_components(dict(MANIFEST["components"][0], idf_requires=["esp_timer", "espressif__mqtt"]),
                            MANIFEST["components"][1])
        with Project(manifest=m) as p:
            p.write("main/idf_component.yml", "dependencies:\n  espressif/mqtt: '*'\n")
            self.assertEqual(p.violations(), {})

    def test_shared_component_directory(self):
        m = with_components(
            dict(MANIFEST["components"][0], sources=["main/ui.c"]),
            {"id": "log", "subsystem": "core", "layer": "app", "path": "main", "sources": ["main/log.c"], "description": "log"},
            MANIFEST["components"][1])
        with Project(manifest=m) as p:
            p.write("main/log.c", "")
            v = p.violations()
            self.assertIn("shared ui", v)
            self.assertIn("shared log", v)

    def test_unowned_file(self):
        m = with_components(dict(MANIFEST["components"][0], sources=["main/ui.c"]), MANIFEST["components"][1])
        with Project(manifest=m) as p:
            p.write("main/extra.c", "")
            self.assertIn("unowned main/extra.c", p.violations())

    def test_ambiguous_file(self):
        m = with_components(MANIFEST["components"][0],
                            dict(MANIFEST["components"][1], sources=["components/flash/*.c", "main/ui.c"]))
        with Project(manifest=m) as p:
            self.assertIn("ambiguous main/ui.c", p.violations())

    def test_missing_component(self):
        m = with_components(MANIFEST["components"][0], dict(MANIFEST["components"][1], path="components/gone"))
        with Project(manifest=m) as p:
            self.assertIn("missing flash", p.violations())

    def test_planned_component_without_path_is_skipped(self):
        m = with_components(*MANIFEST["components"], {"id": "radio", "subsystem": "core", "layer": "drivers", "description": "planned"})
        with Project(manifest=m) as p:
            self.assertEqual(p.violations(), {})

    def test_cmake_comments_and_variables_ignored(self):
        with Project() as p:
            p.write("components/flash/CMakeLists.txt",
                    '# REQUIRES esp_wifi\nidf_component_register(SRCS "flash.c" REQUIRES esp_driver_spi) # esp_wifi\n')
            self.assertEqual(p.violations(), {})


class Baseline(unittest.TestCase):
    def dirty(self, p):
        p.write("components/orphan/CMakeLists.txt", 'idf_component_register(SRCS "orphan.c")\n')
        p.write("components/orphan/orphan.c", "")
        p.write("components/flash/CMakeLists.txt", 'idf_component_register(SRCS "flash.c" REQUIRES esp_driver_spi esp_wifi)\n')

    def test_violation_fails_without_baseline(self):
        with Project() as p:
            self.dirty(p)
            code, out = p.run()
            self.assertEqual(code, 1)
            self.assertIn("violation: requires flash -> esp_wifi", out)

    def test_baseline_accepts_known_violations(self):
        with Project() as p:
            self.dirty(p)
            self.assertEqual(p.run("--write-baseline")[0], 0)
            self.assertEqual(p.run()[0], 0)

    def test_new_violation_fails_with_baseline(self):
        with Project() as p:
            self.dirty(p)
            p.run("--write-baseline")
            p.write("components/flash/flash.c", '#include "ui.h"\n')
            p.write("main/ui.h", "")
            code, out = p.run()
            self.assertEqual(code, 1)
            self.assertIn("violation: include flash -> ui", out)

    def test_fixed_violation_must_leave_baseline(self):
        with Project() as p:
            self.dirty(p)
            p.run("--write-baseline")
            (p.root / "components/orphan/orphan.c").unlink()
            code, out = p.run()
            self.assertEqual(code, 1)
            self.assertIn("fixed, remove from baseline: unowned components/orphan/orphan.c", out)
            self.assertEqual(p.run("--write-baseline")[0], 0)  # shrinking is allowed
            self.assertEqual(p.run()[0], 0)

    def test_baseline_cannot_grow(self):
        with Project() as p:
            self.dirty(p)
            p.run("--write-baseline")
            p.write("components/orphan/more.c", "")
            code, out = p.run("--write-baseline")
            self.assertEqual(code, 1)
            self.assertIn("may only shrink", out)

    def test_invalid_manifest_stops_the_check(self):
        with Project() as p:
            p.write(".esp-architecture/architecture.yaml", "version: 1\n")
            code, out = p.run()
            self.assertEqual(code, 1)
            self.assertIn("Fix the manifest first", out)


if __name__ == "__main__":
    unittest.main()
