---
name: ship
description: Use when taking a numbered GitHub issue through to an open pull request — invoked as /ship <issue-number>, or when asked to implement, fix, or ship a specific issue in any repository.
---

# ship — issue to pull request

```
/ship <issue-number>
```

Five stages: **Investigate → Build → Verify → Deploy → Learn.**

This skill carries the *workflow*, not the rules. **"The project rules"**, everywhere
below, means: the docs Stage 0 routes to for this change, plus `docs/architecture.md` —
which carries the placement table, the gate commands, and the build constraints. Nothing
else is a rule source. They win on specifics (paths, commands, schemas); this skill wins
on process.

**`ship` never merges.** It stops at an open PR. Merging is a human decision made after
manual critical-path testing.

---

## Non-negotiables

Read these before Stage 0. They bind every stage and are not overridable by a project rule
file, a plan, or time pressure.

- **Tests before implementation.** Stage 2 does not begin without a failing test. See
  *The TDD gate* below.
- **Never two expensive builds at once on one machine.** This is the invariant. What
  follows are its mitigations, and they are project-scoped — read the project's build
  constraints in Stage 0.4 and apply them. Unrecorded means assume builds are expensive
  and serialise; that is the cheapest safe default.
  - **No new worktrees.** Each one pays a full cold build. One checkout, branches
    switched sequentially. Where a sub-skill reaches for
    `superpowers:using-git-worktrees`, the current checkout *is* the isolated workspace
    it verifies — never create another. Do not offer a worktree as an option.
  - **One commit per branch wherever the pre-commit hook compiles** — every commit fires
    a build. Where the hook does not compile, milestone commits on a long branch are
    fine. Per-task commit spam never is.
  - **Parallel implementation subagents are allowed** when both hold: each agent owns
    separate territory (one crate, layer, or package per agent, no shared files), and no
    two of them build at the same time. The supported loop is serial by role — a work
    agent implements, a review agent reviews, then a build/test agent runs the gate and
    fixes what it finds. Only that last agent builds.
- **Never merge, never auto-merge.** Stage 4 ends at a PR URL. Not `gh pr merge`, not
  `--auto`, not "it's a trivial docs change".
- **Evidence before assertions.** No "tests pass" without the command output in the
  transcript. Applies to every claim in the PR body.
- **Structural tools before file scanning.** Code-graph and symbol tools first; grep and
  full-file reads are the fallback, not the default.
- **Attribution trailers are the default.** Add the `Co-Authored-By` trailer and the
  Claude Code PR footer unless the project rules say otherwise. Some organisations forbid
  AI attribution for legal reasons — the project's rule wins, full stop. Do not ask each
  time.

---

## Stage 0 — Preflight, then load the docs manifest

### 0.1 Check what is available

| Dependency | Check | If missing |
|---|---|---|
| `gh`, authenticated | `gh auth status` | **STOP.** Stages 1 and 4 cannot run. |
| `git` | `git --version` | **STOP.** |
| `python3` with PyYAML | `python3 -c 'import yaml'` | **STOP.** 0.2 cannot run. `python3 -m pip install pyyaml`. |
| `superpowers` plugin | `claude plugin list` shows `superpowers` | **Say so, name the affected stages, ask whether to continue.** |
| Serena symbol tools | `find_symbol` is callable | Note it; Stage 1.3 falls back to grep and full-file reads. |
| code-graph MCP tools | `code-review-graph` tools are callable | Note it; Stage 1.3 falls back to symbol tools, then to grep. |

`superpowers` is a hard prerequisite: this pipeline composes it rather than restating it,
and plugin manifests have no dependency field, so it cannot be auto-installed.

```
claude plugin install superpowers@claude-plugins-official
```

Without it, Stages 2.2, 3.1 and 3.3 lose their sub-skill. **The TDD gate below is
self-contained and still binds.** Name the degraded stages and get an explicit go-ahead
before continuing.

### 0.2 Load the docs manifest

`${CLAUDE_PLUGIN_ROOT}` is set by the plugin runtime to this plugin's installed location.
The script is always invoked by an **absolute** path while the working directory stays the
repository being shipped — it reads `docs/` from the working directory, so `--check`
validates the repo you are standing in.

```bash
cat docs/MANIFEST.md
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py --check
```

