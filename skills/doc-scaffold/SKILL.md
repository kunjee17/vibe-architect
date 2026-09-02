---
name: doc-scaffold
description: Use when a repository has no docs/MANIFEST.md — including when /ship or /auto stops with "No docs manifest" or "Manifest is empty" — or when asked to set up, scaffold, or bootstrap documentation for a repository with no docs structure an agent can route through.
---

# doc-scaffold — bootstrap a repo's docs baseline

Runs **once per repo**. Ends when `docs/MANIFEST.md` exists and `/ship` Stage 0 can route
through it.

## Deliverable

- [ ] `docs/architecture.md` — placement, gate commands, build constraints, traps
- [ ] `docs/product.md` — why, who for, out of scope, deferred; `verify: ask`
- [ ] `docs/decisions.md` — the ADR log, append-only
- [ ] `docs/MANIFEST.md` — current, generated

## The shapes this skill assigns

The shape vocabulary `ship` routes on is minted here. Use exactly these names, every repo:

| Doc | `shapes:` |
|---|---|
| `architecture.md` | `placement`, `build-constraints` |
| `product.md` | `product` |
| `decisions.md` | `decisions` |

A doc offered in Step 4 carries the shape of the doc it specialises.

## Step 1 — Derive

Invoke by absolute plugin path, with the target repo as the working directory.

```bash
${CLAUDE_PLUGIN_ROOT}/bin/derive-facts.py
```

Each fact prints the file it was quoted from — carry that citation into the doc. Read the
UNDERIVED list as carefully.

**Seed traps.** For each derived gate command, check that the file or binary it invokes
exists. Every miss is a traps entry, cited to the manifest declaring it.

**Establish how specs and plans are stored.** Two probes on observable state:

```bash
git ls-files docs/superpowers      # any output = this repo already tracks them
git check-ignore docs/superpowers  # exit 0     = this repo already ignores them
```

- Either probe speaks → follow it, citing the command that spoke.
- Both silent → no practice is established. Ask: **"Is this repo public, and do the plans
  discuss unreleased work?"** Public *and* unreleased → add `docs/superpowers/` to
  `.gitignore`; otherwise track it.

Record the outcome as an entry in `docs/decisions.md`.

## Step 2 — Ask

One question at a time. Every answer has a destination, and "not recorded" is an accepted
answer to each.

| Ask | Goes in |
|---|---|
| Why does this exist, and who is it for? | `product.md` |
| What is out of scope — what will this deliberately not do? | `product.md` |
| What is deferred — wanted, but not now? | `product.md` |
| What was considered and rejected? ("nothing yet" is honest on a young repo) | `decisions.md` |
| Something that looks like a bug but is deliberate — and why? | traps |
| A term that means something different here than elsewhere? | traps |
| Somewhere the obvious approach is wrong? | traps |
| Does the pre-commit hook compile or build? | build constraints |
| What does a cold build cost? | build constraints |
| Is running two builds at once on one machine safe? | build constraints |

Step 1 partly derives the hook question — `pre-commit-automation` facts show a hook
exists, not whether it compiles — so ask to confirm.

Then every question Step 1 marked UNDERIVED, in these words:

| UNDERIVED slug | Ask | Goes in |
|---|---|---|
| `units` | What separately buildable pieces does this repo hold? | placement table |
| `gate-commands` | What must pass before a change is shippable? | gate commands |
| `pre-commit-automation` | What runs automatically on commit? | build constraints |
| `dependency-manifests` | Where are dependencies declared? | placement table |

Traps, placement, gate commands and build constraints are `docs/architecture.md` sections.

## The three states

Every section of every doc this skill writes ends in exactly one of three states:

1. **a derived fact**, with the file it was quoted from named next to it
2. **an answer from the user**, in the user's words
3. **the literal words "not recorded"**

## Step 3 — Write the required core

Each narrative doc carries `governs:` frontmatter. `paths:` comes from the layout Step 1
derived — `lib/**` in a mix repo, `packages/*/src/**` in a workspace. The placeholder
below names what to look up rather than a value to paste:

```yaml
---
governs:
  paths: [<the source roots Step 1 derived>]
  shapes: [placement, build-constraints]
  verify: source
---
```

`product.md` sets `paths: []` and `verify: ask` — nothing about a product is checkable
against a source tree. `decisions.md` sets `paths: []` and `verify: source`. Both take
their shape from the table above.

**`architecture.md`** — a placement table (what kind of change goes where, a row per unit,
each cited), gate commands (what must pass, each cited), build constraints, and traps (a
row per finding from Steps 1 and 2). Build constraints take this shape verbatim; `ship`
parses the heading and the three labels:

```markdown
## Build constraints

- **Pre-commit hook compiles:** yes | no | not recorded
- **Cold build cost:** <duration> | not recorded
- **Concurrent builds safe:** yes | no | not recorded
```

**`product.md`** — why it exists and who for; what is out of scope; what is deferred.

**`decisions.md`** — append-only, newest last, each entry:

```markdown
## <date> — <the decision, one line>

- **Context:** <what forced the choice>
- **Decision:** <what was chosen>
- **Rejected:** <what else was considered> | not recorded
```

## Step 4 — Offer, do not impose

Offer on the evidence Step 1 produced, stating that evidence:

| Step 1 found | Offer |
|---|---|
| more than one buildable unit | `docs/<units>/<name>.md`, one per unit |
| deploy or infra config | `docs/ops/` |
| a public-facing surface | `docs/design.md` |
| billing or entitlement code | `docs/product/pricing.md` |
| a published API surface | `docs/product/api-spec.md` |

"Step 1 found two buildable units (`packages/api`, `packages/web`) — want a doc for each?"
is an offer. A doc earns its manifest place once evidence or an answer sits behind it and
its sections can reach one of the three states.

## Step 5 — Generate and verify

Confirm every section of every doc written is in one of the three states. Then, from the
repo root — `build-manifest.py` reads the working directory:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py
${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py --check
```

Report the manifest, and say plainly which sections read "not recorded".
