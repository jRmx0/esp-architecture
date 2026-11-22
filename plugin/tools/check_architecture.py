"""Check an ESP-IDF project's code against its arch/architecture.yaml.

usage: python check_architecture.py [--project DIR] [--manifest FILE] [--baseline FILE] [--write-baseline]

Defaults: --project . , --manifest <project>/arch/architecture.yaml, --baseline <project>/arch/baseline.txt.
Exit 0 when every violation is in the baseline and every baseline entry still occurs,
1 otherwise, 2 on bad usage. --write-baseline records the current violations; once a
baseline exists it may only shrink.

Violations, one baseline key each:
  include A -> B     a file of component A includes a header of B, and A does not depend on B
  requires D -> R    ESP-IDF component directory D requires R, which no component in D may use
  shared C           component C is not its own ESP-IDF component (shares its directory)
  unowned F          source file F in main/ or components/*/ belongs to no component
  ambiguous F        source file F is claimed by two components
  missing C          component C has a path but no files
"""
import argparse
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validate_manifest import validate  # noqa: E402

SOURCE_EXT = {".c", ".h", ".cpp", ".hpp", ".cc", ".hh"}
INCLUDE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*"([^"]+)"', re.M)
CMAKE_KEYWORDS = {"SRCS", "SRC_DIRS", "EXCLUDE_SRCS", "INCLUDE_DIRS", "PRIV_INCLUDE_DIRS", "REQUIRES",
                  "PRIV_REQUIRES", "LDFRAGMENTS", "EMBED_FILES", "EMBED_TXTFILES", "KCONFIG",
                  "KCONFIG_PROJBUILD", "WHOLE_ARCHIVE", "REQUIRED_IDF_TARGETS"}


def idf_component_dirs(root):
    """ESP-IDF component directories of the project: main/ and components/*/ with a CMakeLists.txt.
    shortcut: EXTRA_COMPONENT_DIRS is not read; add it when a project uses it."""
    dirs = [root / "main"] + sorted(p for p in (root / "components").glob("*") if p.is_dir())
    return [d for d in dirs if (d / "CMakeLists.txt").is_file()]


def cmake_requirements(comp_dir):
    """REQUIRES + PRIV_REQUIRES from idf_component_register, plus idf_component.yml dependencies
    (the component manager adds those). Names use the registry form, e.g. espressif/mqtt.
    shortcut: literal names only; ${VAR} and if() blocks are not evaluated."""
    text = re.sub(r"#[^\n]*", "", (comp_dir / "CMakeLists.txt").read_text(encoding="utf-8"))
    reqs = set()
    for call in re.findall(r"idf_component_register\s*\((.*?)\)", text, re.S):
        current = None
        for tok in call.split():
            tok = tok.strip('"')
            if tok in CMAKE_KEYWORDS:
                current = tok
            elif current in ("REQUIRES", "PRIV_REQUIRES"):
                reqs.add(normalize(tok))
    manifest = comp_dir / "idf_component.yml"
    if manifest.is_file():
        deps = (yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}).get("dependencies") or {}
        reqs |= {normalize(n) for n in deps if n != "idf"}
    return reqs


def normalize(name):
    return name.replace("__", "/")


def owned_files(root, comps):
    """{relative posix path: [component ids]} for every source file a component claims."""
    owners = {}
    for c in comps:
        if "path" not in c:
            continue  # planned component, no code yet
        if "sources" in c:
            files = [f for g in c["sources"] for f in root.glob(g)]
        else:
            files = (root / c["path"]).rglob("*")
        for f in files:
            if f.is_file() and f.suffix in SOURCE_EXT:
                owners.setdefault(f.relative_to(root).as_posix(), []).append(c["id"])
    return owners


