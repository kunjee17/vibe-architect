# Roadmap

Six things were named. They do not belong in one spec — each group below gets its own
design → plan → implement cycle.

## A — Ship pipeline

`ship` · `auto` · `clean`

The daily loop. Self-contained, depends on nothing else here, and `/goal` removes the hardest
part (the looping construct) before it is written.

**Do this first.** It is what gets used every day, and it is the one that lets the local
`kl-ship` / `pi-ship` / `nv-ship` be deleted and the result open-sourced.

Done when: one real issue in k_lawyer goes from `/ship <n>` to a merged PR, with tests written
first, without touching `kl-ship`.

## B — Knowledge loop

Learn (extends `second-brain`) · `adr-compact`

Both write down what was learned; `adr-compact` maintains the same artifact class.

**Most valuable long-term, least defined.** The routing question — cross-repo vs repo-specific
— is answered in principle but not in mechanism. `adr-compact` is the concrete half and could
be built first on its own: ~10,700 lines across three repos in an identical format, and one
manual compaction already done by hand in pi_dx.

## C — Doc scaffolding

`doc-scaffold`

**Cheapest.** pi_dx already has the template; k_lawyer and nyayvaani have fragments. Mostly a
matter of writing down a structure that exists and generating the missing files.

## Order

**A → C → B.** A unblocks daily use; C is an afternoon; B needs its mechanism settled and
benefits from watching A and C run first.

`adr-compact` can jump the queue if `decisions.md` becomes painful before B is ready — it is
independent of the Learn routing question.

## Open questions

1. ~~**Where Part A lands after migration.**~~ **Answered 2026-09-02** — a lookup order:
   `*-rules` skill, then `CLAUDE.md`, then ask. See `decisions.md`.
2. **Learn's write mechanism.** The destinations are decided; how a session actually proposes a
   rule and gets it approved is not.
3. **What "test coverage around test cases" means.** Raised but never pinned down — coverage
   thresholds as a gate, or something else.
4. **Whether `auto --all` is ever wanted.** Currently answered by `/goal` typed by hand. If that
   proves awkward in practice, revisit.
5. ~~**Marketplace layout.**~~ **Answered 2026-09-02** — single plugin, seven skills.
   `claude plugin validate` passes.

6. **Whether the TDD gate actually binds.** It is written as a discipline rule with a
   rationalization table, but it has not been pressure-tested against a subagent, and the
   coverage table's defaults are a guess. This is Q3 restated as something falsifiable.

7. **Whether the Codex / Cursor / Gemini manifests work.** Written from superpowers' shapes,
   never installed on those runtimes.
