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
import check_records as cr  # noqa: E402

MANIFEST = {
    "version": 1,
    "system": {"name": "demo", "description": "demo"},
    "subsystems": [{"id": "core", "description": "all of it", "decisions": ["DEC-001"]}],
    "layers": [{"id": "app", "description": "top", "decisions": ["DEC-001"]}],
    "components": [{"id": "ui", "subsystem": "core", "layer": "app", "description": "UI",
                    "decisions": ["DEC-002"], "requirements": ["F-REQ-001"]}],
}

REQS = ("# Requirements\n\n## Display\n\n| ID | Title | Requirement | Source |\n|---|---|---|---|\n"
        "| F-REQ-001 | Show the state | The device shows its state. | owner |\n"
        "| NF-REQ-002 | Boot fast | Under 2 s; not F-REQ-009. | owner |\n")


def req_row(req, title="Extra"):
    return f"| {req} | {title} | Text. | owner |\n"


def record(dec, reqs="F-REQ-001"):
    return (f"# {dec} Something\n\n## Context\nWhy.\n\n## Decision\nWhat.\n\n"
            f"## Alternatives\nOthers.\n\n## Requirements\n- {reqs}\n")


FILES = {
    "arch/requirements.md": REQS,
    "arch/decisions/DEC-001-one-layer.md": record("DEC-001", "F-REQ-001, NF-REQ-002"),
    "arch/decisions/DEC-002-ui-component.md": record("DEC-002", "F-REQ-001, NF-REQ-002"),
}


class Project:
    def __init__(self, manifest=MANIFEST, files=FILES):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.write("arch/architecture.yaml", yaml.safe_dump(manifest))
        for path, text in files.items():
            self.write(path, text)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def errors(self):
        return cr.check(self.root, yaml.safe_load((self.root / "arch/architecture.yaml").read_text()))

    def run(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cr.main(["check_records.py", "--project", str(self.root)])
        return code, out.getvalue()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.tmp.cleanup()


def edit(**changes):
    m = yaml.safe_load(yaml.safe_dump(MANIFEST))
    for kind, fields in changes.items():
        m[kind][0].update(fields)
    return m


class Records(unittest.TestCase):
    def test_backed_project_passes(self):
        with Project() as p:
            self.assertEqual(p.errors(), [])
            self.assertEqual(p.run()[0], 0)

    def test_unbacked_component_layer_and_subsystem(self):
        m = edit(components={"decisions": []}, layers={"decisions": []})
        del m["subsystems"][0]["decisions"]
        with Project(manifest=m) as p:
            self.assertEqual(p.errors(), ["subsystem core: cites no decision", "layer app: cites no decision",
                                          "component ui: cites no decision"])

    def test_dangling_ids_in_manifest(self):
        with Project(manifest=edit(components={"decisions": ["DEC-009"], "requirements": ["F-REQ-009"]})) as p:
            self.assertEqual(p.errors(), ["component ui: DEC-009 has no record in arch/decisions",
                                          "component ui: F-REQ-009 is not in requirements.md"])

    def test_decision_must_cite_existing_requirement(self):
        with Project() as p:
            p.write("arch/decisions/DEC-002-ui-component.md", record("DEC-002", "F-REQ-007"))
            self.assertEqual(p.errors(), ["DEC-002-ui-component.md: F-REQ-007 is not in requirements.md"])
            p.write("arch/decisions/DEC-002-ui-component.md", record("DEC-002", "none yet"))
            self.assertEqual(p.errors(), ["DEC-002-ui-component.md: cites no requirement"])

    def test_requirement_outside_requirements_section_does_not_count(self):
        with Project() as p:
            p.write("arch/decisions/DEC-002-ui-component.md",
                    record("DEC-002", "none").replace("Why.", "Why: F-REQ-001."))
            self.assertEqual(p.errors(), ["DEC-002-ui-component.md: cites no requirement"])

    def test_only_table_rows_define_requirements(self):
        with Project() as p:
            p.write("arch/requirements.md", REQS + "\n## F-REQ-003 Old heading form\nSee F-REQ-004.\n")
            self.assertEqual(cr.requirement_ids(p.root / "arch/requirements.md"), ["F-REQ-001", "NF-REQ-002"])
            p.write("arch/requirements.md", REQS + req_row("REQ-003", "No kind prefix"))
            self.assertEqual(cr.requirement_ids(p.root / "arch/requirements.md"), ["F-REQ-001", "NF-REQ-002"])

    def test_requirement_served_by_no_decision(self):
        with Project() as p:
            p.write("arch/requirements.md", REQS + req_row("F-REQ-003", "Log faults"))
            self.assertEqual(p.errors(), ["requirements.md: F-REQ-003 is served by no decision"])

    def test_rules_section_cites_catalog_rules(self):
        with Project() as p:
            p.write("arch/decisions/DEC-002-ui-component.md",
                    record("DEC-002", "F-REQ-001") + "\n## Rules\n- RULE-001\n- RULE-999\n")
            self.assertEqual(p.errors(), ["DEC-002-ui-component.md: RULE-999 is not in the rule catalog"])

    def test_missing_sections(self):
        with Project() as p:
            p.write("arch/decisions/DEC-002-ui-component.md", "# DEC-002 X\n\n## Requirements\nF-REQ-001\n")
            self.assertEqual(p.errors(), ["DEC-002-ui-component.md: missing sections Context, Decision, Alternatives"])

    def test_record_name_and_heading(self):
        with Project() as p:
            p.write("arch/decisions/notes.md", "")
            p.write("arch/decisions/DEC-002-ui-component.md", record("DEC-003"))
            self.assertEqual(p.errors(), ["DEC-002-ui-component.md: first heading must be '# DEC-002 <title>'",
                                          "notes.md: name must be DEC-nnn-slug.md"])

    def test_duplicate_ids(self):
        with Project() as p:
            p.write("arch/requirements.md", REQS + req_row("F-REQ-001", "Again"))
            p.write("arch/decisions/DEC-001-again.md", record("DEC-001"))
            self.assertEqual(p.errors(), ["requirements.md: F-REQ-001 used twice", "DEC-001-one-layer.md: DEC-001 used twice"])

    def test_no_records_at_all(self):
        with Project(files={}) as p:
            self.assertEqual(p.errors(), ["subsystem core: DEC-001 has no record in arch/decisions",
                                          "layer app: DEC-001 has no record in arch/decisions",
                                          "component ui: DEC-002 has no record in arch/decisions",
                                          "component ui: F-REQ-001 is not in requirements.md"])

    def test_invalid_manifest_stops_the_check(self):
        with Project() as p:
            p.write("arch/architecture.yaml", "version: 1\n")
            code, out = p.run()
            self.assertEqual(code, 1)
            self.assertIn("Fix the manifest first", out)


if __name__ == "__main__":
    unittest.main()
