"""Check that an ESP-IDF project's architecture decisions are backed by records.

usage: python check_records.py [--project DIR]

Reads <project>/.esp-architecture/architecture.yaml, .esp-architecture/requirements.md and .esp-architecture/decisions/DEC-nnn-*.md.
Exit 0 when every component, layer and subsystem cites a decision, every cited ID exists,
and every decision cites a requirement; 1 with one error per line otherwise; 2 on bad usage.

  requirements.md   tables "| ID | Title | Requirement |", one row per requirement,
                    its first cell the ID: F-REQ-nnn (functional) or NF-REQ-nnn (non-functional)
  DEC-nnn-slug.md   "# DEC-nnn Title", then sections Context, Decision, Alternatives, Requirements,
                    and optionally Rules (RULE-nnn IDs from the plugin's rules/rules.yaml)
"""
import argparse
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validate_manifest import validate  # noqa: E402

REQ_ID = r"(?:NF|F)-REQ-[0-9]{3}"
REQ = re.compile(rf"\b{REQ_ID}\b")
RULE = re.compile(r"\bRULE-[0-9]{3}\b")
SECTIONS = ("Context", "Decision", "Alternatives", "Requirements")
RULES = pathlib.Path(__file__).resolve().parent.parent / "rules" / "rules.yaml"


def rule_ids():
    return {r["id"] for r in yaml.safe_load(RULES.read_text(encoding="utf-8"))["rules"]}


def requirement_ids(path):
    """[REQ ids] of table rows whose first cell is the ID, in order, duplicates kept for the caller."""
    if not path.is_file():
        return []
    return re.findall(rf"^[ \t]*\|[ \t]*({REQ_ID})[ \t]*\|", path.read_text(encoding="utf-8"), re.M)


def decision_records(folder):
    """{DEC id: (file name, text)} plus errors for bad names, headings and duplicates."""
    records, errors = {}, []
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        m = re.match(r"(DEC-[0-9]{3})-[a-z0-9-]+\.md$", f.name)
        if not m:
            errors.append(f"{f.name}: name must be DEC-nnn-slug.md")
            continue
        text = f.read_text(encoding="utf-8")
        head = re.search(r"^#[ \t]+(DEC-[0-9]{3})\b", text, re.M)
        if not head or head.group(1) != m.group(1):
            errors.append(f"{f.name}: first heading must be '# {m.group(1)} <title>'")
        if m.group(1) in records:
            errors.append(f"{f.name}: {m.group(1)} used twice")
        records[m.group(1)] = (f.name, text)
    return records, errors


def section(text, name):
    m = re.search(rf"^##[ \t]+{name}[ \t]*\n(.*?)(?=^##[ \t]|\Z)", text, re.M | re.S)
    return m.group(1) if m else None


def check(root, manifest):
    """Return a list of error strings; empty means every decision is backed."""
    arch = root / ".esp-architecture"
    req_list = requirement_ids(arch / "requirements.md")
    reqs = set(req_list)
    errors = [f"requirements.md: {r} used twice" for r in sorted(reqs) if req_list.count(r) > 1]
    records, rec_errors = decision_records(arch / "decisions")
    errors += rec_errors

    served, rules = set(), rule_ids()
    for dec, (name, text) in sorted(records.items()):
        errors += [f"{name}: {r} is not in the rule catalog"
                   for r in dict.fromkeys(RULE.findall(section(text, "Rules") or "")) if r not in rules]
        missing = [s for s in SECTIONS if section(text, s) is None]
        if missing:
            errors.append(f"{name}: missing sections {', '.join(missing)}")
        cited = REQ.findall(section(text, "Requirements") or "")
        served.update(cited)
        if not cited:
            errors.append(f"{name}: cites no requirement")
        errors += [f"{name}: {r} is not in requirements.md" for r in dict.fromkeys(cited) if r not in reqs]
    errors += [f"requirements.md: {r} is served by no decision" for r in sorted(reqs - served)]

    for kind in ("subsystems", "layers", "components"):
        for item in manifest.get(kind, []):
            where = f"{kind[:-1]} {item['id']}"
            if not item.get("decisions"):
                errors.append(f"{where}: cites no decision")
            errors += [f"{where}: {d} has no record in .esp-architecture/decisions" for d in item.get("decisions", [])
                       if d not in records]
            errors += [f"{where}: {r} is not in requirements.md" for r in item.get("requirements", [])
                       if r not in reqs]
    return errors


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=".")
    root = pathlib.Path(ap.parse_args(argv[1:]).project).resolve()
    path = root / ".esp-architecture" / "architecture.yaml"
    try:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        print(f"{path}: {e}")
        return 1
    errors = validate(manifest)
    if errors:
        for e in errors:
            print(f"{path}: {e}")
        print("Fix the manifest first.")
        return 1
    errors = check(root, manifest)
    for e in errors:
        print(e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
