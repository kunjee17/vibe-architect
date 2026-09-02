---
name: clean
description: Use when a pull request has just been merged and the local feature branch, the main checkout and stale remote tracking refs still need tidying up.
---

# clean — post-merge local cleanup

```
/clean
```

Verifies the working branch actually landed, pulls the default branch, deletes the branch locally,
prunes stale remote tracking refs.

**Every step that could lose work stops rather than forcing.** Nothing here uses `-D`,
`-f`, or a non-fast-forward pull. If a step's precondition fails, report and stop — do not
route around it.

---

## Step 1 — Check for uncommitted changes

```bash
git status --short
```

Anything uncommitted or unstaged → **stop and report it.** The user handles it first.

Two categories of noise are common and worth naming rather than deleting:

- **Generated-but-gitignored files** that a build or check command rewrites on every run.
- **Files a `git add .` pre-commit hook swept in** on an earlier commit.

Report what you see; let the user decide. Never `git checkout --` or `git clean` on their
behalf.

---

## Step 2 — Detect the default branch, then record the current branch

```bash
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

Store as `<default-branch>`. If that fails (no `gh`, no auth, no network), fall back to:

```bash
git symbolic-ref refs/remotes/origin/HEAD
```

(strip the `refs/remotes/origin/` prefix to get the branch name). Use `<default-branch>`
everywhere below — **never hardcode `main`.**

```bash
git branch --show-current
```

Store as `<current-branch>`. **Empty output means detached HEAD** — stop and report "Not on
a branch (detached HEAD) — nothing to clean." If `<current-branch>` equals
`<default-branch>`, there is nothing to clean — say so and stop.

---

## Step 3 — Fetch and verify the merge

```bash
git fetch origin
gh pr list --head <current-branch> --state merged --json number,mergedAt,title
```

- **Non-empty array** → a merged PR exists. Proceed.
- **Empty array** → report `No merged PR found for branch <current-branch>. Aborting.`
  and stop. **Delete nothing.**

If this branch was stacked on another feature branch, check the parent landed too — a
stacked child can show as merged while its base is still open.

---

## Step 4 — Switch to the default branch and pull

```bash
git checkout <default-branch>
git pull --ff-only origin <default-branch>
```

If `--ff-only` fails, local `<default-branch>` has diverged. Report the error and stop.
**Never force pull.**

---

## Step 5 — Delete the local branch

```bash
git branch -d <current-branch>
```

`-d` only, **never `-D`**. If it fails despite Step 3 passing, report and stop — that
discrepancy is worth a human look.

---

## Step 6 — Prune stale remote tracking refs

```bash
git remote prune origin
```

Capture which refs were pruned.

---

## Step 7 — Offer a build-artifact sweep

Only if the project rules name a sweep command — some toolchains accumulate build
artifacts fast. **Offer, do not run unasked:**

> `<project sweep command>` would drop stale build artifacts. Run it?

Never suggest a full clean as routine cleanup — it forces a cold rebuild of the whole tree.

---

## Step 8 — Report

- Deleted branch: `<current-branch>`
- Now on: `<default-branch>` at `<git rev-parse --short HEAD>`
- Pruned refs: `<list, or "none">`
- Swept: `<yes / no / not offered>`
