---
governs:
  shapes: [product]
  verify: ask
---

# Product

## Why this exists, and who for

Nine skills across three repos had drifted into three copies of the same pipeline. The
workflow half was structurally identical; the rules half was portable to nothing. This repo
extracts the portable half.

**First client: the author's own repos** — k_lawyer, pi_dx, nyayvaani — which use the skills
these were derived from on a daily basis. That is the real bar: it has to be at least as good
as what it replaces, in daily use, before those local copies are deleted.

**Second, hopefully, anyone else.** The repo is public either way. That is why detectors are
data rather than one contributor's stack, why skill bodies name MCP tools and CLI commands
instead of one harness's built-ins, and why the plugin also ships Codex, Cursor and Gemini
manifests.

## What is out of scope

- **`srs` — a Software Requirement Specification skill.** `superpowers:brainstorming` already
  asks questions until an architecture is settled, then writes a spec. A wrapper at most.
- **A standalone Learn skill.** Learn *is* the docs — `decisions.md` and the rest, kept
  current. `doc-refresh` maintains them; nothing separate is needed.

## What is deliberately deferred

- **`doc-refresh`** — Plan 2. Depends on Plan 1's derivation core and benefits from watching
  it run first.
- **`adr-compact`** — the decision logs across the three source repos total ~10,700 lines in
  an identical format. Independent of the routing work; can jump the queue if it hurts first.
- **Proving `ship` end to end.** No real issue has gone from `/ship <n>` to a merged PR yet.
- **A pressure scenario for `ship`.** `doc-scaffold` has RED and GREEN evidence in
  `tests/scenarios/`; `ship` has none, and its TDD gate is the repo's central claim.

## Not recorded

- Whether anyone outside the author's repos has installed this.
- Whether the Codex, Cursor and Gemini manifests work; they were written from superpowers'
  shapes and never installed on those runtimes.
