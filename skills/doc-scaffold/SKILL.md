---
name: doc-scaffold
description: Use when a repository has no docs/MANIFEST.md and the issue-to-PR pipeline refuses to run, or when asked to set up, scaffold, or bootstrap documentation for a repository that has never organised its docs into a structure an agent can route through.
---

# doc-scaffold — bootstrap a repo's docs baseline

Runs **once per repo**. Ends when `docs/MANIFEST.md` exists and `/ship` Stage 0 can route
through it.

## Deliverable

The run ends with these four in place:

- [ ] `docs/architecture.md` — carries the placement table
- [ ] `docs/product.md` — why it exists, who for, what is out of scope; `verify: ask`
- [ ] `docs/decisions.md` — the ADR log, append-only
- [ ] `docs/MANIFEST.md` — current, generated

## Step 1 — Derive

`${CLAUDE_PLUGIN_ROOT}` is set by the plugin runtime to this plugin's installed
location; running from a clone of this repo instead, the plain `bin/` path works.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/derive-facts.py
```

Read what it found and, just as carefully, what it lists as UNDERIVED. Every fact it
prints carries the file it was quoted from — carry that citation into the doc you write
the fact into.

Also derive whether specs and plans are tracked:

```bash
git check-ignore docs/superpowers && echo ignored || echo tracked
```

## Step 2 — Ask

One question at a time. These are not on any source tree, so ask them regardless of what
Step 1 found:

1. **Why does this exist, and who is it for?** → `docs/product.md`
2. **What will the code teach an agent wrong?** → the traps section of
   `docs/architecture.md`. Highest value per question asked; press for specifics.
3. **What was considered and rejected?** → `docs/decisions.md`
4. **What is deliberately deferred?**

Then ask, directly, every question Step 1 marked UNDERIVED — one at a time, same as above.

## The three states

Every section of every doc this skill writes ends in exactly one of three states:

1. **a derived fact**, with the file it was quoted from named next to it
2. **an answer from the user**, in the user's words
3. **the literal words "not recorded"**

A doc is finished when each of its sections is in one of these three states. There is no
fourth state — a filled-in-looking sentence that is not one of the three is the failure
mode this rule exists to name.

## Step 3 — Write the required core

Each of the three narrative docs carries `governs:` frontmatter:

```yaml
---
governs:
  paths: [src/**]
  shapes: [placement]
  verify: source
---
```

`docs/product.md` sets `verify: ask` — nothing about a product is checkable against a
source tree:

```yaml
---
governs:
  paths: []
  shapes: [product]
  verify: ask
---
```

## Step 4 — Offer, do not impose

Offer, on the evidence Step 1 produced — state the evidence when you offer:

| Step 1 found | Offer |
|---|---|
| more than one buildable unit | `docs/<units>/<name>.md`, one per unit |
| deploy or infra config | `docs/ops/` |
| a public-facing surface | `docs/design.md` |
| billing or entitlement code | `docs/product/pricing.md` |
| a published API surface | `docs/product/api-spec.md` |

"Step 1 found two buildable units (`packages/api`, `packages/web`) — want a doc for each?"
is an offer. A doc earns a place in the manifest once it has evidence or an answer behind
it — write it at that point, once its sections can already reach one of the three states
above.

## Step 5 — Generate and verify

```bash
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py --check
```

Report the manifest, and say plainly which sections read "not recorded".
