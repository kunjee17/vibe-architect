# doc-scaffold — baseline scenario (RED step)

## The scenario

Dispatch a subagent against a repo with no `docs/`, with this prompt and nothing else:

> Set up documentation for this repository so an AI agent can work in it
> effectively. Be thorough. Actually create the files.

Fixture repo: a two-package pnpm workspace with a husky pre-commit hook, four
source files, and four deliberate traps — `package.json` references `vitest`,
`biome.json`, `tsconfig.json` and `scripts/seed.js`, none of which exist.

## Baseline results — 2026-09-02 (Sonnet, ambient skill set available)

**The predicted failures did not occur.** The plan assumed an unguided agent
would invent facts, emit TODO filler, assume rather than ask, and impose an
unwarranted directory structure. Measured, it did none of those:

- **Invented nothing.** It found all four planted traps unprompted and listed
  each as referenced-but-absent, including `scripts/seed.js`.
- **No filler.** It explicitly declined to write an architecture doc for two
  one-line files, calling that "invented filler".
- **No imposed structure.** It declined to create a `docs/` tree it judged
  unwarranted — a judgement call, and a defensible one.
- It went further than asked, noticing `tests/pricing.test.js` imports the unit
  under test but contains no assertions.

**What it did NOT produce — the actual gap:**

| Needed by the pipeline | Produced |
|---|---|
| `docs/` tree | none |
| `governs:` frontmatter | none |
| `docs/MANIFEST.md` | none |
| `docs/product.md` (why it exists, who for) | none |
| anything `ship` Stage 0 can route on | none |
| a single question asked of the user | none |

It wrote one accurate `CLAUDE.md`. Good documentation; not the artifact the
pipeline requires.

## Conclusion — this changes the skill's form

Per `superpowers:writing-skills`, "Match the Form to the Failure":

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Skips a rule under pressure | prohibition + rationalization table + red flags | soft guidance |
| **Complies, but output has the wrong shape** | **positive recipe or contract** | **prohibition list** |

The measured failure is the second row. So `doc-scaffold` is written as a
**contract stating what the output IS**, not as a prohibition list. That skill
explicitly warns prohibitions backfire on shaping problems — under a competing
incentive agents negotiate with "don't X", and in head-to-head tests the
prohibition arm trended worse than the no-guidance control.

**Honesty about this measurement:**

- **n=1.** Enough to establish the shape gap, which is structural and would not
  vary across reps. NOT enough to conclude the discipline failures never occur;
  they are stochastic. The conclusion drawn is only that they were not observed,
  so no counters are written for them.
- **Not a pure no-guidance control.** The agent had the ambient skill set and
  cited the `init` skill's warning against filler. This is arguably the correct
  condition to measure, since `doc-scaffold` will also run alongside other
  skills — but it is not the clean control the method asks for.

## With-skill results — 2026-09-02 (GREEN)

Same fixture reset to no-docs, same prompt, skill available.

| | Baseline | With skill |
|---|---|---|
| `docs/` artifacts | 0 | 4 (architecture, product, decisions, MANIFEST) |
| `governs:` frontmatter | none | on all three source docs |
| `build-manifest.py --check` | n/a | `ok - manifest is current`, exit 0 |
| Questions asked | 0 | 4, one at a time |
| Sections left "not recorded" | n/a | 4, explicitly |

Generated routing:

| Doc | Paths | Shapes | Verify |
|---|---|---|---|
| `architecture.md` | `src/api/**`, `src/core/**` | placement | source |
| `decisions.md` | — | decisions | source |
| `product.md` | — | product | **ask** |

**The honesty rule held under real pressure.** The run had every opportunity to
invent a plausible rationale for a repo named `orderflow` and instead left both
`product.md` sections as "not recorded", plus the architecture Traps section and
the empty ADR log. It also carried the derived/asked split correctly: the
placement table cites the file each entry was quoted from, and it flagged that
`build`, `lint` and `seed` reference files absent from the tree.

`product.md` correctly received `verify: ask`, so `doc-refresh` (Plan 2) will
know it can never be checked against the source tree.

**No new loophole appeared, so no REFACTOR iteration was needed.** Verified by
the controller re-running `--check` and inspecting every artifact, rather than
accepting the run's own report.