def find_violations(root, manifest):
    """{baseline key: example detail}."""
    comps = {c["id"]: c for c in manifest["components"]}
    rank = {l["id"]: i for i, l in enumerate(manifest["layers"])}
    owners = owned_files(root, comps.values())
    found = {}

    for f, ids in owners.items():
        if len(ids) > 1:
            found[f"ambiguous {f}"] = f"claimed by {', '.join(sorted(ids))}"
    for c in comps.values():
        if "path" in c and not any(c["id"] in ids for ids in owners.values()):
            found[f"missing {c['id']}"] = f"no source files under {c['path']}"

    # header basename -> owning component (first owner wins when ambiguous: reported above)
    header_owner = {}
    for f, ids in owners.items():
        header_owner.setdefault(pathlib.PurePosixPath(f).name, ids[0])

    for f, ids in sorted(owners.items()):
        src = ids[0]
        text = (root / f).read_text(encoding="utf-8", errors="replace")
        for m in INCLUDE.finditer(text):
            dst = header_owner.get(pathlib.PurePosixPath(m.group(1)).name)
            if dst is None or dst == src or dst in comps[src].get("depends_on", []):
                continue  # not one of ours (ESP-IDF, libc), own header, or allowed
            key = f"include {src} -> {dst}"
            if key not in found:
                line = text.count("\n", 0, m.start()) + 1
                upward = rank[comps[dst]["layer"]] < rank[comps[src]["layer"]]
                found[key] = f"{f}:{line}" + (" (upward)" if upward else "")

    component_dirs = {d.resolve(): d for d in idf_component_dirs(root)}
    by_dir = {}
    for c in comps.values():
        if "path" in c:
            by_dir.setdefault((root / c["path"]).resolve(), []).append(c)
    for d, members in by_dir.items():
        if len(members) > 1:
            for c in members:
                others = sorted(o["id"] for o in members if o is not c)
                found[f"shared {c['id']}"] = f"{c['path']} also holds {', '.join(others)}"
    for d_abs, d in component_dirs.items():
        members = by_dir.get(d_abs, [])
        allowed = {normalize(r) for c in members for r in c.get("idf_requires", [])}
        for c in members:
            for dep in c.get("depends_on", []):
                if "path" in comps[dep]:
                    allowed.add(pathlib.PurePosixPath(comps[dep]["path"]).name)
        for req in sorted(cmake_requirements(d) - allowed):
            found[f"requires {d.name} -> {req}"] = f"{d.relative_to(root).as_posix()}/CMakeLists.txt or idf_component.yml"

    for d in component_dirs.values():
        for f in d.rglob("*"):
            rel = f.relative_to(root).as_posix()
            if f.is_file() and f.suffix in SOURCE_EXT and rel not in owners:
                found[f"unowned {rel}"] = "no component's path or sources covers it"
    return found


def read_baseline(path):
    if not path.is_file():
        return None
    return {l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=".")
    ap.add_argument("--manifest")
    ap.add_argument("--baseline")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args(argv[1:])
    root = pathlib.Path(args.project).resolve()
    manifest_path = pathlib.Path(args.manifest) if args.manifest else root / "arch" / "architecture.yaml"
    baseline_path = pathlib.Path(args.baseline) if args.baseline else root / "arch" / "baseline.txt"

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        print(f"{manifest_path}: {e}")
        return 1
    errors = validate(manifest)
    if errors:
        for e in errors:
            print(f"{manifest_path}: {e}")
        print("Fix the manifest first.")
        return 1

    found = find_violations(root, manifest)
    baseline = read_baseline(baseline_path)

    if args.write_baseline:
        grown = sorted(set(found) - baseline) if baseline is not None else []
        if grown:
            for k in grown:
                print(f"new: {k}  [{found[k]}]")
            print(f"{baseline_path}: the baseline may only shrink; fix the violations above instead.")
            return 1
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text("# Known architecture violations. May only shrink. Written by check_architecture.py.\n"
                                 + "".join(f"{k}\n" for k in sorted(found)), encoding="utf-8")
        print(f"{baseline_path}: {len(found)} entries")
        return 0

    baseline = baseline or set()
    new = sorted(set(found) - baseline)
    stale = sorted(baseline - set(found))
    for k in new:
        print(f"violation: {k}  [{found[k]}]")
    for k in stale:
        print(f"fixed, remove from baseline: {k}")
    known = len(set(found) & baseline)
    print(f"{len(new)} new, {known} in baseline, {len(stale)} stale baseline entries")
    return 1 if new or stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
