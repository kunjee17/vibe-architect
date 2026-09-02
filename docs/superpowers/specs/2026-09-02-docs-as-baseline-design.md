# Docs as the pipeline baseline — design

**Date**: 2026-09-02
**Status**: approved, not implemented
**Supersedes**: the Stage 0 rule-lookup decided earlier the same day in `docs/decisions.md`

---

## Problem

`ship` needs project rules — placement, build gate, schema topology — and carries none by
design. The lookup order shipped in v0.1.0 was: a `*-rules` skill, then `CLAUDE.md`, then
ask. Measurement afterwards showed the fallback does not work.

**No `CLAUDE.md` in any of the three repos contains a placement table.** Two of them say so
outright:

> "This file is orientation and traps only; it deliberately does not restate what `kl-ship`
> holds." — k_lawyer

k_lawyer's also defers the migration commands to the skill. So a `ship` run there reaches
Stage 2.2 with nothing to fill Placement from, and the failure mode is inventing a path —
precisely what the stage exists to prevent.

Two further problems, neither fixed by a better fallback:

1. **Part A is not skill-shaped.** Read it: an apps table, code placement, database
   topology, background jobs, testing conventions, commands. That is `architecture.md` and
   `tech.md` wearing a skill's clothes. It lives in a skill for one reason — skills
   auto-load — and that is likely why three copies drifted. A doc changes in a reviewed PR
   diff. A skill file does not.

2. **`ship` reads and writes different artifacts.** Stage 5 (Learn) writes to project docs.
   Stage 0 read a rules skill. Read from one place, write to another, and drift is
   guaranteed — the same failure this repo exists to remove, one level up.

Counter-evidence for docs, from the field: pi_dx carries 131 doc files and its docs have
repeatedly caught misdirected agents. `pi-ship`'s review gate already does selective doc
loading by change shape. The mechanism is proven; it was just never the baseline.

---

## Decisions

| # | Decision |
|---|---|
| 1 | Routing is generated from `governs:` frontmatter on each doc, never hand-maintained |
| 2 | `ship`/`auto` **hard block** when no manifest exists — no degraded run |
| 3 | `doc-scaffold` derives what is derivable from the source tree, interviews only for intent |
| 4 | A change contradicting a governing doc is a **FAIL**; a gap is a **note** |
| 5 | Refresh is a separate `doc-refresh` skill sharing one derivation core |
| 6 | Detectors are **data, not code**, and nothing is required |

### Why hard block (2)

The same reasoning that turned TDD from a rule into a gate. A degraded mode is the status
quo, and the status quo measurably fails: no `CLAUDE.md` here has a placement table, so a
warned-but-continuing `ship` still guesses. A precondition that can be skipped is a
preference.

Consequence, accepted: all three repos need `doc-scaffold` before their first `/ship`.

### Why contradiction FAILs but a gap does not (4)

The manifest declares its docs authoritative and `ship` refuses to run without them. An
authoritative doc that is *wrong* actively misdirects — worse than an advisory one that is
wrong, and the exact failure docs are supposed to prevent.

But making every new file a doc edit is the tax that stops people writing docs at all. So
the split is by kind, not by severity:

- The change makes a governing doc's claim **false** → FAIL. Fix the doc or the code, same
  commit.
- The change does something the doc **does not mention yet** → note, non-blocking.

This replaces the inherited "stale docs are never a FAIL", which was correct only while docs
were advisory.

---

## The `governs:` contract

Each doc declares what it rules. The routing rule lives next to the doc it describes, so
moving or deleting a doc updates routing without a second edit.

```markdown
---
governs:
  paths: [libs/domain/**, libs/actors/**]
  shapes: [event-schema, actor]
---

# Architecture
```

- `paths` — globs, matched against the change's touched files
- `shapes` — free-form tags a plan can name when the change is not path-shaped

`bin/build-manifest.py` walks `docs/`, reads frontmatter, emits `docs/MANIFEST.md` between
`BEGIN GENERATED` / `END GENERATED` markers. `--check` exits non-zero on drift and belongs
in the project's build gate.

