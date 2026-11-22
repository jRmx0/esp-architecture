# esp-architecture — notes for agents

Goal and plan: [epic #1](https://github.com/jRmx0/esp-architecture/issues/1). Work is issues in this repo (labels `epic`, `enhancement`, `bug`, ...; no project board).

## Where things live

- Knowledge (how it works, decisions, how-tos): pages in `wiki/`, changed only by PR, current state only. Not the GitHub wiki.
- Repo markdown otherwise: this file and a short README.
- Branches: `feat/<issue#>-slug` → PR → `development` (default). Every PR closes at least one open issue.
- Reusable ESP-IDF facts learned here go to the esp-knowledge hub, not this repo.

## Scope

- Architecture only: layers, components, dependencies, interfaces, tasks, decisions, diagrams. Not coding style, power or timing.
- ESP-IDF framework only (PlatformIO `framework = espidf` or `idf.py`).
- The pilot project is rmx-lt/rmx-mower-gateway ([rmx-lt/rmx-mower-gateway#120](https://github.com/rmx-lt/rmx-mower-gateway/issues/120)): prove each feature on it.

## Rules

- This repo is public. Rules are written in our own words with an ID and a rationale. Never commit text, quotes, figures or citations (title, chapter, page) from the books or other copyrighted sources they come from.
- Each rule's source and context go only in the gitignored `sources.local.yaml` (rule ID → source, location, context). Never `git add -f` it.
- Public sources (Espressif docs URLs) may be cited in the repo.
- Every rule must have a source: no rules from assumption.
- Before a PR that changes `plugin/rules/rules.yaml`, run `python tools/check_sources.py` (needs your local `sources.local.yaml`).
- The shipped plugin is `plugin/` (skills, hooks, tools go there); the repo root holds the marketplace, docs and dev files. Validate before a PR: `claude plugin validate --strict plugin` and `claude plugin validate --strict .claude-plugin/marketplace.json`.
