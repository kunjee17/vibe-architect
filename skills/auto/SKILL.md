---
name: auto
description: Use when no specific issue has been chosen yet and the next piece of work needs picking out of an open GitHub issue backlog — "what should I work on", "pick something easy", or /auto with optional label filters.
---

# auto — pick the next issue

```
/auto [label] [label] ...
/auto --milestone <name>
/auto --quick
```

Selection only. It ranks candidates, confirms one with you, and hands to `/ship`.

**It does not loop.** Repetition is `/goal`, typed by you — it is condition-driven and stops
when the queue empties, where `/loop` would keep firing at an empty backlog.

---

## Step 0 — Precondition

`auto` hands to `ship`, which requires a current docs manifest. Run the same check `ship`
Stage 0.2 runs:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py --check
```

Anything other than "current" — absent, empty, stale (DRIFT), no `docs/` directory, or a
malformed-frontmatter `error:` — **stop.** See `ship` Stage 0.2 for the exact remedy per
result; do not restate its table here. Do not rank issues you cannot then ship.

## Step 1 — List open unassigned issues

```bash
gh issue list --state open --json number,title,body,labels,assignees,milestone --limit 50
```

Add `--label "<a>,<b>"` when labels were passed, `--milestone "<name>"` for `--milestone`.
`gh` infers the repo from the checkout; name it explicitly with `--repo` only when the
remote is ambiguous.

**Drop every issue with a non-empty `assignees`.** Someone already has it.

Then ask the user: does a pinned tracking issue or a playbook doc sequence this backlog?
The manifest's `governs:` schema (`paths`, `shapes`, `verify`) has no field for this, so
there is no mechanical way to find one — ask rather than search for it. If they name one,
read it before ranking. **Sequence beats convenience**: an issue that unblocks the current
milestone outranks a smaller one that does not.

---

## Step 2 — Rank

### Complexity (primary sort, ascending)

Prefer the repo's own labels when they exist:

| Label | Score |
|---|---|
| `complexity:s` | 1 |
| `complexity:m` | 2 |
| `complexity:l` | 3 |
| `complexity:xl` | 4 |

**Most repos have only GitHub's default labels** (`bug`, `enhancement`, `documentation`,
`question`). There is no complexity taxonomy to read, so you are inferring every score.
That is expected — say which you used.

Infer 1–4 from title plus body:

| Score | Shape |
|---|---|
| 1 | One file. Copy fix, one field, one i18n key. |
| 2 | 2–3 known files, clear path, no new contract. |
| 3 | Cross-package or cross-crate, or a design decision is still open, or the body lists unknowns. |
| 4 | Schema change, new module or crate, architecture work, multi-app. |

Score from the issue text alone — ranking happens before `ship`'s Stage 1.3 codebase
exploration, so do not go digging through the repo to judge one. When the text is too thin
to judge, say so in the Notes column instead of guessing; an unrankable issue is a signal,
not something to score anyway.

Mark inferred scores `(inferred)` in the output.

**Never auto-pick a 4.** Surface it and let the user decide — that is design territory, and
it wants `superpowers:brainstorming` before it wants `/ship`.

### Priority (tiebreak, ascending)

`priority:p0-critical` → 0, `p1-high` → 1, `p2-medium` → 2, `p3-low` → 3, unlabelled → 2.

Sort ascending by **(complexity, priority)**. With `--quick`, additionally drop anything
scoring above 2 and anything whose body **names a blocker** — an explicit dependency on
another issue or on unmerged work, or an open question the body says must be answered
before work can start.

---

## Step 3 — Present the top 3

```
Rank  #      Title                             Complexity    Priority  Notes
----  -----  --------------------------------  ------------  --------  --------------------------
1     #123   Add matter tag field              s (label)     p2        single field + i18n key
2     #117   Fix citation error copy           1 (inferred)  p3        UI copy only
3     #141   Tabular column reorder bug        m (label)     p1        bug in existing component
```

The Notes column justifies the score in one phrase — especially for inferred ones.

---

## Step 4 — Confirm, then hand off

> Picking **#\<n\> — \<title\>** (complexity \<s\>, \<label|inferred\>).
> Confirm to start `/ship <n>`, or give a different issue number.

**Wait for the answer.** Then invoke `/ship <n>` and follow that workflow from Stage 0.

---

## Edge cases

- **No candidates** — say the backlog is empty (or fully assigned) under those filters and
  stop. Do not widen the filters unasked.
- **Everything scores 4** — report that and recommend brainstorming the top one rather than
  shipping it.
- **The tracking issue or playbook contradicts the complexity ranking** — it wins. Say so
  in Notes.
