# vibe-architect

Portable Claude Code skills for the issue-to-PR pipeline, extracted from the per-project
`kl-ship` / `pi-ship` / `nv-ship` skills that had drifted into three copies of the same thing.

**Status: v0.1.0 — the ship pipeline is written, not yet proven.** `ship`, `auto` and
`clean` exist, plus four graph-navigation helpers. Nothing has shipped a real issue through
them yet, and the local `*-ship` skills are still untouched.

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
| `superpowers` plugin | **Hard** | These skills compose it rather than reimplement it. Not bundled and not auto-installable — plugin manifests have no dependency field. `ship` checks for it in Stage 0 and tells you which stages degrade without it. Install: `claude plugin install superpowers@claude-plugins-official` |
| code-review-graph MCP | **Soft** | Structural navigation. Without it, `ship` Stage 1.3 falls back to symbol tools, then grep. The four helper skills need it outright. |

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

## Skills

| Skill | Status | Replaces |
|---|---|---|
| `ship` | **written** | Part B of `kl-ship` / `pi-ship` / `nv-ship` |
| `auto` | **written** | `pi-auto`, `nv-auto` — selection only |
| `clean` | **written** | `kl-clean`, `pi-clean`, `nv-clean` |
| `explore-codebase` | **written** | identical copies in pi_dx + k_lawyer |
| `debug-issue` | **written** | identical copies in pi_dx + k_lawyer |
| `review-changes` | **written** | identical copies in pi_dx + k_lawyer |
| `refactor-safely` | **written** | identical copies in pi_dx + k_lawyer |
| `adr-compact` | planned | nothing — new |
| `doc-scaffold` | planned | nothing — new |

The four helpers were found during extraction, not in the original survey: they are
byte-identical between pi_dx and k_lawyer apart from a five-line token-efficiency block.

## Where project rules come from

`ship` carries no project rules. Stage 0 loads them from the repo you are standing in,
taking the first that exists:

1. `.claude/skills/*-rules/SKILL.md` — a rules-only project skill
2. `CLAUDE.md` / `AGENTS.md` at the repo root, plus nested ones for touched directories
3. Neither → stop and ask

So migration is: rename `kl-ship` → `kl-rules`, delete its Part B, keep Part A. Until then
the `CLAUDE.md` fallback means `ship` works in every repo today with no changes.

## Other runtimes

The skill bodies name MCP tools and CLI commands, never a specific harness's built-ins, so
they port. Manifests ship for Claude Code (`.claude-plugin/`), Codex (`.codex-plugin/`),
Cursor (`.cursor-plugin/`) and Gemini CLI (`gemini-extension.json`) — all pointing at the
same `skills/` directory. Codex, Copilot CLI and Gemini CLI also read `~/.agents/skills/`,
so a symlink works without any plugin system at all.

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
