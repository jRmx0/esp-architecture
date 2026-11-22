"""Generate Mermaid diagrams from arch/architecture.yaml: context, block, organigram, layering.

usage: python generate_diagrams.py [--project DIR] [--manifest FILE] [--out FILE] [--level N] [--check | --as-is]

Writes a marked section into --out (default <project>/arch/diagrams.md). An existing file keeps
everything outside the markers, so the section can live inside a wiki page.
--check   exit 1 when the section differs from what the manifest generates (stale diagrams)
--as-is   print the include graph the code has now (from check_architecture), for discovery
"""
import argparse
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_architecture import include_edges, owned_files  # noqa: E402
from validate_manifest import schema_errors, validate  # noqa: E402

BEGIN = "<!-- esp-architecture:diagrams begin: generated from {src} by generate_diagrams.py, do not edit -->"
END = "<!-- esp-architecture:diagrams end -->"
SECTION = re.compile(r"<!-- esp-architecture:diagrams begin.*?<!-- esp-architecture:diagrams end -->", re.S)
RED = "stroke:#d33,stroke-width:2px"


def node(i):
    return f"n_{i}"  # prefix: Mermaid reserves words like end, graph, style


def label(*lines):
    text = "<br/>".join(l for l in lines if l)
    return '"' + text.replace('"', "#quot;") + '"'


def fence(lines):
    return "```mermaid\n" + "\n".join(lines) + "\n```"


def context(m):
    ctx = m.get("context", {})
    shape = {"person": ("([", "])"), "system": ("[", "]"), "device": ("{{", "}}")}
    out = ["flowchart LR", f"  {node('system')}[[{label('<b>' + m['system']['name'] + '</b>', m['system']['description'])}]]"]
    for a in ctx.get("actors", []):
        o, c = shape[a["kind"]]
        out.append(f"  {node(a['id'])}{o}{label('<b>' + a['id'] + '</b>', a['description'])}{c}")
    for f in ctx.get("flows", []):
        out.append(f"  {node(f['from'])} -->|{label(f['data'])}| {node(f['to'])}")
    return fence(out)


def block(m):
    hw = m.get("hardware", {})
    out = ["flowchart LR", f"  subgraph chip[{label(m['system']['name'])}]", "    direction TB"]
    out += [f"    {node(b['id'])}[/{label(b['id'], b['kind'])}/]" for b in hw.get("buses", [])]
    out += [f"    {node(c['id'])}[{label(c['id'])}]" for c in m["components"]]
    out.append("  end")
    out += [f"  {node(d['id'])}{{{{{label(d['id'], d['description'])}}}}}" for d in hw.get("devices", [])]
    out += [f"  {node(d['bus'])} --- {node(d['id'])}" for d in hw.get("devices", [])]
    out += [f"  {node(c['id'])} --- {node(h)}" for c in m["components"] for h in c.get("hardware", [])]
    return fence(out)


def tasks(m):
    rows = [f"| `{t['id']}` | {t['component']} | {t.get('priority', '')} | {t.get('stack', '')} |" for t in m.get("tasks", [])]
    rows += [f"| ISR `{i['id']}` | {i['component']} | {i['source']} | |" for i in m.get("isrs", [])]
    if not rows:
        return ""
    return "\n\n| Task | Component | Priority | Stack |\n|---|---|---|---|\n" + "\n".join(rows)


def organigram(m):
    comps = {c["id"]: c for c in m["components"]}
    rank = {l["id"]: i for i, l in enumerate(m["layers"])}
    out = ["flowchart TD"]
    out += [f"  {node(c['id'])}[{label(c['id'])}]" for c in m["components"]]
    users, upward, n = {}, [], 0
    for c in m["components"]:
        for d in c.get("depends_on", []):
            out.append(f"  {node(c['id'])} --> {node(d)}")
            users.setdefault(d, []).append(c["id"])
            if d in comps and rank.get(comps[d]["layer"], 0) < rank.get(c["layer"], 0):
                upward.append(str(n))
            n += 1
    shared = [d for d, u in users.items() if len(u) > 1]
    if shared:
        out.append(f"  classDef shared {RED}")
        out.append(f"  class {','.join(node(d) for d in shared)} shared")
    if upward:
        out.append(f"  linkStyle {','.join(upward)} {RED}")
    return fence(out), shared, len(upward)


