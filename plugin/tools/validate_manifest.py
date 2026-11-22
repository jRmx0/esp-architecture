"""Validate an .esp-architecture/architecture.yaml: JSON Schema first, then cross-references and layer rules.

usage: python validate_manifest.py <architecture.yaml>
Exit 0 when valid, 1 with one error per line otherwise.
"""
import json
import pathlib
import sys

import jsonschema
import yaml

SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schema" / "architecture.schema.json"


def schema_errors(manifest):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
        for e in jsonschema.Draft202012Validator(schema).iter_errors(manifest)
    ]


def validate(manifest):
    """Return a list of error strings; empty means valid."""
    errors = schema_errors(manifest)
    if errors:
        return errors  # cross-reference checks assume the shape is right

    ctx = manifest.get("context", {})
    hw = manifest.get("hardware", {})
    layers = [l["id"] for l in manifest["layers"]]
    subsystems = [s["id"] for s in manifest["subsystems"]]
    comps = {c["id"]: c for c in manifest["components"]}
    actors = [a["id"] for a in ctx.get("actors", [])]
    buses = [b["id"] for b in hw.get("buses", [])]
    devices = [d["id"] for d in hw.get("devices", [])]

    # one namespace for everything a diagram draws as a box
    seen = {"system"}
    for kind, ids in (("subsystem", subsystems), ("layer", layers), ("component", [c["id"] for c in manifest["components"]]),
                      ("actor", actors), ("bus", buses), ("device", devices)):
        for i in ids:
            if i in seen:
                errors.append(f"{kind} {i}: id used twice (or 'system', which is reserved)")
            seen.add(i)
    task_ids = [t["id"] for t in manifest.get("tasks", [])]
    errors += [f"task {t}: id used twice" for t in sorted({t for t in task_ids if task_ids.count(t) > 1})]

    for d in hw.get("devices", []):
        for b in [d["bus"]] if isinstance(d["bus"], str) else d["bus"]:
            if b not in buses:
                errors.append(f"device {d['id']}: bus {b} is not declared")
    for f in ctx.get("flows", []):
        ends = {f["from"], f["to"]}
        for e in ends - {"system"}:
            if e not in actors:
                errors.append(f"flow {f['from']} -> {f['to']}: {e} is not an actor")
    for kind in ("tasks", "isrs"):
        for t in manifest.get(kind, []):
            if t["component"] not in comps:
                errors.append(f"{kind[:-1]} {t['id']}: component {t['component']} is not declared")

    used = {c["subsystem"] for c in manifest["components"]}
    errors += [f"component {c['id']}: subsystem {c['subsystem']} is not declared"
               for c in manifest["components"] if c["subsystem"] not in subsystems]
    errors += [f"subsystem {s}: no component belongs to it" for s in subsystems if s not in used]

    rank = {l: i for i, l in enumerate(layers)}  # 0 = top
    sideways = manifest.get("allow_sideways", True)
    for c in manifest["components"]:
        if c["layer"] not in rank:
            errors.append(f"component {c['id']}: layer {c['layer']} is not declared")
            continue
        for h in c.get("hardware", []):
            if h not in buses and h not in devices:
                errors.append(f"component {c['id']}: hardware {h} is not a declared bus or device")
        for dep in c.get("depends_on", []):
            if dep == c["id"]:
                errors.append(f"component {c['id']}: depends on itself")
            elif dep not in comps:
                errors.append(f"component {c['id']}: depends on undeclared component {dep}")
            elif comps[dep]["layer"] in rank:
                here, there = rank[c["layer"]], rank[comps[dep]["layer"]]
                if there < here:
                    errors.append(f"component {c['id']} ({c['layer']}) depends on {dep} ({comps[dep]['layer']}): upward")
                elif there == here and not sideways:
                    errors.append(f"component {c['id']} depends on {dep}: same layer, allow_sideways is false")

    errors += [f"dependency cycle: {' -> '.join(cyc)}" for cyc in _cycles(comps)]
    return errors


def _cycles(comps):
    """One representative path per cycle found by DFS over depends_on."""
    found, state = [], {}  # state: 1 = on stack, 2 = done

    def visit(node, path):
        state[node] = 1
        for dep in comps[node].get("depends_on", []):
            if dep not in comps:
                continue
            if state.get(dep) == 1:
                found.append(path[path.index(dep):] + [dep])
            elif dep not in state:
                visit(dep, path + [dep])
        state[node] = 2

    for c in comps:
        if c not in state:
            visit(c, [c])
    return found


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = pathlib.Path(argv[1])
    try:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        print(f"{path}: {e}")
        return 1
    errors = validate(manifest if manifest is not None else {})
    for e in errors:
        print(f"{path}: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