**A doc with no `governs:` block is not authoritative** and never routes. That is the escape
hatch for narrative docs — a vision statement, a business one-pager — which should not bind
a code change.

### Cost, stated

Stage 0 reads only the manifest, which is tens of lines. Individual docs are pulled per
stage, per issue, by what the manifest routes to. Reading pi_dx's 73,792 doc lines per issue
is not the mechanism and never could be.

---

## Stage 0, rewritten

```
0.1  Preflight — gh, git, superpowers, graph tools        (unchanged)
0.2  Read docs/MANIFEST.md
       absent  -> STOP. "No docs manifest. Run /doc-scaffold first."
       stale   -> STOP. "Manifest drifted. Run bin/build-manifest.py."
0.3  Route: touched paths + change shape -> governing docs
0.4  Read the routed docs, plus decisions.md always
```

`CLAUDE.md` keeps its current job — orientation and traps, loaded every session anyway. It
is no longer expected to carry rules, which is what it already says about itself.

The `*-rules` skill from the v0.1.0 decision **is dropped**. It was a second artifact class
holding doc-shaped content, and the migration is simpler without it: Part A moves into
`docs/`, and the legacy skill is deleted outright rather than renamed.

---

## `doc-scaffold`

Runs **once per repo**. Bootstraps `docs/` to the point where `ship` will run.

### Derive, then ask

Derived — never asked, because a script cannot hallucinate a build command:

- separately-buildable units
- actual directory layout
- gate commands (test / lint / typecheck / build)
- pre-commit automation
- where dependencies are declared
- whether specs and plans are tracked (see below)

Asked — because it cannot be read off the tree:

- why does this unit exist, in one sentence
- **what will the code teach an agent wrong?** (the traps section; highest value per question)
- what was considered and deliberately rejected
- what is deliberately deferred

Anything underived and unasked is written as **"not recorded"**, never as a plausible
reconstruction. A confident wrong claim in an authoritative doc is the worst output this
skill can produce.

### The docs tree is offered, not imposed

Required core, because the manifest and `ship` depend on them:

- `docs/decisions.md` — the ADR log
- `docs/architecture.md` — carries the placement table. The name is fixed, because Stage 0
  needs a required doc it can demand by path when routing has not been established yet.

Everything else is **offered from what was detected**, never scaffolded by default:

| Detected | Offered |
|---|---|
| more than one buildable unit | `docs/<units>/<name>.md` |
| deploy or infra config | `docs/ops/` |
| a public-facing surface | `docs/design.md` |

pi_dx's full layout — including `business/` — is one repo's structure and is not the
template.

### Specs and plans: tracked or ignored

Derive first. Read `.gitignore` and `git ls-files docs/superpowers`; if the repo has a
practice, follow it.

Observed default across k_lawyer, pi_dx and nyayvaani (195 tracked files, 3/3 consistent):

- `docs/superpowers/` — specs and plans — **tracked.** They are decision records; they
  explain why the code looks the way it does.
- `.superpowers/` — orchestration scratch — **ignored.**

Ask only on a repo with no established answer, and ask the question that actually varies:
whether the repo is public and the plans discuss unreleased work.

---

## `doc-refresh`

Runs **on a schedule** (`/loop`, `/schedule`, or by hand). Docs exist; the job is keeping
them true and getting what was learned written down.

1. Re-derive facts from the source tree.
2. Diff against what the docs claim. Report **contradictions first** — these are why the
   skill exists.
3. Regenerate the manifest; report routing that now points nowhere.
4. Ask about direction: what changed in intent since the last run, what decision was made
   that is not in `decisions.md`, what is now deferred or abandoned.
5. Propose edits. **Never write unattended** — the same user-triggered constraint as Stage 5.

Separate from `doc-scaffold` because the triggers are unrelated and each needs a clean
"Use when" description. A two-job skill drifts into summarizing its own workflow in the
description, which is the documented failure that makes agents skip the body.

