---
governs:
  paths: [skills/**, docsbase/**, bin/**, tests/**]
  shapes: [placement, build-constraints]
---

# Architecture

## Placement

Where new work goes. Derived from the tracked tree on 2026-09-02.

| What | Where |
|---|---|
| A skill — judgement, prose, no logic | `skills/<name>/SKILL.md` |
| Skill test evidence (RED/GREEN scenarios) | `tests/scenarios/<skill>-baseline.md` |
| Mechanism — deterministic and testable | `docsbase/<module>.py` |
| Data a contributor extends without touching logic | `docsbase/*.toml` |
| A CLI entry point wrapping `docsbase` | `bin/<name>.py` |
| Unit tests | `tests/test_<module>.py` |
| A design worked through before building | `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` |
| An implementation plan | `docs/superpowers/plans/YYYY-MM-DD-<topic>.md` |

**The seam is the rule: mechanism in `docsbase/`, judgement in `skills/`.** Anything a
script can decide deterministically belongs in Python and gets a test. Anything requiring
judgement belongs in a skill and gets a scenario. A skill that encodes mechanism will drift;
a script that encodes judgement will be wrong in a way tests cannot see.

## Gate commands

```bash
bin/run-tests.py          # stdlib unittest, no pytest required
claude plugin validate .  # marketplace manifest
bin/check-versions.py     # five manifests must agree
```

All three must pass before a commit. There is no CI wiring them yet — running them is manual.

## Build constraints

- **Pre-commit hook compiles:** no
- **Cold build cost:** none — no build step; the test suite runs in under a second
- **Concurrent builds safe:** yes

Derived: no `.husky/`, no `.pre-commit-config.yaml`, no non-sample `.git/hooks`, and no
compiled artefacts. Consequently `ship`'s serialisation mitigations do **not** bind here —
multiple commits on a branch are fine, and parallel implementation agents may run.
This makes vibe-architect unrepresentative of the Rust repos it was extracted for; do not
generalise its looseness to them.

## Traps

Things the code will teach you wrong, or not at all.

**The version lives in five places and nothing enforces agreement.**
`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`,
`.cursor-plugin/plugin.json`, `gemini-extension.json`. `bin/check-versions.py` exists solely
for this; `bin/check-versions.py 0.3.0` sets all five. Editing one by hand looks correct and
is not.

**`.superpowers/` is ignored, `docs/superpowers/` is tracked. This is deliberate.**
Orchestration scratch is disposable; specs and plans are decision records that explain why
the code looks the way it does. The near-identical names make it read like an inconsistency.

**Helper scripts are invoked by absolute path, and the working directory decides which repo
is read.** `bin/build-manifest.py` reads `pathlib.Path.cwd()`. A skill running in another
repo calls `${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py` while cwd stays that repo. `cd`-ing
into a clone of this repo to make a relative path resolve silently operates on *this* repo's
docs instead — this shipped as a real bug and was caught only in final review.

**The four graph-helper skills are inert without the `code-review-graph` MCP server.** They
name its tools directly. Each states the dependency and a fallback; if you add a fifth, do
the same.

**`docsbase/detectors.toml` is data, not code.** Adding an ecosystem is a data edit. A typo
in `extract` raises rather than silently matching nothing — that is deliberate, so a broken
detector fails loudly instead of leaving a question permanently underived.

**`bin/derive-facts.py` returns 4/4 underived on this repo.** Correct, not broken: there is
no `package.json`, `Cargo.toml`, `pyproject.toml` or `Justfile` here. A pure-scripts Python
repo has no detector, and the honest output is to ask.
