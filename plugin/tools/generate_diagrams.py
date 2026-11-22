"""Generate Mermaid diagrams from arch/architecture.yaml: context, block (levels 1 and 2), organigram, layering.

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
RED = "stroke:#d33,stroke-width:2px"  # breaks a rule
AMBER = "stroke:#d98e04,stroke-width:2px"  # shared: check contention
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


# Kinds whose devices use their own pins or channels: several devices on one do not contend.
SEPARATE_PINS = {"gpio", "adc", "pwm"}


def shared_buses(buses, devices):
    return [b["id"] for b in buses
            if sum(b["id"] in bus_ids(d) for d in devices) > 1 and b["kind"] not in SEPARATE_PINS]


def block(m):
    """Level 1: a hardware and a software block diagram. Hardware: one processor box and each
    device outside it, joined by one line per bus, labelled with the bus's peripheral. Software:
    the same, but each bus is a box inside the processor, because it is driver code to write.
    Components come in lower levels."""
    # Flowcharts, not block-beta: block-beta cannot make boxes touch only when connected.
    # No layout hints: the lines say only what is connected, and Mermaid places the boxes.
    hw = m.get("hardware", {})
    buses, devices = hw.get("buses", []), hw.get("devices", [])
    tag = {b["id"]: b.get("peripheral", b["kind"].upper()) for b in buses}
    shared = shared_buses(buses, devices)
    links = [(d, b) for d in devices for b in bus_ids(d)]  # every line runs inside out
    title = label("<b>" + hw.get("processor", m["system"]["name"]) + "</b>")
    # names only: what a device holds is a software decision, shown in lower levels
    boxes = [f"  {node(d['id'])}[{label(d.get('name', d['id']))}]" for d in devices]
    style = ["  classDef device fill:none,stroke:#888",
             f"  class {','.join(node(d['id']) for d in devices)} device"] if devices else []
    amber = ",".join(str(n) for n, (_, b) in enumerate(links) if b in shared)
    amber = [f"  linkStyle {amber} {AMBER}"] if amber else []

    # cpu_box has no n_ prefix, so no device or bus id can collide with it
    hard = ["flowchart LR", f"  cpu_box[{title}]", *boxes]
    hard += [f"  cpu_box ---|{label(tag[b])}| {node(d['id'])}" for d, b in links]
    soft = ["flowchart LR", f"  subgraph cpu_box[{title}]"]
    soft += [f"    {node(b['id'])}[{label(tag[b['id']])}]" for b in buses] + ["  end", *boxes]
    soft += [f"  {node(b)} --- {node(d['id'])}" for d, b in links]
    if shared:
        soft += [f"  classDef shared {AMBER}", f"  class {','.join(node(b) for b in shared)} shared"]
    return fence(hard + style + amber), fence(soft + style + amber), shared


def subsystems(m):
    """Level 2: the processor holds one box per subsystem and one per bus; devices sit outside on
    their buses as in level 1b. Lines join a subsystem to the buses its components drive. No arrows
    between subsystems: a plain line joins two when a component of one depends on one of the other,
    either way; who calls whom is the organigram's job. No layout hints: Mermaid places the boxes."""
    hw = m.get("hardware", {})
    buses, devices = hw.get("buses", []), hw.get("devices", [])
    dev_buses = {d["id"]: bus_ids(d) for d in devices}
    drives = {}  # a dict as an ordered set
    for c in m["components"]:
        for h in c.get("hardware", []):
            for b in dev_buses.get(h, [h]):  # a device stands for the buses it is on
                drives[(c["subsystem"], b)] = None
    title = label("<b>" + hw.get("processor", m["system"]["name"]) + "</b>")
    out = ["flowchart LR", f"  subgraph cpu_box[{title}]"]
    out += [f"    {node(s['id'])}[{label('<b>' + s['id'] + '</b>')}]" for s in m["subsystems"]]
    out += [f"    {node(b['id'])}[{label(b.get('peripheral', b['kind'].upper()))}]" for b in buses]
    out += ["  end"] + [f"  {node(d['id'])}[{label(d.get('name', d['id']))}]" for d in devices]
    out += [f"  {node(s)} --- {node(b)}" for s, b in drives]
    out += [f"  {node(b)} --- {node(d['id'])}" for d in devices for b in bus_ids(d)]
    order = {s["id"]: i for i, s in enumerate(m["subsystems"])}
    sub = {c["id"]: c["subsystem"] for c in m["components"]}
    links = {tuple(sorted((sub[c["id"]], sub[d]), key=order.get))
             for c in m["components"] for d in c.get("depends_on", []) if d in sub and sub[d] != sub[c["id"]]}
    out += [f"  {node(a)} --- {node(b)}" for a, b in sorted(links, key=lambda l: (order[l[0]], order[l[1]]))]
    out += ["  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3"] if buses else []
    out += [f"  class {','.join(node(b['id']) for b in buses)} bus"] if buses else []
    out += ["  classDef device fill:none,stroke:#888",
            f"  class {','.join(node(d['id']) for d in devices)} device"] if devices else []
    shared = shared_buses(buses, devices)
    out += [f"  classDef shared {AMBER}", f"  class {','.join(node(b) for b in shared)} shared"] if shared else []
    table = "\n".join(f"| `{s['id']}` | {', '.join(c['id'] for c in m['components'] if c['subsystem'] == s['id'])} "
                      f"| {s['description']} |" for s in m["subsystems"])
    return fence(out) + "\n\n| Subsystem | Components | Does |\n|---|---|---|\n" + table


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
        out.append(f"  classDef shared {AMBER}")
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
    note = (f" Amber boxes: used by more than one component ({', '.join(shared)}); "
            "check contention (one caller at a time, locking, the slowest caller sets the pace)." if shared else "")
    note += f" Red arrows: {upward} upward, which the layers forbid." if upward else ""
    hard, soft, shared_buses = block(m)
    hw_text = m.get("hardware", {}).get("description")
    bnote = (f" Amber: a bus shared by several devices ({', '.join(shared_buses)}); check contention "
             "(one transfer at a time, locking, the slowest device sets the speed)." if shared_buses else "")
    return "\n".join([
        BEGIN.format(src=src), "",
        f"{h} Context", "", "The device and the world around it.", "", context(m), "",
        f"{h} Block", "",
        f"{h}# Level 1a: hardware", "", "The processor and the devices outside it, one line per bus."
        + (f" {hw_text}" if hw_text else "") + bnote, "", hard, "",
        f"{h}# Level 1b: software", "", "The same hardware, each bus a box inside the processor: the drivers to write.",
        "", soft, "",
        f"{h}# Level 2: subsystems", "", "The subsystems inside the processor, each joined to the buses it drives and to the subsystems it is connected to.", "", subsystems(m), "",
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