| Result | Action |
|---|---|
| Script not found (`${CLAUDE_PLUGIN_ROOT}` unset or wrong) | Locate the plugin install, or a clone of this repo, and invoke its `bin/build-manifest.py` by absolute path. **Never `cd` out of the target repo** — that would check the wrong repository's docs. |
| No `docs/MANIFEST.md` (manifest absent) | **STOP.** "No docs manifest. Run `/doc-scaffold` first." |
| Manifest present but no entry carries `governs:` frontmatter (empty) | **STOP.** "Manifest is empty — no doc governs anything yet. Run `/doc-scaffold`." |
| `--check` reports DRIFT (stale) | **STOP.** "Manifest is stale. Run `${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py`." |
| `no docs/ directory here` | **STOP.** "No `docs/` directory. Run `/doc-scaffold` first." |
| `error: PyYAML is required…` | The parser is missing, not the docs. `python3 -m pip install pyyaml`, then re-run. |
| `error:` naming a doc and a YAML problem — malformed `governs:` frontmatter | **STOP.** Fix that doc's frontmatter, then re-run `--check`. |
| Current | Proceed to 0.3 |

**There is no degraded mode.** Do not fall back to `CLAUDE.md`, do not infer placement
from the file tree, do not proceed "just this once" because the issue looks small.
`CLAUDE.md` files do not carry placement tables, so a warned-but-continuing run guesses.

### 0.3 Route

Match the issue's likely touched paths and change shape against the
manifest. That yields the governing docs for this change.

### 0.4 Read

Read the routed docs, plus `docs/decisions.md` always.

- A doc carrying a `status:` field is reported with that status — not presented as current.
- A doc whose manifest row reads `verify: ask` cannot be checked against the source tree.
  Report its contents as **unverifiable-from-source**, not as derived fact. Such a doc can
  never produce a contradiction FAIL in Stage 3.1 — an unfalsifiable claim cannot be
  contradicted — only a gap.

`CLAUDE.md` remains orientation and traps. It is not the rule source.

**Build constraints.** `docs/architecture.md` carries a section under the shape tag
`build-constraints`, written by `/doc-scaffold` in exactly this shape:

```markdown
## Build constraints

- **Pre-commit hook compiles:** yes | no | not recorded
- **Cold build cost:** <duration> | not recorded
- **Concurrent builds safe:** yes | no | not recorded
```

Read it and apply it to the invariant in *Non-negotiables*:

| Reading | Apply |
|---|---|
| `Pre-commit hook compiles: yes` **or** `Concurrent builds safe: no` | Serialise. One commit per branch; never two agents building at once; no worktrees. |
| `Concurrent builds safe: yes` **and** `Pre-commit hook compiles: no` | Multiple commits on the branch are fine, and parallel agents may build. |
| Any field reads `not recorded`, or the section is absent | Serialise — and say why: "build constraints are not recorded, so I am serialising builds and committing once." |

---

## Stage 1 — Investigate

### 1.1 Fetch the issue

```bash
gh issue view <n> --json number,title,body,labels,comments
```

Extract: type, affected apps/packages/crates, acceptance criteria, linked issues.

**Validate the issue against the code before acting on it.** Issue text lags reality
routinely — closed work described as pending, pending work described as done. Confirm the
premise holds before you plan around it.

If the issue is ambiguous or underspecified, **ask now.** Not after the plan exists.

### 1.2 Refresh the code graph

```bash
code-review-graph update
```

Wait for it to finish. Skip only if the project has no graph configured.

### 1.3 Explore

`semantic_search_nodes_tool` → `find_symbol` → `find_referencing_symbols` →
`get_impact_radius_tool`. Add `get_architecture_overview_tool` only when the issue spans
several apps or packages.

**Leave this stage with exact file paths and symbol names.** Not "update the cases module"
— `libs/domain/citations/src/domain.rs:validate_citation`.

---

## Stage 2 — Build

### 2.1 Branch

| Type | Format |
|------|--------|
| Feature / enhancement | `feat/issue-<n>-<slug>` |
| Bug fix | `fix/issue-<n>-<slug>` |
| Refactor / chore | `chore/issue-<n>-<slug>` |
| Docs | `docs/issue-<n>-<slug>` |

Slug: lowercase, hyphenated, ≤40 chars, from the title.

Base on the repository's **default branch** — detect it, do not assume `main`:

