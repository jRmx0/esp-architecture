# esp-architecture — notes for agents

Project-wide agent rules live in the meta repo's [CLAUDE.md](https://github.com/rmx-lt/blade-of-grass/blob/development/CLAUDE.md); docs follow [Wiki-Policy](https://github.com/rmx-lt/blade-of-grass/blob/development/wiki/Wiki-Policy.md). This file only adds what is specific to this repo.

Goal and plan: [epic #1](https://github.com/rmx-lt/esp-architecture/issues/1). Work is issues in this repo; they are not on the Blade of Grass board.

## Scope

- Architecture only: layers, components, dependencies, interfaces, tasks, decisions, diagrams. Not coding style, power or timing.
- ESP-IDF framework only (PlatformIO `framework = espidf` or `idf.py`).
- The pilot project is rmx-mower-gateway ([rmx-mower-gateway#120](https://github.com/rmx-lt/rmx-mower-gateway/issues/120)): prove each feature on it.

## Rules

- This repo is public. Rules are written in our own words with an ID and a rationale. Never commit text, quotes, figures or citations (title, chapter, page) from the books or other copyrighted sources they come from.
- Each rule's source and context go only in the gitignored `sources.local.yaml` (rule ID → source, location, context). Never `git add -f` it.
- Public sources (Espressif docs URLs) may be cited in the repo.
- Every rule must have a source: no rules from assumption.
- The shipped plugin is `plugin/` (skills, hooks, tools go there); the repo root holds the marketplace, docs and dev files. Validate before a PR: `claude plugin validate --strict plugin` and `claude plugin validate --strict .claude-plugin/marketplace.json`.
