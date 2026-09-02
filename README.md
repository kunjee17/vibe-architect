# vibe-architect

Portable Claude Code skills for the issue-to-PR pipeline, extracted from the per-project
`kl-ship` / `pi-ship` / `nv-ship` skills that had drifted into three copies of the same thing.

**Status: design only.** Nothing is implemented. The docs in `docs/` are the first cut;
no skill has been written yet.

## Why this exists

Nine skills across three repos, in three families:

| Family | k_lawyer | pi_dx | nyayvaani | What it does |
|---|---|---|---|---|
| `*-ship` | 443 ln | 357 ln | 380 ln | Part A rules + Part B workflow |
| `*-auto` | — | 114 ln | 63 ln | pick an issue, hand to ship |
| `*-clean` | 97 ln | 88 ln | 95 ln | post-merge cleanup |

The **Part B halves are 201 / 147 / 131 lines and structurally identical** — fetch issue →
refresh graph → explore → branch → plan → implement → review → commit → PR. The Part A
halves share almost nothing: placement rules, database topology, per-repo traps. The three
`*-clean` skills are within 9 lines of each other.

So the workflow is portable and the rules are not. That seam is what this repo extracts.

Two further gaps, measured rather than assumed:

- **TDD is a manual rule.** `superpowers:test-driven-development` has been invoked **0 times**
  across the last 33 sessions in k_lawyer. The rule is real; the enforcement is memory.
- **Nothing gets written down.** There is no step that turns a shipped PR into a durable rule.
  Small conventions — *run humanizer on frontend content* — live in one person's head.

## Install

```bash
claude plugin marketplace add kunjee17/vibe-architect
claude plugin install vibe-architect@vibe-architect
```

## Prerequisites

| Dependency | Required? | Notes |
|---|---|---|
| `gh` | **Hard** | Issue fetch, PR creation. Must be authenticated. |
| `git` | **Hard** | |
| `obsidian` CLI | **Soft** | `~/.local/bin/obsidian`. Adds graph queries to the second-brain vault but **requires the Obsidian app to be running**. Never architect around it — plain `Grep`/`Read` over `~/Workspace/secondbrain/` works headless and in cron. Not `obs`, which is OBS Studio. |
| `superpowers` plugin | **Hard** | These skills compose it rather than reimplement it. |

## `/goal` must be typed by you

`/goal` is a built-in slash command that installs a session-scoped Stop hook. **A skill
cannot trigger it** — there is no tool for setting a goal, and a skill is injected
instructions, not typed input.

So the "work the whole milestone" mode is not built here. You type it:

```
/goal every open issue in milestone X is merged, or stop after 20 turns
```

`claude -p "/goal <condition>"` works non-interactively if you want it from a script, but
that starts a nested session — noted, not built on in v1.

| Want | Mechanism |
|---|---|
| ship one named issue | `/ship <n>` |
| pick an easy one, then ship | `/auto` → `/ship` |
| chew the whole milestone | `/goal` — built-in, condition-driven |
| nightly / interval | `/loop`, `/schedule` — time-driven |

## Planned skills

| Skill | Status | Replaces |
|---|---|---|
| `ship` | planned | Part B of `kl-ship` / `pi-ship` / `nv-ship` |
| `auto` | planned | `pi-auto`, `nv-auto` — selection only |
| `clean` | planned | `kl-clean`, `pi-clean`, `nv-clean` |
| `adr-compact` | planned | nothing — new |
| `doc-scaffold` | planned | nothing — new |

Not built, deliberately — see `docs/decisions.md`:

- **`srs`** — `superpowers:brainstorming` already does this.
- **Learn as a new skill** — extends the existing `second-brain` skill instead.

## Docs

- [`docs/design.md`](docs/design.md) — the three layers, the pipeline, how it composes superpowers
- [`docs/decisions.md`](docs/decisions.md) — what was decided and why
- [`docs/roadmap.md`](docs/roadmap.md) — three sub-projects and their order

## Migration

Local `kl-ship` / `pi-ship` / `nv-ship` stay **untouched** until `ship` proves out in real
use. Then they are deleted one repo at a time, leaving only their Part A rules behind.
