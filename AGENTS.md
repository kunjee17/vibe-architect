# vibe-architect — for agents working in this repo

This repository contains **skills**, not application code. Every change here is a change to
instructions another agent will follow, so a wrong line manufactures wrong behaviour rather
than merely confusing a reader.

## Before editing any SKILL.md

Read `superpowers:writing-skills`. In particular:

- `description` states **when to use** the skill — triggering conditions only. Never
  summarize the workflow there; agents follow the description instead of reading the body.
- `name` is kebab-case, letters/numbers/hyphens only, and matches the directory name.
- Discipline rules need a rationalization table and a red-flags list, not softer wording.

## Layers

| Layer | Lives where |
|---|---|
| Personal constraints, workflow | this repo |
| Project rules — placement, schemas, build commands | the repo they describe |

**This repo never encodes project-specific rules.** If a change would only be true in one
repository, it belongs in that repository's `CLAUDE.md` or its `*-rules` skill.

## Runtimes

The skills are runtime-agnostic on purpose. Manifests: `.claude-plugin/` (Claude Code),
`.codex-plugin/`, `.cursor-plugin/`, `gemini-extension.json`. All four point at the same
`skills/` directory — keep them version-synced.

Do not name a specific harness's built-in tools in a skill body. Name the MCP tools
(`semantic_search_nodes_tool`, `find_symbol`) and the CLI commands (`gh`, `git`), which
exist everywhere.

## Docs

`docs/design.md` · `docs/decisions.md` · `docs/roadmap.md`. Decisions are append-only.
