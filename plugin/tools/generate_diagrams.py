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
NBSP = "&nbsp;"
PER_LINE = 6  # components per line in the layering grid


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
    # names only: the context diagram is about relationships, not what is inside any box
    out = ["flowchart LR", f"  {node('system')}[[{label('<b>' + m['system']['name'] + '</b>')}]]"]
    for a in ctx.get("actors", []):
        o, c = shape[a["kind"]]
        out.append(f"  {node(a['id'])}{o}{label(a['id'])}{c}")
    for f in ctx.get("flows", []):
        arrow = f"-->|{label(f['data'])}|" if f.get("data") else "-->"
        out.append(f"  {node(f['from'])} {arrow} {node(f['to'])}")
    return fence(out)


def bus_ids(device):
    """A device's `bus` is one bus id or a list of them."""
    return [device["bus"]] if isinstance(device["bus"], str) else device["bus"]


def block(m):
    """Level 1, hardware only: the processor with its buses on its left and right edges, each device
    outside beside its bus. Components come in lower levels."""
    # block-beta gives every grid column the same width, so the processor is one block spanning
    # three outer columns and the device columns beside it stay narrow.
    hw = m.get("hardware", {})
    buses, devices = hw.get("buses", []), hw.get("devices", [])
    on = {b["id"]: [d for d in devices if b["id"] in bus_ids(d)] for b in buses}
    # Buses joined by a device stay on one edge, so its lines don't cross the chip. Groups go
    # largest first to the edge with fewer rows; a device sits beside the first of its buses.
    groups, seen = [], set()
    for b in buses:
        if b["id"] in seen:
            continue
        group, todo = [], [b]
        while todo:
            x = todo.pop(0)
            if x["id"] not in seen:
                seen.add(x["id"])
                group.append(x)
                todo += [y for y in buses for d in on[x["id"]] if y["id"] in bus_ids(d)]
        group.sort(key=buses.index)
        cells, placed = [], set()
        for x in group:
            new = [d for d in on[x["id"]] if d["id"] not in placed]
            placed.update(d["id"] for d in new)
            cells += [(x, new[0] if new else None)] + [(None, d) for d in new[1:]]
        groups.append(cells)
    rows = ([], [])
    for cells in sorted(groups, key=len, reverse=True):
        rows[len(rows[1]) < len(rows[0])].extend(cells)
    height = max(1, *map(len, rows))  # one row at least, for the processor's name
    rows = [r + [(None, None)] * (height - len(r)) for r in rows]
    title = hw.get("processor", m["system"]["name"])

    # Every cell has exactly two lines: the side columns are separate grids, so devices line up
    # with their buses only while all cells are the same height. A blank line is a no-break space.
    def dev(d):
        if not d:
            return "    space"
        return f"    {node(d['id'])}[{label(d['id'], ', '.join(d.get('holds', [])) or NBSP)}]"

    def bus(b):
        return f"    {node(b['id'])}[/{label(b.get('peripheral', b['kind'].upper()), b['id'])}/]" if b else "    space"

    out = ["block-beta", "  columns 5", "  block:left", "    columns 1"]
    out += [dev(d) for _, d in rows[0]]
    out += ["  end", "  block:chip:3", "    columns 3"]
    for n, ((lb, _), (rb, _)) in enumerate(zip(*rows)):
        # the processor's name sits in the empty middle column, not a row of its own
        middle = f"    chip_title[{label('<b>' + title + '</b>')}]" if n == 0 else "    space"
        out += [bus(lb), middle, bus(rb)]
    out += ["  end", "  block:right", "    columns 1"]
    out += [dev(d) for _, d in rows[1]]
    out += ["  end", "  style left fill:none,stroke:none", "  style right fill:none,stroke:none"]
    out += [f"  {node(b)} --- {node(d['id'])}" for d in devices for b in bus_ids(d)]
    out += ["  classDef title fill:none,stroke:none", "  classDef device fill:none,stroke:#888",
            "  classDef planned fill:none,stroke:#888,stroke-dasharray:4 3", "  class chip_title title"]
    for cls, ds in (("device", [d for d in devices if not d.get("planned")]),
                    ("planned", [d for d in devices if d.get("planned")])):
        if ds:
            out.append(f"  class {','.join(node(d['id']) for d in ds)} {cls}")
    # GPIO lines are separate pins, so several devices on GPIO do not contend
    shared = [b["id"] for b in buses if len(on[b["id"]]) > 1 and b["kind"] != "gpio"]
    if shared:
        out += [f"  classDef shared {RED}", f"  class {','.join(node(b) for b in shared)} shared"]
    return fence(out), shared


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
    # block-beta draws a grid: one row per layer, a title cell, then the layer's components.
    # flowchart subgraphs left uneven empty space between layers in GitHub's renderer.
    # A layer with more than PER_LINE components wraps onto further lines, so the grid stays
    # narrow enough for GitHub to draw it at a readable size.
    rows = [(l, [c["id"] for c in m["components"] if c["layer"] == l["id"]]) for l in m["layers"]]
    per_line = max(1, min(PER_LINE, max(len(members) for _, members in rows)))
    out = ["block-beta", "  columns 1"]
    for layer, members in rows:
        out += [f"  block:r_{layer['id']}", f"    columns {per_line + 1}"]
        lines = [members[i:i + per_line] for i in range(0, len(members), per_line)] or [[]]
        for n, chunk in enumerate(lines):
            # id only: every column is as wide as the widest cell, so a long title would widen the grid
            out.append(f"    t_{layer['id']}[{label(layer['id'])}]" if n == 0 else "    space")
            out += [f"    {node(c)}[{label(c)}]" for c in chunk]
            out += ["    space"] * (per_line - len(chunk))
        out.append("  end")
    out += ["  classDef title fill:none,stroke:#888,font-weight:bold", f"  class {','.join('t_' + l['id'] for l, _ in rows)} title"]
    table = "\n".join(f"| `{l['id']}` | {l['description']} |" for l, _ in rows)
    return fence(out) + "\n\n| Layer | Holds |\n|---|---|\n" + table


def render(m, src, level=2):
    h = "#" * level
    org, shared, upward = organigram(m)
    note = (f" Red boxes: used by more than one component ({', '.join(shared)}); a shared resource needs care "
            "against contention." if shared else "")
    note += f" Red arrows: {upward} upward, which the layers forbid." if upward else ""
    blk, shared_buses = block(m)
    bnote = (f" Red buses: more than one device ({', '.join(shared_buses)}); they contend for the bus."
             if shared_buses else "")
    return "\n".join([
        BEGIN.format(src=src), "",
        f"{h} Context", "", "The device and the world around it.", "", context(m), "",
        f"{h} Block", "", "Level 1, hardware: the processor, its buses on its edges and the devices outside on them."
        + bnote, "", blk, "",
        f"{h} Organigram", "", "Who calls whom, from the top down (`depends_on`)." + note, "", org + tasks(m), "",
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
