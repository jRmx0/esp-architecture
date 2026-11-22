# esp-architecture

A Claude Code plugin that makes the architecture of an ESP-IDF project code that agents cannot quietly break. A project describes its layers, components and allowed dependencies in `arch/architecture.yaml`; the ESP-IDF build and a blocking checker enforce it, every decision is backed by requirements and sourced rules, and diagrams (context, block, organigram, layering) are generated from the same file.

Scope: architecture only, ESP-IDF framework only (PlatformIO `framework = espidf` or `idf.py`). It is meant for existing projects too: discover, gather requirements, design, then refactor to the design.

Status: early. The plugin installs and ships the manifest schema, its validator and the checker; no skills, hooks or diagrams yet; the plan is [epic #1](https://github.com/jRmx0/esp-architecture/issues/1).

Documentation: [wiki/Home.md](wiki/Home.md).

## Install

In Claude Code:

```
/plugin install esp-architecture --marketplace jRmx0/esp-architecture
```

From a local clone: `/plugin marketplace add <path to clone>`, then `/plugin install esp-architecture@esp-architecture`.

## License

Apache-2.0, see [LICENSE](LICENSE).
