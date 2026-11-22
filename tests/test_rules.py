"""Run: python -m unittest discover -s tests"""
import pathlib
import re
import sys
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_sources as cs  # noqa: E402

CATALOG = yaml.safe_load((ROOT / "plugin" / "rules" / "rules.yaml").read_text(encoding="utf-8"))
CHECKERS = {"validate_manifest", "check_architecture", "check_records", "generate_diagrams", "review"}


class Catalog(unittest.TestCase):
    def test_rules_are_well_formed(self):
        ids = [r["id"] for r in CATALOG["rules"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate rule ID")
        for r in CATALOG["rules"]:
            with self.subTest(r["id"]):
                self.assertRegex(r["id"], r"^RULE-[0-9]{3}$")
                self.assertEqual(set(r) - {"see"}, {"id", "area", "rule", "rationale", "checked_by"})
                self.assertTrue(r["rule"].strip() and r["rationale"].strip())
                self.assertTrue(r["checked_by"] and set(r["checked_by"]) <= CHECKERS, r["checked_by"])
                for url in r.get("see", []):
                    self.assertTrue(url.startswith("https://docs.espressif.com/"), url)

    def test_no_book_citation(self):
        text = (ROOT / "plugin" / "rules" / "rules.yaml").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"(?i)\b(chapter|ch\.|page|pp?\.|figure)\b", text))


class Sources(unittest.TestCase):
    RULES = {"rules": [{"id": "RULE-001"}, {"id": "RULE-002"}]}
    ENTRY = {"source": "s", "location": "l", "context": "c"}

    def test_complete_map_passes(self):
        self.assertEqual(cs.check(self.RULES, {"RULE-001": self.ENTRY, "RULE-002": self.ENTRY}), [])

    def test_missing_orphan_and_incomplete(self):
        errors = cs.check(self.RULES, {"RULE-001": {"source": "s"}, "RULE-009": self.ENTRY})
        self.assertEqual(errors, ["RULE-002: no entry in sources.local.yaml",
                                  "RULE-009: entry for a rule that does not exist",
                                  "RULE-001: missing location", "RULE-001: missing context"])


if __name__ == "__main__":
    unittest.main()