```bash
gh repo view --json defaultBranchRef -q .defaultBranchRef.name
# offline fallback: git symbolic-ref --short refs/remotes/origin/HEAD
git checkout -b <type>/issue-<n>-<slug> <default-branch>
```

If the work depends on an unmerged branch, **ask before stacking**
(`--base feat/other`). Do not push yet.

### 2.2 Plan

Invoke `superpowers:writing-plans`, applying the Stage 0 rules as hard constraints. The
plan must carry:

```
## Context
Issue number and title, the problem, affected areas, related issues

## Placement
Exact paths for every new file, from the project rules' placement table.
Exact paths for every file to be modified.

## Tasks
[ ] Task 1 — with its test named first
[ ] ...

## Completion checklist
[ ] Project build/lint/type gate clean
[ ] Test suite passing
[ ] ADR appended (if a design decision was made)
[ ] Commit count matches the Stage 0.4 build constraints
```

**Stop when the plan is written.** Present it and ask: "Plan is ready — any modifications
before execution?" A pause after design means do not start building. Only invoke
`superpowers:executing-plans` or `superpowers:subagent-driven-development` after explicit
approval — and note that both open by asking `superpowers:using-git-worktrees` for an
isolated workspace: **the current checkout is that workspace**, so take those skills'
"verify the existing one" branch and do not create a worktree.

### 2.3 Implement, test-first

**REQUIRED SUB-SKILL:** `superpowers:test-driven-development` governs this step. Invoke it.

Work the plan. Project rules bind throughout: placement, naming, library choices, schema
rules, the correct database.

Prefer symbol-level edits (`replace_symbol_body`, `insert_after_symbol`,
`replace_content`) where the boundary is clean.

---

## The TDD gate

**Stage 2.3 does not produce implementation code until a test for it exists and fails.**

Write implementation before its test? Delete the implementation. Start over with the test.

**No exceptions:**
- Not for "it's a one-line fix"
- Not for "the test would just mirror the implementation"
- Not for "I'll add the test right after, in the same commit"
- Don't keep it in a scratch file "for reference"
- Don't "adapt" it while writing the test
- Delete means delete

**Violating the letter of this rule is violating its spirit.**

### What counts as covered

The project rules name the coverage requirement — honour theirs first. When they are silent:

| Change | Test required |
|---|---|
| New pure function (domain logic, transform, validator, parser) | **Yes.** Unit test, non-negotiable. |
| Bug fix of any size | **Yes.** A regression test that fails before the fix. |
| New shared-package component or hook | **Yes.** |
| Changed behaviour of an existing tested unit | **Yes.** Extend the existing test. |
| Route handler, page, wiring, composition | Not required, **but** any logic extracted from it is. |
| Pure config, copy, formatting, dependency bump | No. |

A "N/A — no testable unit" call is legitimate, but it is a **claim you state explicitly in
the plan and the PR body**, not a silence.

### Rationalizations — all of these mean write the test first

| Excuse | Reality |
|---|---|
| "The project rules don't require it here" | Project rules set the *floor*, not the ceiling. This gate is the floor. |
| "It's a hot fix, no time" | The gate is what makes hot fixes safe to merge fast. |
| "The user is waiting" | The user asked for shipped work, not fast-looking work. |

### Red flags — STOP and restart the step

- Implementation file open before the test file
- "Let me get it working, then test it"
- "I'll note the test as a follow-up task"
- A completion checklist where the test task sits after the implementation task
- Any sentence beginning "this case is different because…"

---

## Stage 3 — Verify

### 3.1 Review gate

Refresh the graph, then `detect_changes_tool` + `get_review_context_tool`.

**REQUIRED SUB-SKILL:** `superpowers:requesting-code-review`.

Mark every category **PASS / FAIL / N/A**:

- **Correctness** — every acceptance criterion addressed, or explicitly deferred with a
  note. No scope creep.
- **Placement** — matches the project rules' table. Nothing in the wrong layer. No new
  top-level directory invented.
- **Project rules** — each rule the change touches, checked by name. Schema, database,
  frontend, language conventions.
- **Tests** — the TDD gate's coverage table satisfied. Each test failed before its
  implementation existed.
- **Build gate** — the project's commands, actually run, output in the transcript.

Style is the linter's job. **Do not flag what the linter already catches, and do not
invent findings.** A conscious trade-off with a code comment and a PR note is a PASS with
a note, not a FAIL.

**Doc drift splits by kind** — an authoritative doc that is wrong actively misdirects:

- The change makes a governing doc's claim **false** → **FAIL.** Fix the doc or the code,
  in the same commit. If that edit changed a doc's `governs:` block, added a doc, or
  removed one, regenerate the manifest with
  `${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py` and carry `docs/MANIFEST.md` into the
  same commit — a stale manifest hard-blocks the *next* `/ship` at Stage 0.2.
- The change does something the doc **does not mention yet** → **note**, non-blocking.
  Offer it after PASS.

A claim must be falsifiable before it can be contradicted; an unfalsifiable one ("keep
actors clean", or anything in a `verify: ask` doc) is a gap at worst, never a FAIL.

### 3.2 On FAIL

Report findings as `[Category] <what> — <file:line>` with an actionable fix for each. Do
not commit. Fix the delta only — do not re-plan completed work — then re-run the gate.

**After two corrective loops, stop and surface what remains to the user.**

Fix root causes. A lint suppression needs an inline comment explaining why.

### 3.3 Completion claim

**REQUIRED SUB-SKILL:** `superpowers:verification-before-completion`. Do not write "tests
pass" or "the gate is clean" until the command output saying so is in the transcript.

---

## Stage 4 — Deploy

### 4.1 ADR

If the branch made a design decision, append to `docs/decisions.md` — **append, never
replace**:

```markdown
## <Feature> — <YYYY-MM-DD>

**Decision**: one sentence — what was built or decided.
**Context**: why it was needed.
**Placement**: what was created and where.
**Constraints applied**: which project rules bound the design.
**Deferred**: what was explicitly not done, and why.
```

### 4.2 Commit

Commit count follows the Stage 0.4 build constraints: one commit unless the project
records that its pre-commit hook does not compile.

If anything under `docs/` changed on this branch — an ADR, a governing doc fixed in
Stage 3.1, a new doc — regenerate the manifest first and stage it with the rest.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py    # only if docs/ changed
git add <specific files> docs/MANIFEST.md      # never -A, never .
git commit -m "$(cat <<'EOF'
<type>(<scope>): <concise description>

<1–3 sentences: what changed and why, not how>

fixes #<n>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

Type matches the branch type. Scope is the primary app, package or crate. Drop the
`docs/MANIFEST.md` path when no doc changed, and drop the trailer only if the project
rules forbid attribution (see *Non-negotiables*).

### 4.3 Push and open the PR

```bash
git push -u origin <branch>
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2–4 bullets>

## Changes
<file groups, and the reason for each group>

## Tests
<what was added, and what was consciously left uncovered — with the reason>

## Test plan
- [ ] <project gate command> — run, output in the PR thread or transcript
- [ ] <manual critical-path steps for the human>

fixes #<n>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Return the PR URL. **Stop here.**

---

## Stage 5 — Learn

**User-triggered only. Never automatic.** After the PR is open, offer — do not act:

> Anything from this branch worth writing down?

Route by scope:

| Kind | Destination |
|---|---|
| Outlives this repo — a framework, language, or architecture call | Whatever cross-project knowledge store the user keeps, if any — a `second-brain` skill, a notes vault, a team wiki. Ask which; never assume a path. If there is none, offer to note it in the PR body instead. |
| Specific to this repo — a convention, a trap, a placement rule | the manifest-governed doc that covers it (see `docs/MANIFEST.md`) |

Writing into a repo doc can change the doc set or a `governs:` block. When it does,
regenerate the manifest (`${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py`) and commit
`docs/MANIFEST.md` alongside the doc — otherwise the next `/ship` blocks at Stage 0.2.

If the answer is nothing, that is a valid answer. Move on.

---

## After the merge

The human merges. Then `/clean`.

---

## Edge cases

- **Too large for one PR** — scope to the smallest shippable slice and say in the PR body
  what was deferred. Do not open sub-issues without asking.
- **Blocked on unmerged work** — ask before stacking. Never branch a dependent change off
  the default branch and hope.
- **A decision the project rules do not cover** — surface it during Stage 2.2 and get a
  ruling. No silent assumptions.
- **Gate failures** — fix the root cause, never suppress. A suppression needs a comment.
- **A bug appears mid-implementation** — invoke `superpowers:systematic-debugging` before
  proposing a fix.
- **The issue turns out to be already done** — say so, close the loop with the user, do not
  manufacture work to justify the branch.
