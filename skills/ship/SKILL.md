---
name: ship
description: Use when taking a numbered GitHub issue through to an open pull request — invoked as /ship <issue-number>, or when asked to implement, fix, or ship a specific issue in any repository.
---

# ship — issue to pull request

```
/ship <issue-number>
```

Five stages: **Investigate → Build → Verify → Deploy → Learn.**

This skill carries the *workflow*. It carries no project rules — those are loaded in
Stage 0 from the repository you are standing in. Project rules always win on specifics
(paths, commands, schemas); this skill wins on process.

**`ship` never merges.** It stops at an open PR. Merging is a human decision made after
manual critical-path testing.

---

## Non-negotiables

Read these before Stage 0. They bind every stage and are not overridable by a project rule
file, a plan, or time pressure.

- **Tests before implementation.** Stage 2 does not begin without a failing test. See
  *The TDD gate* below.
- **Never worktrees.** `superpowers:using-git-worktrees` is disabled inside this pipeline.
  One checkout, branches switched sequentially. Do not offer a worktree as an option.
- **Never merge, never auto-merge.** Stage 4 ends at a PR URL. Not `gh pr merge`, not
  `--auto`, not "it's a trivial docs change".
- **One issue → one branch → one commit.** Logical milestone commits on a long branch are
  fine. Per-task commits are not.
- **Evidence before assertions.** No "tests pass" without the command output in the
  transcript. Applies to every claim in the PR body.
- **Structural tools before file scanning.** Code-graph and symbol tools first; grep and
  full-file reads are the fallback, not the default.
- **Attribution trailers are the default.** Add the `Co-Authored-By` trailer and the
  Claude Code PR footer unless the project rules explicitly say otherwise — and treat a
  project rule forbidding them as suspect, since that preference was reversed on
  2026-08-16 and several `*-ship` skills still carry the old text. Do not ask each time.

---

## Stage 0 — Preflight, then load the docs manifest

### 0.1 Check what is available

| Dependency | If missing |
|---|---|
| `gh`, authenticated | **STOP.** Stages 1 and 4 cannot run. `gh auth status` to check. |
| `git` | **STOP.** |
| `superpowers` plugin | **Say so, name the affected stages, ask whether to continue.** |
| code-graph MCP tools | Note it; Stage 1.3 falls back to symbol tools, then to grep. |

`superpowers` is a **hard prerequisite by design** — this pipeline composes it rather than
restating it, and a vendored copy would drift. It is not bundled and cannot be
auto-installed: Claude Code plugin manifests have no dependency field.

```
claude plugin install superpowers@claude-plugins-official
```

Without it, `writing-plans`, `requesting-code-review`,
`verification-before-completion` and `systematic-debugging` are unavailable, and Stages
2.2, 3.1 and 3.3 lose their sub-skill. **The TDD gate below is self-contained and still
binds** — it does not depend on the plugin. Say which stages are degraded and get an
explicit go-ahead before continuing.

### 0.2 Load the docs manifest

`${CLAUDE_PLUGIN_ROOT}` is set by the plugin runtime to this plugin's installed
location; running from a clone of this repo instead, the plain `bin/` path works.

```bash
cat docs/MANIFEST.md
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py --check
```

| Result | Action |
|---|---|
| No `docs/MANIFEST.md` (manifest absent) | **STOP.** "No docs manifest. Run `/doc-scaffold` first." |
| Manifest present but no entry carries `governs:` frontmatter (empty) | **STOP.** "Manifest is empty — no doc governs anything yet. Run `/doc-scaffold`." |
| `--check` reports DRIFT (stale) | **STOP.** "Manifest is stale. Run `${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py`." |
| `no docs/ directory here` | **STOP.** "No `docs/` directory. Run `/doc-scaffold` first." |
| `error:` — malformed `governs:` frontmatter | **STOP.** Fix the doc's frontmatter, then re-run `--check`. |
| Current | Proceed to 0.3 |

