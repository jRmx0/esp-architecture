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
    "subsystems": [{"id": "core", "description": "everything"}],
    "layers": [{"id": "app", "description": "top"}, {"id": "drivers", "description": "bottom"}],
    "components": [
        {"id": "ui", "subsystem": "core", "layer": "app", "description": "UI", "depends_on": ["flash_drv"]},
        {"id": "flash_drv", "subsystem": "core", "layer": "drivers", "description": "flash driver", "hardware": ["flash"]},
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

    def test_gateway_target_architecture_is_valid(self):
        self.assertEqual(vm.validate(yaml.safe_load(GATEWAY.read_text(encoding="utf-8"))), [])


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
            d["components"].append({"id": "logger", "subsystem": "core", "layer": "app", "description": "log"})
            d["components"][0]["depends_on"].append("logger")
        self.check(m(a=edit), "same layer")

    def test_cycle(self):
        def edit(d):
            d["components"] += [
                {"id": "a", "subsystem": "core", "layer": "app", "description": "a", "depends_on": ["b"]},
                {"id": "b", "subsystem": "core", "layer": "app", "description": "b", "depends_on": ["a"]},
            ]
        self.check(m(a=edit), "dependency cycle: a -> b -> a")

    def test_subsystems_required(self):
        self.check(m(a=lambda d: d.pop("subsystems")), "'subsystems' is a required property")
        self.check(m(a=lambda d: d.update(subsystems=[])), "should be non-empty")
        self.check(m(a=lambda d: d["components"][0].pop("subsystem")), "'subsystem' is a required property")

    def test_undeclared_subsystem(self):
        self.check(m(a=lambda d: d["components"][0].update(subsystem="nope")), "subsystem nope is not declared")

    def test_empty_subsystem(self):
        self.check(m(a=lambda d: d["subsystems"].append({"id": "radio", "description": "r"})),
                   "subsystem radio: no component belongs to it")

    def test_subsystem_id_unique_across_kinds(self):
        self.check(m(a=lambda d: d["subsystems"].append({"id": "ui", "description": "u"})), "component ui: id used twice")

    def test_device_unknown_bus(self):
        self.check(m(a=lambda d: d["hardware"]["devices"][0].update(bus="i2c0")), "bus i2c0 is not declared")

    def test_processor_and_holds_accepted(self):
        def edit(d):
            d["hardware"]["processor"] = "ESP32-S3"
            d["hardware"]["devices"][0]["holds"] = ["version", "image data"]
        self.assertEqual(vm.validate(m(a=edit)), [])

    def test_device_planned_is_refused(self):
        self.check(m(a=lambda d: d["hardware"]["devices"][0].update(planned=True)), "planned")

    def test_device_name_accepted(self):
        self.assertEqual(vm.validate(m(a=lambda d: d["hardware"]["devices"][0].update(name="SIM7600 modem"))), [])

    def test_holds_must_be_a_list(self):
        self.check(m(a=lambda d: d["hardware"]["devices"][0].update(holds="fonts")), "holds")

    def test_device_on_several_buses(self):
        def edit(d):
            d["hardware"]["buses"].append({"id": "pins", "kind": "gpio", "description": "g"})
            d["hardware"]["devices"][0]["bus"] = ["spi2", "pins"]
        self.assertEqual(vm.validate(m(a=edit)), [])
        self.check(m(a=lambda d: d["hardware"]["devices"][0].update(bus=["spi2", "i2c9"])), "bus i2c9 is not declared")
        self.check(m(a=lambda d: d["hardware"]["devices"][0].update(bus=[])), "bus")

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
