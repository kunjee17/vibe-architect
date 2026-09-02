# Design

## Three layers

The per-project ship skills conflated three things that change at different rates.

| Layer | Changes | Lives in | Example |
|---|---|---|---|
| **Personal** | Almost never | This repo | Never worktrees. TDD first. Human gate before merge. |
| **Workflow** | Rarely | This repo | Investigate → Build → Verify → Deploy → Learn |
| **Project** | Constantly | The repo it describes | saas-next has three Turso DBs; firm-next has one Supabase |

Only the first two are portable. Project rules stay where they are — this repo never tries
to own them.

## The five stages

Stage names borrowed from Faktorial's delivery loop, which is a better vocabulary than the
ad-hoc step lists in the current skills. Four of the five already exist in some form.

| Stage | Today | Here |
|---|---|---|
| **Investigate** | fetch issue → refresh graph → explore | unchanged |
| **Build** | branch → plan → implement | **tests first, as a gate** |
| **Verify** | review gate, pre-commit `test && build` | compose `requesting-code-review` + `verification-before-completion` |
| **Deploy** | commit → PR → clean | **stops before merge** |
| **Learn** | *nothing* | writes to second-brain / project docs |

## `ship`

```
/ship <issue-number>
```

1. **Investigate** — fetch the issue, refresh the code graph, explore before planning
2. **Build** — branch, plan, then implement **test-first**
3. **Verify** — review gate; evidence before any completion claim
4. **Deploy** — commit, open the PR, **stop**
5. → hand back

`ship` **never merges.** It stops at the PR. The human does critical-path testing by hand,
and merge is a separate decision. When nothing comes back from review: merge, then `/clean`.

### Non-negotiables

- **Tests before implementation.** Not a suggestion; the Build stage does not proceed without them.
- **Never worktrees.** Already a promoted cross-project lesson (`atman/no-git-worktrees` in the
  second-brain vault). `superpowers:using-git-worktrees` is explicitly disabled.
- **Never auto-merge.** The human gate is the point.
- **Evidence before assertions.** No "it works" without the command output in the transcript.

### Composition, not reimplementation

`ship` calls superpowers skills rather than restating them:

| Stage | Skill |
|---|---|
| Build | `superpowers:test-driven-development` |
| Verify | `superpowers:requesting-code-review` |
| Verify | `superpowers:verification-before-completion` |
| Deploy | `superpowers:finishing-a-development-branch` |
| on any bug | `superpowers:systematic-debugging` |
| never | `superpowers:using-git-worktrees` |

These four are currently invoked **0 times** in 33 sessions. The pipeline is where they get
triggered, since relying on a rule in CLAUDE.md demonstrably has not worked.

## `auto`

Selection only. It picks an issue and hands to `ship`.

```
/auto                  # lowest-complexity open unassigned issue
/auto --milestone X    # from a milestone
/auto --quick          # no blockers, small, fast
```

It does **not** loop. Repetition is `/goal`, which is built in and condition-driven — it
stops when the queue is empty, where `/loop` would keep firing.

## `clean`

Post-merge: verify the branch is merged, pull, delete the local branch, prune refs. Derived
from the three existing copies, which are within 9 lines of each other.

## `adr-compact`

`docs/decisions.md` grows without bound:

```
pi_dx      5,010 lines  (99 entries) + 1,691 archived   ← already compressed once by hand
k_lawyer   2,603 lines
nyayvaani  1,412 lines
          ~10,700 lines
```

Same format everywhere: `## Title — YYYY-MM-DD`, then **Decision** / **Context**. Compaction
moves superseded entries to `decisions-archive.md`, preserving dates and cross-links. Never
deletes — a reversed decision is a fact worth keeping.

## `doc-scaffold`

pi_dx has the template; the other repos have fragments of it.

```
docs/architecture.md  design.md  tech.md  roadmap.md  deployment.md  decisions.md
docs/apps/<app>.md      one per app, same shape        (pi_dx: 9)
docs/ops/<runbook>.md   deploy, restore, release       (pi_dx: 7)
docs/business/          api-spec, brand, pricing       (pi_dx: 5)
```

All three repos have `decisions.md`. Neither k_lawyer nor nyayvaani has the `apps/` + `ops/`
split. The pattern exists and has not propagated.

## Learn

The stage nothing currently does. Two destinations, and the routing matters:

| Kind | Goes to |
|---|---|
| Outlives the repo — framework, language, architecture | `~/Workspace/secondbrain/` via `second-brain` |
| Specific to one repo — *run humanizer on frontend content* | that repo's docs / CLAUDE.md |

**Explicitly user-triggered, never automatic.** This was a direct requirement.

Extends the existing `second-brain` skill rather than duplicating it. That vault already
holds promoted lessons, so the loop is half-built.
