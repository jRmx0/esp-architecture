"""Maintainer check: every rule in plugin/rules/rules.yaml has a source in sources.local.yaml.

usage: python tools/check_sources.py
Exit 0 when every rule has an entry with source, location and context and no entry names an
unknown rule; 1 otherwise. Skipped (exit 0) when sources.local.yaml is absent, e.g. in CI,
because the file is private and never committed.
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / "plugin" / "rules" / "rules.yaml"
SOURCES = ROOT / "sources.local.yaml"
FIELDS = ("source", "location", "context")


def check(rules, sources):
    ids = [r["id"] for r in rules["rules"]]
    errors = [f"{i}: no entry in sources.local.yaml" for i in ids if i not in sources]
    errors += [f"{i}: entry for a rule that does not exist" for i in sources if i not in ids]
    errors += [f"{i}: missing {f}" for i in ids if i in sources for f in FIELDS
               if not (sources[i] or {}).get(f)]
    return errors


def main():
    if not SOURCES.is_file():
        print("sources.local.yaml not found: skipped")
        return 0
    errors = check(yaml.safe_load(RULES.read_text(encoding="utf-8")),
                   yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {})
    for e in errors:
        print(e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
