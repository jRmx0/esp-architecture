# esp-architecture: architecture as code for ESP-IDF projects

What the [esp-architecture](https://github.com/jRmx0/esp-architecture) plugin is and how it is used. The plan and open work are in [epic #1](https://github.com/jRmx0/esp-architecture/issues/1).

## 1. Purpose

AI agents that write ESP-IDF firmware tend to ignore architecture. The plugin makes the architecture a file the build and a checker enforce, so a violation blocks the agent instead of being a review comment.

## 2. Current state

The plugin installs in Claude Code and has no skills or hooks yet. It ships the manifest schema and its validator (§4). The checker that compares code with the manifest, the diagram generator and the skills are planned in the epic's sub-issues.

## 3. Rule sources

Rules are public, in our own words, each with an ID and a rationale. Where a rule comes from (book, page, context) is kept only in each maintainer's local `sources.local.yaml`, which git ignores, so no copyrighted text or citation is published. Espressif documentation is cited openly.

## 4. The manifest: `arch/architecture.yaml`

One file per project describes the architecture. The checker and the diagram generator read only this file. Schema: `plugin/schema/architecture.schema.json` (editors with the YAML language server pick it up from a `# yaml-language-server: $schema=...` first line). Example: `examples/gateway/architecture.yaml`, the rmx-mower-gateway target layers.

| Section | Holds | Feeds |
|---|---|---|
| `system` | Name and purpose | Every diagram's title |
| `context` | `actors` (person, system, device) and `flows` between `system` and an actor | Context diagram |
| `hardware` | `buses` inside the chip, `devices` on a bus | Block diagram |
| `layers` | Ordered from the top (application) to the bottom (platform) | Layering diagram |
| `components` | Layer, `path`, `depends_on` (other components), `idf_requires` (ESP-IDF or managed components), `hardware`, `interfaces` (public headers), `requirements` (`REQ-nnn`), `decisions` (`DEC-nnn`) | Block diagram boxes; `depends_on` is the organigram |
| `allow_sideways` | Whether a component may depend on one in its own layer (default true) | Validator |
| `tasks`, `isrs` | Owner component, priority, stack, source | Block diagram notes, the checker |

Validate:

```
pip install -r requirements.txt
python plugin/tools/validate_manifest.py arch/architecture.yaml
```

Exit 0 when valid, 1 with one error per line. Besides the schema it checks:

- every id is unique across layers, components, actors, buses and devices; `system` is reserved
- every reference exists: a component's layer, `depends_on`, `hardware`; a device's bus; a flow's actor; a task's or ISR's component
- every flow has `system` at one end
- dependencies go down or sideways, never up; sideways only with `allow_sideways`
- no dependency cycles

Tests: `python -m unittest discover -s tests`.