def layering(m):
    out = ["flowchart TB"]
    for layer in m["layers"]:
        members = [c for c in m["components"] if c["layer"] == layer["id"]]
        out += [f"  subgraph L_{layer['id']}[{label('<b>' + layer['id'] + '</b>: ' + layer['description'])}]", "    direction LR"]
        out += [f"    {node(c['id'])}[{label(c['id'])}]" for c in members] or [f"    empty_{layer['id']}[ ]"]
        out.append("  end")
    ids = [f"L_{l['id']}" for l in m["layers"]]
    out += [f"  {a} ~~~ {b}" for a, b in zip(ids, ids[1:])]  # invisible links keep the layers stacked in order
    return fence(out)


def render(m, src, level=2):
    h = "#" * level
    org, shared, upward = organigram(m)
    note = (f" Red boxes: used by more than one component ({', '.join(shared)}); a shared resource needs care "
            "against contention." if shared else "")
    note += f" Red arrows: {upward} upward, which the layers forbid." if upward else ""
    return "\n".join([
        BEGIN.format(src=src), "",
        f"{h} Context", "", "The device and the world around it.", "", context(m), "",
        f"{h} Block", "", "Inside the chip: components and the buses they drive; outside: devices on those buses.", "",
        block(m) + tasks(m), "",
        f"{h} Organigram", "", "Who calls whom, from the top down (`depends_on`)." + note, "", org, "",
        f"{h} Layering", "", "Layers from the top (application) to the bottom (platform).", "", layering(m), "",
        END,
    ])


def as_is(root, m):
    comps = {c["id"]: c for c in m["components"]}
    rank = {l["id"]: i for i, l in enumerate(m["layers"])}
    edges = include_edges(root, owned_files(root, comps.values()))
    out, bad = ["flowchart TD"], []
    for n, ((src, dst), _) in enumerate(sorted(edges.items())):
        out.append(f"  {node(src)}[{label(src)}] --> {node(dst)}[{label(dst)}]")
        if dst not in comps[src].get("depends_on", []):
            bad.append(str(n))
    if bad:
        out.append(f"  linkStyle {','.join(bad)} {RED}")
    upward = sum(1 for s, d in edges if rank[comps[d]["layer"]] < rank[comps[s]["layer"]])
    return (f"Includes between components in the code now: {len(edges)} edges, {len(bad)} not in the manifest (red), "
            f"{upward} upward.\n\n" + fence(out) + "\n")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=".")
    ap.add_argument("--manifest")
    ap.add_argument("--out")
    ap.add_argument("--level", type=int, default=2, choices=range(1, 7))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--as-is", action="store_true")
    args = ap.parse_args(argv[1:])
    root = pathlib.Path(args.project).resolve()
    manifest_path = pathlib.Path(args.manifest).resolve() if args.manifest else root / "arch" / "architecture.yaml"
    out_path = pathlib.Path(args.out).resolve() if args.out else root / "arch" / "diagrams.md"

    try:
        m = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        print(f"{manifest_path}: {e}")
        return 1
    errors = schema_errors(m)
    if errors:
        for e in errors:
            print(f"{manifest_path}: {e}")
        print("Fix the manifest first.")
        return 1
    for e in validate(m):  # still drawable; upward edges show in red
        print(f"warning: {manifest_path}: {e}", file=sys.stderr)

    if args.as_is:
        sys.stdout.write(as_is(root, m))
        return 0

    try:
        src = manifest_path.relative_to(root).as_posix()
    except ValueError:
        src = manifest_path.name
    section = render(m, src, args.level)
    old = out_path.read_text(encoding="utf-8") if out_path.is_file() else ""
    match = SECTION.search(old)
    if args.check:
        if match and match.group(0) == section:
            return 0
        print(f"{out_path}: diagrams are stale or missing; run generate_diagrams.py")
        return 1
    if match:
        new = old[:match.start()] + section + old[match.end():]
    else:
        new = (old.rstrip("\n") + "\n\n" if old else "") + section + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(new, encoding="utf-8")
    print(f"{out_path}: diagrams written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