**There is no degraded mode.** Do not fall back to `CLAUDE.md`, do not infer
placement from the file tree, do not proceed "just this once" because the
issue looks small. A precondition that can be skipped is a preference, and
this one was measured: no `CLAUDE.md` in the repos this was built from
carries a placement table, so a warned-but-continuing run still guesses.

### 0.3 Route

Match the issue's likely touched paths and change shape against the
manifest. That yields the governing docs for this change.

### 0.4 Read

Read the routed docs, plus `docs/decisions.md` always. A doc carrying a
`status:` field is reported with that status — not presented as current.

`CLAUDE.md` remains orientation and traps. It is not the rule source.

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

```bash
git checkout -b <type>/issue-<n>-<slug>
```

Base on `main`. If the work depends on an unmerged branch, **ask before stacking**
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
[ ] Single commit
```

**Stop when the plan is written.** Present it and ask: "Plan is ready — any modifications
before execution?" A pause after design means do not start building. Only invoke
`superpowers:executing-plans` or `superpowers:subagent-driven-development` after explicit
approval.

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
| "Too simple to break" | Simple code breaks. The test costs 30 seconds. |
| "I'll write tests after" | Tests written after passing code prove nothing about the code. They encode what it does, not what it should do. |
| "I already ran it manually" | Manual runs are not in CI and do not survive the next change. |
| "The test would just restate the implementation" | Then the behaviour is unclear. That is a design signal, not a reason to skip. |
| "Tests-after achieve the same goal" | Tests-first is a design tool. Tests-after is a description tool. Different tools. |
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

**Doc drift splits by kind.** The manifest declares these docs authoritative
and Stage 0 refuses to run without them, so an authoritative doc that is
wrong actively misdirects.

- The change makes a governing doc's claim **false** → **FAIL.** Fix the doc
  or the code, in the same commit.
- The change does something the doc **does not mention yet** → **note**,
  non-blocking. Offer it after PASS.

A claim must be falsifiable before it can be contradicted. "Only
`CommandActor` appends" is falsifiable. "Keep actors clean" is not — that is
a gap at worst, never a FAIL.

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

If the branch made a design decision, append to the project's decision log (usually
`docs/decisions.md`) — **append, never replace**:

```markdown
## <Feature> — <YYYY-MM-DD>

**Decision**: one sentence — what was built or decided.
**Context**: why it was needed.
**Placement**: what was created and where.
**Constraints applied**: which project rules bound the design.
**Deferred**: what was explicitly not done, and why.
```

### 4.2 Commit

One commit, all changes.

```bash
git add <specific files>          # never -A, never .
git commit -m "$(cat <<'EOF'
<type>(<scope>): <concise description>

<1–3 sentences: what changed and why, not how>

fixes #<n>
EOF
)"
```

Type matches the branch type. Scope is the primary app, package or crate. Include the
attribution trailer per *Non-negotiables* above.

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
| Outlives this repo — a framework, language, or architecture call | `second-brain` skill → `~/Workspace/secondbrain/` |
| Specific to this repo — a convention, a trap, a placement rule | the manifest-governed doc that covers it (see `docs/MANIFEST.md`) |

If the answer is nothing, that is a valid answer. Move on.

---

## After the merge

The human merges. Then `/clean`.

---

## Edge cases

- **Too large for one PR** — scope to the smallest shippable slice and say in the PR body
  what was deferred. Do not open sub-issues without asking.
- **Blocked on unmerged work** — ask before stacking. Never branch a dependent change off
  `main` and hope.
- **A decision the project rules do not cover** — surface it during Stage 2.2 and get a
  ruling. No silent assumptions.
- **Gate failures** — fix the root cause, never suppress. A suppression needs a comment.
- **A bug appears mid-implementation** — invoke `superpowers:systematic-debugging` before
  proposing a fix.
- **The issue turns out to be already done** — say so, close the loop with the user, do not
  manufacture work to justify the branch.
