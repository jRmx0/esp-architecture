# esp-architecture: architecture as code for ESP-IDF projects

What the [esp-architecture](https://github.com/jRmx0/esp-architecture) plugin is and how it is used. The plan and open work are in [epic #1](https://github.com/jRmx0/esp-architecture/issues/1).

## 1. Purpose

AI agents that write ESP-IDF firmware tend to ignore architecture. The plugin makes the architecture a file the build and a checker enforce, so a violation blocks the agent instead of being a review comment.

## 2. Current state

The plugin installs in Claude Code and has no skills or hooks yet. It ships the manifest schema and its validator (§4), the checker that compares the code with the manifest (§5), the diagram generator (§6), the records lint (§7) and the rule catalog (§8). The skills and hooks are planned in the epic's sub-issues.

## 3. Rule sources

Rules are public, in our own words, each with an ID and a rationale. Where a rule comes from (book, page, context) is kept only in each maintainer's local `sources.local.yaml`, which git ignores, so no copyrighted text or citation is published. Espressif documentation is cited openly. The rules are in `plugin/rules/rules.yaml` (§8). Before a PR that touches them, a maintainer runs `python tools/check_sources.py`: it fails when a rule has no entry (source, location, context) in `sources.local.yaml` or an entry names no rule, and it skips when the file is absent, as in CI.

## 4. The manifest: `arch/architecture.yaml`

One file per project describes the architecture. The checker and the diagram generator read only this file. Schema: `plugin/schema/architecture.schema.json` (editors with the YAML language server pick it up from a `# yaml-language-server: $schema=...` first line). Example: `examples/gateway/architecture.yaml`, transcribed from rmx-mower-gateway; not a reviewed design.

| Section | Holds | Feeds |
|---|---|---|
| `system` | Name and purpose | Every diagram's title |
| `context` | `actors` (person, system, device) and `flows` between two parties: `system` (the device) and an actor, or two actors; a flow's `data` is an optional short label | Context diagram |
| `hardware` | `processor` (the chip or module, e.g. ESP32-WROVER-E; optional); `description` (what the processor or module has inside, e.g. integrated flash and PSRAM; optional, shown as text above the block diagram); `buses` inside the chip, each with an optional `peripheral` (e.g. UART2) that labels it; `devices`, each on one `bus` or a list of them (a modem on UART and GPIO), with an optional `name` shown in diagram boxes (the id when absent) and optional `holds` (what it stores, a software decision, to be shown at level 3) | Block diagram |
| `subsystems` | Mandatory, at least one (a small project may have a single one): the few bundles the components fall into, each an `id`, `description` and `decisions` (`DEC-nnn`) | Block level 2 |
| `layers` | Ordered from the top (application) to the bottom (platform), each with `decisions` (`DEC-nnn`) | Layering diagram |
| `components` | `subsystem` (mandatory, a declared subsystem), layer, `path` (the ESP-IDF component directory), `sources` (globs of the files it owns; default all sources under `path`), `depends_on` (other components), `idf_requires` (ESP-IDF or managed components), `hardware`, `interfaces` (public headers), `requirements` (`F-REQ-nnn` or `NF-REQ-nnn`), `decisions` (`DEC-nnn`) | `depends_on` is the organigram |
| `allow_sideways` | Whether a component may depend on one in its own layer (default true) | Validator |
| `tasks`, `isrs` | Owner component, priority, stack, source | Task table under the organigram, the checker |

Validate:

```
pip install -r requirements.txt
python plugin/tools/validate_manifest.py arch/architecture.yaml
```

Exit 0 when valid, 1 with one error per line. Besides the schema it checks:

- every id is unique across subsystems, layers, components, actors, buses and devices; `system` is reserved
- every reference exists: a component's subsystem, layer, `depends_on`, `hardware`; each of a device's buses; a flow's actor; a task's or ISR's component
- dependencies go down or sideways, never up; sideways only with `allow_sideways`
- no dependency cycles
- every subsystem has at least one component

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

Code at `725a2ce`, manifest `examples/gateway/architecture.yaml`, an example transcribed from the as-built code with two fixes (the code's upward `cell -> usage` is not in it; `supervisor -> ntrip` is added), not a reviewed target; the pilot's design will replace it. 78 violations:

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

Writes six Mermaid diagrams (block: levels 1a, 1b and 2), which GitHub renders, into a marked section of `--out` (default `arch/diagrams.md`). Text outside the markers is kept, so the section can sit inside a wiki page; `--level` sets its heading level.

Colour key, the same in every diagram: **amber** = shared (a bus with several devices, a component with several callers): not an error, check contention. **Red** = breaks a rule (an upward dependency; in `--as-is`, an include the manifest does not declare).

| Diagram | Drawn from | Shows |
|---|---|---|
| Context | `system`, `context` | How the device fits into the world: the device as one box, the actors around it and the flows between them, including flows between two actors. Boxes hold names only (descriptions stay in the manifest); an arrow carries its flow's short `data` label, or none. |
| Block | `hardware`, `subsystems` | Levels 1 and 2, three Mermaid flowcharts. **1a, hardware:** one processor box titled with `hardware.processor` (or the system name), showing nothing else, and each device as its own box outside it, showing its `name` (or id), joined by one line per bus the device uses, labelled with the bus's `peripheral` (or the kind in capitals), so a modem on UART and GPIO gets two lines. **1b, software:** the same hardware, but each bus is a box inside the processor, labelled the same way, because it is driver code to write; each device is joined to the bus boxes it uses. Level 1 shows only devices outside the processor or module: memory inside the module (e.g. a WROVER's flash and PSRAM) is not a device, and `hardware.description` mentions it in the text above 1a instead. A device's `holds` are not shown: how a memory is used is a software decision, so level 3 will show it. **Sharing rule:** a bus with more than one device is amber in both diagrams (its lines, and in 1b its box), because the devices share its lines: check contention (one transfer at a time, locking, the slowest device sets the speed); buses of kind `gpio`, `adc` or `pwm` are exempt, because each device there uses its own pins or channels. **Level 2, subsystems:** the processor holds one box per subsystem and the bus boxes of 1b (shared buses amber, as in 1b); devices sit outside on their buses. A line joins a subsystem to each bus its components drive (`hardware`; a device there stands for the buses it is on). A plain line, with no arrowhead, joins two subsystems when a component of one depends on a component of the other, either way; who calls whom is the organigram's job. A table lists each subsystem's components. **Layout:** Mermaid places the boxes; the generator sets no positions, only general rules derived from the manifest. 1a needs none: every line runs from the one processor box to a device. 1b and level 2 have several boxes inside the processor, and without rules Mermaid ranks them by line order, so the hardware edge is lost: in 1b, devices sharing their first bus stay on one side and groups go largest first to the side with fewer lines; at level 2, lines run inside out (subsystem → bus → device, and between subsystems from one that drives no bus to one that does), subsystems that drive a bus sit at the processor's edge, and those that drive none one column further in, with invisible links only where no real line places them. Components themselves come at level 3, planned in its own issue, not yet generated. Flowcharts rather than `block-beta`, because `block-beta` cannot draw boxes that touch only when connected: it has no row span, one padding value is both the margin inside a box and the gap between boxes, and it gives all children of a group the same size. |
| Organigram | `depends_on`, `tasks`, `isrs` | Who calls whom from the top down. Amber box: a component used by more than one other (a shared resource; check contention). Red arrow: an upward dependency, which breaks the layering rule. A task table follows. |
| Layering | `layers`, `components` | A grid (Mermaid `block-beta`): one row per layer from the top, the layer id, then its components, wrapping after 6. A table below gives each layer's description. |

`--check` exits 1 when the section is missing or differs from what the manifest generates now. `--as-is` prints the include graph the code has now (from the checker), with includes the manifest does not allow in red; it is for discovery and is not checked.

A manifest with schema errors is refused. Rule errors (an upward edge, a cycle) only warn, so a design under discussion can still be drawn; the checker is what blocks.

Examples, rendered on GitHub: `examples/gateway/diagrams.md` (target) and `examples/gateway/as-is.md` (code at rmx-lt/rmx-mower-gateway `725a2ce`: 69 edges, 47 not in the manifest, 6 upward).

## 7. Requirements and decision records

Every subsystem, layer and component in the manifest exists because of a decision, and every decision serves a requirement. Both live next to the manifest.

**Requirements are the source of truth.** Code, documentation, issues and decision records reference requirement IDs; a requirement never points at them. A new feature starts with its requirement, and its issue, code and documentation cite the ID. A requirement may name an outside specification it relies on (an interface contract, a standard) the way it would name a standard, but not the project's own code or pages.


| File | Format |
|---|---|
| `arch/requirements.md` | Tables with the columns `ID \| Title \| Requirement`, one row per requirement: its ID in the first cell: `F-REQ-nnn` for a functional requirement (what the system does) or `NF-REQ-nnn` for a non-functional one (how well it does it, and the limits it fits in), a short title, and what is required and why (the outcome, not how it is built). `##` headings may group the tables by area |
| `arch/decisions/DEC-nnn-slug.md` | One file per decision. First heading `# DEC-nnn Title`, then the sections `## Context` (the problem), `## Decision` (what was chosen), `## Alternatives` (what else was considered and why not) and `## Requirements` (the `REQ-nnn` IDs it serves), and optionally `## Rules` (the `RULE-nnn` IDs it applies, §8) |

The manifest cites them: `decisions` on each subsystem, layer and component, and optional `requirements` on a component.

Check:

```
python plugin/tools/check_records.py --project <project root>
```

Exit 0 when the records back the manifest, 1 with one error per line. It refuses an invalid manifest (§4) and reports:

- a subsystem, layer or component that cites no decision;
- a cited `DEC-nnn` with no record, or a requirement ID not in `requirements.md`;
- a record that misses a section, cites no requirement in its Requirements section, or cites one that does not exist;
- a requirement that no record's Requirements section cites, so nothing in the design serves it;
- a rule ID in a Rules section that is not in the catalog;
- a record whose file name is not `DEC-nnn-slug.md` or whose first heading does not match it, and an ID used twice.

The gateway example has no records: it is not a reviewed design, and the pilot (rmx-lt/rmx-mower-gateway#120) writes the first real ones.

## 8. Rule catalog

`plugin/rules/rules.yaml` holds the architecture rules, each with an ID (`RULE-nnn`), an area, the rule, its rationale, `checked_by` (the tool that enforces it, or `review` when a person or agent must judge it) and, where public, Espressif links in `see`. Decision records cite the rules they apply (§7).

| Area | Rules | Enforced by a tool |
|---|---|---|
| dependencies | 001 layers point down, 002 no cycles, 003 one ESP-IDF component per component, 004 REQUIRES/PRIV_REQUIRES match the design, 005 main lists its requirements, 006 includes only from dependencies | 001–004, 006 (validator, checker); 005 by review |
| hardware | 010 bus driver apart from device drivers, 011 one driver per shared bus and a recorded sharing decision, 012 drivers as adapters with a uniform interface, 013 components named for the role, not the chip | 011 is flagged amber in the diagrams; the rest by review |
| interfaces | 020 private state, 021 public headers are the interface, 022 a component initializes what it depends on, 023 small interfaces, 024 application logic testable on a host | review |
| structure | 030 subsystems and levelled diagrams, 031 subsystems bundle what is used together, 032 combine or split by use, 033 shared resources have an owner | 030 (validator, generator), 033 amber in diagrams; 031 is planned as a check ([#15](https://github.com/jRmx0/esp-architecture/issues/15)) |
| concurrency | 040 short interrupt handlers that hand work to tasks, 041 interrupts only when timing needs them, 042 shared data protected, 043 priorities follow importance | review |

Rules come from published embedded-systems design guidance and the ESP-IDF documentation; the exact sources are in the maintainers' local map (§3).
