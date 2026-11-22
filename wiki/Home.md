# esp-architecture: architecture as code for ESP-IDF projects

What the [esp-architecture](https://github.com/jRmx0/esp-architecture) plugin is and how it is used. The plan and open work are in [epic #1](https://github.com/jRmx0/esp-architecture/issues/1).

## 1. Purpose

AI agents that write ESP-IDF firmware tend to ignore architecture. The plugin makes the architecture a file the build and a checker enforce, so a violation blocks the agent instead of being a review comment.

## 2. Current state

The repo holds the plugin and marketplace manifests only. It installs in Claude Code and has no skills, hooks or checker yet.

## 3. Rule sources

Rules are public, in our own words, each with an ID and a rationale. Where a rule comes from (book, page, context) is kept only in each maintainer's local `sources.local.yaml`, which git ignores, so no copyrighted text or citation is published. Espressif documentation is cited openly.
