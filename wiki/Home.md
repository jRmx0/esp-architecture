# esp-architecture: architecture as code for ESP-IDF projects

What the [esp-architecture](https://github.com/jRmx0/esp-architecture) plugin is and how it is used. The plan and open work are in [epic #1](https://github.com/jRmx0/esp-architecture/issues/1).

## 1. Purpose

AI agents that write ESP-IDF firmware tend to ignore architecture. The plugin makes the architecture a file the build and a checker enforce, so a violation blocks the agent instead of being a review comment.

## 2. Current state

The plugin installs in Claude Code and has no skills or hooks yet. It ships the manifest schema and its validator (§4) the checker that compares the code with the manifest (§5) and the diagram generator (§6). The skills, hooks and decision records are planned in the epic's sub-issues.

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
| `components` | Layer, `path` (the ESP-IDF component directory), `sources` (globs of the files it owns; default all sources under `path`), `depends_on` (other components), `idf_requires` (ESP-IDF or managed components), `hardware`, `interfaces` (public headers), `requirements` (`REQ-nnn`), `decisions` (`DEC-nnn`) | Block diagram boxes; `depends_on` is the organigram |
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

## 5. The checker

```
python plugin/tools/check_architecture.py --project <project root>
```

Reads `arch/architecture.yaml` (validated first) and `arch/baseline.txt`, then the project's ESP-IDF component directories: `main/` and `components/*/` with a `CMakeLists.txt`. Each violation has a stable key:

| Key | Meaning |
|---|---|
| `include A -> B` | A file of component A includes a header of component B, and A does not list B in `depends_on`. The detail says `(upward)` when B is in a higher layer. One key per pair of components, not per file. |
| `requires D -> R` | ESP-IDF component directory D requires R (`REQUIRES`, `PRIV_REQUIRES` or an `idf_component.yml` dependency), and no component in D allows it through `idf_requires` or `depends_on`. |
| `shared C` | Component C shares its ESP-IDF component directory with another component, so the build cannot enforce the boundary between them. |
| `unowned F` | Source file F belongs to no component. |
| `ambiguous F` | Two components claim file F. |
| `missing C` | Component C has a `path` but no files. Components without a `path` are planned and skipped. |

Exit 0 when every violation is in the baseline and every baseline entry still occurs; 1 otherwise. `--write-baseline` records the current violations. Once a baseline exists it may only shrink: writing refuses new entries, and a fixed violation left in the baseline fails the check until it is removed. Done means an empty baseline.

Includes are matched by header file name against the files components own; headers no component owns (ESP-IDF, libc) are skipped, and the build enforces those once each component is its own ESP-IDF component.

Why it reads `CMakeLists.txt` and not the build's `project_description.json`: the description is only as current as the last build. PlatformIO writes it to `.pio/build/<env>/project_description.json`; in rmx-mower-gateway both that copy and `build/project_description.json` predated the last `main/CMakeLists.txt` change (checked 2026-11-22). Limits: literal names only (no `${VAR}`, no `if()`), and `EXTRA_COMPONENT_DIRS` is not read.

### 5.1 First run on rmx-mower-gateway (2026-11-22)

Code at `725a2ce`, manifest `examples/gateway/architecture.yaml` with `cell -> usage` removed (the validator rejects that upward edge). 78 violations:

- 16 `shared`: every module except `rmx_codec` lives in `main`.
- 47 `include` pairs, 6 upward: `cell` → `gwstate`, `metrics`, `usage`; `ota` → `supervisor`; `remote_cmd` → `supervisor`; `gw_tasks` → `rmx_codec`. Many of the others are edges the wiki's target graph leaves out on purpose (`gw_tasks`, `settings`) or never drew (`app_main` initialising every module).
- 15 `requires`: the manifest gives no component `idf_requires` yet.

The gap is mostly between the sketch and a manifest precise enough to enforce. Closing it is the pilot's work (rmx-lt/rmx-mower-gateway#120).

## 6. Diagrams

```
python plugin/tools/generate_diagrams.py --project <project root> [--out FILE] [--level N]
python plugin/tools/generate_diagrams.py --project <project root> --check
python plugin/tools/generate_diagrams.py --project <project root> --as-is
```

Writes four Mermaid diagrams, which GitHub renders, into a marked section of `--out` (default `arch/diagrams.md`). Text outside the markers is kept, so the section can sit inside a wiki page; `--level` sets its heading level.

| Diagram | Drawn from | Shows |
|---|---|---|
| Context | `system`, `context` | The device as one box, the actors around it, what flows each way |
| Block | `components`, `hardware`, `tasks` | The chip: components in a row per layer, the peripherals (buses) below them; devices outside, on their bus; which component drives which bus or device. A task table follows. |
| Organigram | `depends_on` | Who calls whom from the top down. Red box: a component used by more than one other (a shared resource). Red arrow: an upward dependency. |
| Layering | `layers`, `components` | A grid: one row per layer from the top, a title cell, then its components (Mermaid `block-beta`) |

`--check` exits 1 when the section is missing or differs from what the manifest generates now. `--as-is` prints the include graph the code has now (from the checker), with includes the manifest does not allow in red; it is for discovery and is not checked.

A manifest with schema errors is refused. Rule errors (an upward edge, a cycle) only warn, so a design under discussion can still be drawn; the checker is what blocks.

Examples, rendered on GitHub: `examples/gateway/diagrams.md` (target) and `examples/gateway/as-is.md` (code at rmx-lt/rmx-mower-gateway `725a2ce`: 69 edges, 46 not in the manifest, 6 upward).
