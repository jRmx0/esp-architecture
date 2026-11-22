"""Run: python -m unittest discover -s tests"""
import copy
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "tools"))
import validate_manifest as vm  # noqa: E402

GATEWAY = ROOT / "examples" / "gateway" / "architecture.yaml"

MINIMAL = {
    "version": 1,
    "system": {"name": "demo", "description": "demo device"},
    "context": {
        "actors": [{"id": "user", "kind": "person", "description": "presses the button"}],
        "flows": [{"from": "user", "to": "system", "data": "button press"}],
    },
    "hardware": {
        "buses": [{"id": "spi2", "kind": "spi", "description": "SPI bus"}],
        "devices": [{"id": "flash", "bus": "spi2", "description": "external flash"}],
    },
    "layers": [{"id": "app", "description": "top"}, {"id": "drivers", "description": "bottom"}],
    "components": [
        {"id": "ui", "layer": "app", "description": "UI", "depends_on": ["flash_drv"]},
        {"id": "flash_drv", "layer": "drivers", "description": "flash driver", "hardware": ["flash"]},
    ],
    "tasks": [{"id": "ui", "component": "ui", "priority": 3, "stack": 4096}],
}


def m(**edits):
    """MINIMAL with edits applied by callables: m(x=lambda d: ...)."""
    d = copy.deepcopy(MINIMAL)
    for f in edits.values():
        f(d)
    return d


class Valid(unittest.TestCase):
    def test_minimal_is_valid(self):
        self.assertEqual(vm.validate(copy.deepcopy(MINIMAL)), [])

    def test_gateway_reports_only_its_upward_dependency(self):
        errors = vm.validate(yaml.safe_load(GATEWAY.read_text(encoding="utf-8")))
        self.assertEqual(errors, ["component cell (l1_links) depends on usage (l3_services): upward"])


class Rejects(unittest.TestCase):
    def check(self, manifest, fragment):
        errors = vm.validate(manifest)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_schema_unknown_key(self):
        self.check(m(a=lambda d: d.update(extra=1)), "Additional properties")

    def test_schema_bad_id(self):
        self.check(m(a=lambda d: d["components"][0].update(id="Bad-Id")), "does not match")

    def test_duplicate_id_across_kinds(self):
        self.check(m(a=lambda d: d["components"][1].update(id="flash")), "id used twice")

    def test_reserved_system_id(self):
        self.check(m(a=lambda d: d["context"]["actors"][0].update(id="system")), "id used twice")

    def test_duplicate_task(self):
        self.check(m(a=lambda d: d["tasks"].append(dict(d["tasks"][0]))), "task ui: id used twice")

    def test_undeclared_layer(self):
        self.check(m(a=lambda d: d["components"][0].update(layer="nope")), "layer nope is not declared")

    def test_undeclared_dependency(self):
        self.check(m(a=lambda d: d["components"][0].update(depends_on=["ghost"])), "undeclared component ghost")

    def test_self_dependency(self):
        self.check(m(a=lambda d: d["components"][0].update(depends_on=["ui"])), "depends on itself")

    def test_upward(self):
        self.check(m(a=lambda d: d["components"][1].update(depends_on=["ui"])), "upward")

    def test_sideways_forbidden(self):
        def edit(d):
            d["allow_sideways"] = False
            d["components"].append({"id": "logger", "layer": "app", "description": "log"})
            d["components"][0]["depends_on"].append("logger")
        self.check(m(a=edit), "same layer")

    def test_cycle(self):
        def edit(d):
            d["components"] += [
                {"id": "a", "layer": "app", "description": "a", "depends_on": ["b"]},
                {"id": "b", "layer": "app", "description": "b", "depends_on": ["a"]},
            ]
        self.check(m(a=edit), "dependency cycle: a -> b -> a")

    def test_device_unknown_bus(self):
        self.check(m(a=lambda d: d["hardware"]["devices"][0].update(bus="i2c0")), "bus i2c0 is not declared")

    def test_component_unknown_hardware(self):
        self.check(m(a=lambda d: d["components"][1].update(hardware=["lcd"])), "hardware lcd")

    def test_flow_between_actors_without_data(self):
        def edit(d):
            d["context"]["actors"].append({"id": "cloud", "kind": "system", "description": "c"})
            d["context"]["flows"].append({"from": "user", "to": "cloud"})
        self.assertEqual(vm.validate(m(a=edit)), [])

    def test_flow_unknown_actor(self):
        self.check(m(a=lambda d: d["context"]["flows"][0].update({"from": "ghost"})), "ghost is not an actor")

    def test_task_unknown_component(self):
        self.check(m(a=lambda d: d["tasks"][0].update(component="ghost")), "component ghost is not declared")


class Cli(unittest.TestCase):
    def run_on(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "architecture.yaml"
            p.write_text(text, encoding="utf-8")
            return vm.main(["validate_manifest.py", str(p)])

    def test_valid_exits_0(self):
        self.assertEqual(self.run_on(yaml.safe_dump(MINIMAL)), 0)

    def test_invalid_exits_1(self):
        self.assertEqual(self.run_on("version: 2\n"), 1)

    def test_broken_yaml_exits_1(self):
        self.assertEqual(self.run_on("layers: [\n"), 1)

    def test_empty_file_exits_1(self):
        self.assertEqual(self.run_on(""), 1)


if __name__ == "__main__":
    unittest.main()