---

## Derivation: questions are the interface, detectors are data

This repo is public. A script hardcoding one contributor's stack both reveals that stack and
imposes it on everyone who installs the plugin. So the script implements **stack-agnostic
questions**, and the stack knowledge lives in a data file.

Questions (fixed, universal):

1. What are the separately-buildable units?
2. What is the directory layout? *(pure filesystem — needs no detector)*
3. What commands verify a change?
4. What runs automatically before a commit?
5. Where are dependencies declared?

Detectors (data, extensible, none required):

```toml
[[detector]]
question = "pre-commit-automation"
when     = ".husky/"
extract  = "files"

[[detector]]
question = "pre-commit-automation"
when     = ".pre-commit-config.yaml"
extract  = "repos[].hooks[].id"
```

Shipped coverage aims at mainstream OSS tooling — npm/pnpm/yarn/bun, cargo, uv/pip/poetry,
go, gradle/maven, make, just, task; hooks via husky/lefthook/pre-commit/`.git/hooks`. No
ecosystem is privileged and none is a precondition.

**Three rules that make this safe:**

- **A detector extracts only what it can quote literally from a file.** It never infers. If
  it cannot quote its source, it reports nothing.
- **A miss is reported, not guessed.** Unmatched questions fall through to the interview,
  labelled underived.
- **Zero matches still works.** A repo the table has never seen scaffolds fine, entirely by
  interview.

A wrong detector produces a confidently wrong fact, which is worse than a miss — hence the
quote-or-nothing rule.

---

## Roadmap consequence

`doc-scaffold` becomes a **dependency of `ship` Stage 0**, not the cheap afterthought in
Group C. Revised order:

```
C (doc-scaffold + manifest)  ->  A migration  ->  B (doc-refresh, adr-compact)
```

`ship`, `auto` and `clean` are already written and unaffected apart from Stage 0 and the
Verify doc rule.

Per-repo migration, one at a time, k_lawyer first:

1. `/doc-scaffold` — derive, interview, generate the tree and manifest
2. Move Part A out of the legacy `*-ship` skill into the docs it was always shaped for
3. Delete the legacy skill (`*-clean` too — `clean` replaces it)
4. Point `CLAUDE.md`'s skill table at the plugin
5. First real `/ship` run

---

## Implementation splits into two plans

This spec spans two roadmap groups and must not become one plan:

| Plan | Contains | Group |
|---|---|---|
| 1 | `governs:` frontmatter, `build-manifest.py`, detector table, `doc-scaffold`, `ship` Stage 0 rewrite, Verify's contradiction rule | C + A |
| 2 | `doc-refresh` | B |

Plan 1 is the whole critical path — nothing ships through the pipeline until it lands. Plan 2
depends on Plan 1's derivation core existing and benefits from watching Plan 1 run on a real
repo first.

## Out of scope

- `adr-compact` — unchanged, still Group B
- `ship`'s other stages
- Automatic doc writing. Both new skills propose; the human approves. Stage 5's
  user-triggered constraint holds throughout.

---

## Open questions

1. **Manifest granularity.** Per-doc routing may be too coarse for a 1,000-line
   architecture doc where only one section governs the change. Sections are not addressable
   in the current design. Deferred until it hurts.
2. **`shapes` vocabulary.** Free-form tags are flexible and will drift. Whether a controlled
   list is worth the rigidity is unknown until two repos have used it.
3. **Detector table format.** TOML assumed for readability; not validated against real
   parsing needs.
4. **How reliably a contradiction can be detected.** It gates a commit, so a false positive
   blocks real work. Decision 4 stands — contradiction FAILs — and the lever if false
   positives appear is **narrowing what counts as a contradiction**, not downgrading it to a
   note. A doc claim must be specific enough to be falsifiable ("only `CommandActor`
   appends") before it can contradict anything; vague prose ("keep actors clean") is a gap
   at worst. Needs measurement on real diffs.
