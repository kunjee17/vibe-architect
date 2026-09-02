# vibe-architect — Decisions

Format: `## Title — YYYY-MM-DD`, then **Decision** / **Context**.

## Build the pipeline, do not buy Faktorial — 2026-08-24

**Decision**: build these skills rather than adopt [faktorial.ai](https://faktorial.ai/).

**Context**: Faktorial is an autonomous delivery platform (Asynkron, the Proto.Actor team).
GitHub stays source of truth; it dispatches Claude Code / Codex / Copilot under controlled
parameters, one isolated branch per issue. Five stages: Investigate → Build (tests first) →
Verify → Deploy → Learn.

Four of those five already exist in the `*-ship` skills. The missing one is Learn.

Three reasons not to buy:

1. **The requirement contradicts the product.** Its value proposition is autonomy — issues to
   merged PRs without a human in the loop. The requirement here is explicitly *"NOT automatic
   but me triggered"*. On the one stage that is missing, the two want opposite things.
2. **The managed option is disqualified.** Legal Desk AI is positioned as privacy-first for
   legal professionals. A third party operating the pipeline means their infrastructure
   touching a codebase handling advocate and client data. Self-managed avoids that, but then
   it is orchestration around agents that are already orchestrated.
3. **Throughput is not the bottleneck.** Faktorial targets teams with backlogs and no headcount.
   This is one person whose loop works — 15 `kl-ship` runs, 11 `kl-clean` in 33 sessions. What
   leaks is that nothing learned gets written down. More agents produce unwritten lessons faster.

Assessment is from the landing page only — marketing copy, no pricing disclosed, nothing
independently verified. Revisit on hiring, or if the backlog outgrows one driver.

**Kept**: the five-stage vocabulary. It is better than the ad-hoc step lists.

## The workflow goes global; project rules stay local — 2026-08-24

**Decision**: this repo owns the personal and workflow layers. Project rules stay in the repo
they describe.

**Context**: the `*-ship` skills are two halves. Part B (the workflow) is 201 / 147 / 131 lines
and structurally identical across three repos. Part A is placement rules, database topology and
per-repo traps — portable to nothing. Extracting only Part B is the natural seam.

Where Part A ends up after migration is **deferred**, not decided. Candidates: a rules-only
per-project skill, the repo's CLAUDE.md, or a plain data file the global skill reads.

## Local ship skills stay untouched until `ship` proves out — 2026-08-24

**Decision**: `kl-ship`, `pi-ship`, `nv-ship` are frozen. Delete them one repo at a time, only
after the global `ship` has been used for real work.

**Context**: accepts temporary duplication — the workflow will exist in two places and can
drift. That is the cheaper risk. Rewriting three working pipelines against an unproven skill
is not.

## `/goal` is user-typed; `auto` does selection only — 2026-08-24

**Decision**: no looping construct is built. `auto` selects an issue and hands to `ship`.
Repetition is `/goal`, typed by the user, documented in the README.

**Context**: `/goal` is a built-in slash command wrapping a session-scoped Stop hook. A small
fast model evaluates the condition after every turn. **A skill cannot trigger it** — there is
no tool for setting a goal, and a skill is injected instructions, not typed input.

The docs name this exact use case: *"Working through a labeled issue backlog until the queue
is empty."* Condition-driven is correct here; `/loop` is time-driven and would keep firing
after the queue empties.

`claude -p "/goal <condition>"` works non-interactively but starts a nested session. Noted,
not built on in v1.

## `srs` is not built — brainstorming already does it — 2026-08-24

**Decision**: do not write an `srs` skill.

**Context**: the requirement was "asks questions and discusses until the whole project
architecture is set up". `superpowers:brainstorming` on its architectural path already does
exactly that: questions one at a time, 2–3 approaches with trade-offs, a sectioned design with
approval per section, then it writes a spec and hands to `writing-plans`. This document set was
produced that way.

If it needs personal conventions layered on, that is a thin wrapper — not a new skill.

## Learn extends second-brain; routing is by scope — 2026-08-24

**Decision**: Learn writes cross-repo lessons to `~/Workspace/secondbrain/` via the existing
`second-brain` skill, and repo-specific conventions to that repo's own docs. User-triggered
only.

**Context**: the vault is explicitly cross-project. A rule like *run humanizer on frontend
content* is k_lawyer-specific and would pollute it. The vault README already lists
`atman/no-git-worktrees` as a promoted lesson, so the loop is half-built — this connects it to
the pipeline rather than starting over.

## The obsidian CLI is a soft dependency — 2026-08-24

**Decision**: `gh` is a hard requirement. The `obsidian` CLI is an accelerator only, with
`Grep`/`Read` as the always-available path.

**Context**: the CLI is at `~/.local/bin/obsidian` and **requires the Obsidian app to be
running**. The existing `second-brain` skill already states the rule: *"Treat it as an
accelerator; never architect around it."* Plain file access works headless and in cron.

Note: `/usr/bin/obs` is OBS Studio, not Obsidian. Different binary.

## TDD becomes a gate, not a rule — 2026-08-24

**Decision**: the Build stage does not proceed without tests. Enforced by the pipeline, not by
a line in CLAUDE.md.

**Context**: measured over the last 33 sessions in k_lawyer — 7,490 tool calls, 86 skill
invocations. `superpowers:test-driven-development` was invoked **0 times**. So were
`verification-before-completion`, `requesting-code-review`, `receiving-code-review` and
`finishing-a-development-branch`.

Of 34 superpowers invocations, 25 were `brainstorming` + `writing-plans`. The front half of the
workflow fires reliably; the back half never does. A rule stating the intention has already
been tried and has not worked — hence a gate.

## Never worktrees — 2026-08-24

**Decision**: `superpowers:using-git-worktrees` is explicitly disabled in the pipeline.

**Context**: personal constraint, already promoted to the second-brain vault as
`atman/no-git-worktrees`. Recorded here so the pipeline enforces it rather than relying on the
vault being read first.

## Project rules load by lookup order, not by a fixed home — 2026-09-02

**Decision**: `ship` Stage 0 loads project rules from the first of: a `*-rules` skill in
`.claude/skills/`, then the repo's `CLAUDE.md`/`AGENTS.md`, then stop and ask.

**Context**: this was the open question deferred in `roadmap.md` — where Part A lands after
migration. It could not stay deferred: a global `ship` needs *some* contract for finding
placement tables, database topology and build commands on day one.

A lookup order settles it without forcing a migration. The `CLAUDE.md` fallback means `ship`
runs in every repo today with zero changes. When a repo is ready, `kl-ship` becomes
`kl-rules` — Part A kept, Part B deleted — and the first branch of the lookup picks it up.

Rejected: **CLAUDE.md only**, because it would push ~250 lines of ship-time rules into a file
that loads on every session whether or not anything is being shipped. Rejected: **a fixed
data file** (`.claude/project-rules.md`), because nothing outside `ship` would load it, so the
rules would stop applying to ordinary non-shipping work.

## Four graph helper skills fold in too — 2026-09-02

**Decision**: `explore-codebase`, `debug-issue`, `review-changes` and `refactor-safely` move
into this plugin alongside the ship pipeline.

**Context**: not in the original survey. They exist in both pi_dx and k_lawyer and are
byte-identical apart from a five-line token-efficiency block pi_dx added. They contain no
project content at all — they are code-review-graph boilerplate. Merging them was a copy plus
a frontmatter fix (the originals used `name: Explore Codebase`, with spaces and capitals,
which the skill spec does not allow).

Cost was near zero and it empties the duplicated set in both repos in one pass rather than
leaving a second migration to remember.

## superpowers stays a documented prerequisite, not a vendored copy — 2026-09-02

**Decision**: do not bundle or vendor any superpowers skill. `ship` Stage 0.1 checks for the
plugin, names the stages that degrade without it, and asks before continuing.

**Context**: Claude Code plugin manifests have **no dependency field** — checked across every
installed plugin, the accepted keys are name, description, version, author, homepage,
repository, license, keywords, commands, skills, mcpServers, userConfig. So there is no
auto-install to declare.

Copying the four composed skills in would reintroduce exactly the drift this repo exists to
remove, one level up. A loud preflight is the cheaper failure mode than silently skipping a
stage.

**Consequence**: the TDD gate is written **inline in `ship`**, not delegated. It is the one
piece that must bind even when the plugin is absent, since it is the measured gap the whole
design turns on.

## The plugin ships for Codex, Cursor and Gemini too — 2026-09-02

**Decision**: carry `.codex-plugin/`, `.cursor-plugin/` and `gemini-extension.json` beside
`.claude-plugin/`, all pointing at the same `skills/` directory.

**Context**: three extra manifests and an `AGENTS.md`. The real cost is a writing constraint,
not a packaging one: **skill bodies name MCP tools and CLI commands, never a specific
harness's built-in tools.** `gh`, `git`, `semantic_search_nodes_tool` and `find_symbol` exist
everywhere; a named Grep/Read tool does not.

Codex, Copilot CLI and Gemini CLI additionally read `~/.agents/skills/`, so a symlink is a
zero-manifest install path.

Untested on any runtime other than Claude Code. The manifests are written from the shapes
superpowers ships, not from a passing install.
