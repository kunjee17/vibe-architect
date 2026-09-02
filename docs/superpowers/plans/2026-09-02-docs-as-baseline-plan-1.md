# Docs-as-Baseline, Plan 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `docs/` the authoritative rule source for `ship`, by generating a routing manifest from per-doc frontmatter and gating the pipeline on it.

**Architecture:** An importable `docsbase` package holds three pure units — frontmatter parsing, manifest building/routing, and a data-driven fact detector. Two thin CLIs in `bin/` wrap them. Two skills (`doc-scaffold`, and a rewritten `ship` Stage 0) carry only judgment: what to ask, what counts as a contradiction. Mechanism lives in tested Python; judgment lives in prose.

**Tech Stack:** Python 3.11+ (stdlib `tomllib`, stdlib `unittest`), PyYAML as a soft dependency for frontmatter. No test dependencies — `unittest` tests run under `pytest` unchanged for contributors who have it.

**Spec:** `docs/superpowers/specs/2026-09-02-docs-as-baseline-design.md`

## Global Constraints

- **Python 3.11 minimum.** `tomllib` is stdlib from 3.11; do not add a `toml` dependency.
- **Zero required third-party packages.** PyYAML is the only import outside stdlib, it is soft, and its absence must produce one actionable line and exit 1 — never a silent fallback or a hand-rolled YAML parser.
- **Tests use stdlib `unittest`.** No `pytest` import anywhere, including in tests.
- **A detector extracts only what it can quote literally from a file.** It never infers. If it cannot quote its source, it reports nothing.
- **A miss is reported, never guessed.** Unmatched questions surface as `underived`, and the skill asks instead.
- **No ecosystem is privileged and none is a precondition.** Zero detector matches must still produce a usable run.
- **Skill frontmatter:** `name` kebab-case matching the directory; `description` starts with "Use when" and states triggering conditions only — never a workflow summary.
- **Existing commit convention:** include the `Co-Authored-By` trailer and the `Claude-Session` line (see the repo's recent commits for the exact form).

---

### Task 1: Package scaffolding and the test runner

Establishes the first executable code in this repo. Nothing here has logic worth testing on its own, so its deliverable is proven by Task 2's tests running green — this task ends when `bin/run-tests.py` executes and reports zero tests without error.

**Files:**
- Create: `docsbase/__init__.py`
- Create: `tests/__init__.py`
- Create: `bin/run-tests.py`
- Modify: `AGENTS.md` (add a "Running the tests" section)

**Interfaces:**
- Consumes: nothing
- Produces: `bin/run-tests.py` — discovers and runs every `tests/test_*.py`; exit 0 on pass, 1 on failure. Every later task's verification step calls it.

- [ ] **Step 1: Create the package markers**

`docsbase/__init__.py`:

```python
"""Mechanism for the docs-as-baseline pipeline.

Judgment lives in the skills under skills/; anything here must be
deterministic and testable.
"""

__all__ = ["frontmatter", "manifest", "detect"]
```

`tests/__init__.py`: empty file.

- [ ] **Step 2: Write the test runner**

`bin/run-tests.py`:

```python
#!/usr/bin/env python3
"""Run the docsbase test suite. Stdlib only — no pytest required.

Usage: bin/run-tests.py [-v]
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    verbosity = 2 if "-v" in sys.argv else 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Make it executable and run it**

Run:
```bash
chmod +x bin/run-tests.py && bin/run-tests.py
```
Expected: `Ran 0 tests` and `OK`, exit 0. Zero tests is correct here — Task 2 adds the first one.

- [ ] **Step 4: Document it**

Append to `AGENTS.md`:

```markdown
## Running the tests

```bash
bin/run-tests.py        # stdlib unittest, no pytest needed
bin/run-tests.py -v     # per-test output
```

Mechanism (`docsbase/`) is tested. Judgment (`skills/`) is prose and is
tested by pressure scenarios — see `superpowers:writing-skills`.
```

- [ ] **Step 5: Commit**

```bash
git add docsbase tests bin/run-tests.py AGENTS.md
git commit -m "build: add docsbase package and stdlib test runner"
```

---

### Task 2: Frontmatter parsing

**Files:**
- Create: `docsbase/frontmatter.py`
- Test: `tests/test_frontmatter.py`

**Interfaces:**
- Consumes: `bin/run-tests.py` from Task 1
- Produces:
  - `Governs` — dataclass with fields `paths: list[str]`, `shapes: list[str]`, `verify: str` (`"source"` or `"ask"`), `status: str | None`
  - `parse(text: str) -> Governs | None` — returns `None` when the document has no frontmatter or no `governs:` key, meaning the doc is not authoritative and never routes
  - `ParseError` — raised on malformed frontmatter or an invalid `verify` value

- [ ] **Step 1: Write the failing test**

`tests/test_frontmatter.py`:

```python
import unittest

from docsbase import frontmatter


class TestParse(unittest.TestCase):
    def test_full_block(self):
        doc = (
            "---\n"
            "governs:\n"
            "  paths: [libs/domain/**, libs/actors/**]\n"
            "  shapes: [event-schema, actor]\n"
            "---\n\n# Architecture\n"
        )
        g = frontmatter.parse(doc)
        self.assertEqual(g.paths, ["libs/domain/**", "libs/actors/**"])
        self.assertEqual(g.shapes, ["event-schema", "actor"])
        self.assertEqual(g.verify, "source")
        self.assertIsNone(g.status)

    def test_no_frontmatter_is_not_authoritative(self):
        self.assertIsNone(frontmatter.parse("# Just a heading\n"))

    def test_frontmatter_without_governs_is_not_authoritative(self):
        self.assertIsNone(frontmatter.parse("---\ntitle: Vision\n---\n# Vision\n"))

    def test_verify_ask_and_status(self):
        doc = (
            "---\n"
            "governs:\n"
            "  shapes: [scope]\n"
            "  verify: ask\n"
            "status: stale - cost basis changed\n"
            "---\n# Product\n"
        )
        g = frontmatter.parse(doc)
        self.assertEqual(g.verify, "ask")
        self.assertEqual(g.paths, [])
        self.assertEqual(g.status, "stale - cost basis changed")

    def test_invalid_verify_raises(self):
        doc = "---\ngoverns:\n  verify: sometimes\n---\n"
        with self.assertRaises(frontmatter.ParseError):
            frontmatter.parse(doc)

    def test_unterminated_frontmatter_raises(self):
        with self.assertRaises(frontmatter.ParseError):
            frontmatter.parse("---\ngoverns:\n  paths: [a]\n")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/run-tests.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsbase.frontmatter'`

- [ ] **Step 3: Write minimal implementation**

`docsbase/frontmatter.py`:

```python
"""Parse the `governs:` contract out of a doc's YAML frontmatter.

A doc with no frontmatter, or with frontmatter carrying no `governs:` key,
is NOT authoritative and never routes. That is the escape hatch for
narrative docs.
"""
from __future__ import annotations

import dataclasses

VALID_VERIFY = ("source", "ask")
DELIM = "---"


class ParseError(Exception):
    """Frontmatter is present but malformed, or a value is out of range."""


@dataclasses.dataclass(frozen=True)
class Governs:
    paths: list[str]
    shapes: list[str]
    verify: str
    status: str | None


def _load_yaml(block: str) -> dict:
    try:
        import yaml
    except ImportError:  # pragma: no cover - environment dependent
        raise ParseError(
            "PyYAML is required to read doc frontmatter. "
            "Install it with: python3 -m pip install pyyaml"
        )
    try:
        data = yaml.safe_load(block)
    except Exception as exc:
        raise ParseError(f"invalid YAML in frontmatter: {exc}") from exc
    return data if isinstance(data, dict) else {}


def _split(text: str) -> str | None:
    """Return the raw frontmatter block, or None when there is none."""
    if not text.startswith(DELIM + "\n"):
        return None
    end = text.find("\n" + DELIM, len(DELIM))
    if end == -1:
        raise ParseError("frontmatter opened with --- but never closed")
    return text[len(DELIM) + 1 : end + 1]


def parse(text: str) -> Governs | None:
    block = _split(text)
    if block is None:
        return None
    data = _load_yaml(block)
    governs = data.get("governs")
    if governs is None:
        return None
    if not isinstance(governs, dict):
        raise ParseError("`governs:` must be a mapping")

    verify = governs.get("verify", "source")
    if verify not in VALID_VERIFY:
        raise ParseError(
            f"`verify: {verify}` is not valid; use one of {VALID_VERIFY}"
        )

    status = data.get("status")
    return Governs(
        paths=list(governs.get("paths") or []),
        shapes=list(governs.get("shapes") or []),
        verify=verify,
        status=str(status) if status is not None else None,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bin/run-tests.py -v`
Expected: PASS — 6 tests, OK

- [ ] **Step 5: Commit**

```bash
git add docsbase/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: parse the governs: frontmatter contract"
```

---

### Task 3: Manifest building and routing

Routing is the load-bearing logic of the whole design — it decides which docs an agent reads. It gets the heaviest test coverage in this plan.

**Files:**
- Create: `docsbase/manifest.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: `frontmatter.parse`, `frontmatter.Governs` from Task 2
- Produces:
  - `Entry` — dataclass with `path: str`, `governs: frontmatter.Governs`
  - `collect(docs_dir: pathlib.Path) -> list[Entry]` — every authoritative doc, sorted by `path`
  - `render(entries: list[Entry]) -> str` — the full `MANIFEST.md` text
  - `route(entries, touched: list[str], shapes: list[str]) -> list[Entry]` — docs governing a change, sorted by `path`, deduplicated
  - `BEGIN`, `END` — the generated-block marker constants

- [ ] **Step 1: Write the failing test**

`tests/test_manifest.py`:

```python
import pathlib
import tempfile
import unittest

from docsbase import frontmatter, manifest


def _g(paths=(), shapes=(), verify="source", status=None):
    return frontmatter.Governs(list(paths), list(shapes), verify, status)


class TestRoute(unittest.TestCase):
    def setUp(self):
        self.entries = [
            manifest.Entry("docs/architecture.md", _g(paths=["libs/domain/**"],
                                                      shapes=["actor"])),
            manifest.Entry("docs/design.md", _g(paths=["packages/ui/**"])),
            manifest.Entry("docs/product.md", _g(shapes=["scope"], verify="ask")),
        ]

    def test_glob_match_selects_doc(self):
        hits = manifest.route(self.entries, ["libs/domain/matters/src/lib.rs"], [])
        self.assertEqual([e.path for e in hits], ["docs/architecture.md"])

    def test_shape_match_selects_doc_with_no_paths(self):
        hits = manifest.route(self.entries, [], ["scope"])
        self.assertEqual([e.path for e in hits], ["docs/product.md"])

    def test_no_match_returns_empty(self):
        self.assertEqual(manifest.route(self.entries, ["README.md"], []), [])

    def test_multiple_hits_are_sorted_and_deduplicated(self):
        hits = manifest.route(
            self.entries,
            ["packages/ui/src/Button.tsx", "libs/domain/a/src/lib.rs"],
            ["actor"],
        )
        self.assertEqual(
            [e.path for e in hits], ["docs/architecture.md", "docs/design.md"]
        )

    def test_nested_glob_matches_at_any_depth(self):
        hits = manifest.route(self.entries, ["libs/domain/a/b/c/d.rs"], [])
        self.assertEqual([e.path for e in hits], ["docs/architecture.md"])


class TestCollectAndRender(unittest.TestCase):
    def test_collect_skips_non_authoritative_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = pathlib.Path(tmp)
            (docs / "architecture.md").write_text(
                "---\ngoverns:\n  paths: [src/**]\n---\n# A\n"
            )
            (docs / "vision.md").write_text("# Vision\n")
            entries = manifest.collect(docs)
            self.assertEqual([e.path for e in entries], ["architecture.md"])

    def test_render_is_stable_and_marks_the_generated_block(self):
        entries = [manifest.Entry("docs/product.md",
                                  _g(shapes=["scope"], verify="ask",
                                     status="stale - provisional"))]
        out = manifest.render(entries)
        self.assertIn(manifest.BEGIN, out)
        self.assertIn(manifest.END, out)
        self.assertIn("docs/product.md", out)
        self.assertIn("stale - provisional", out)
        self.assertIn("ask", out)
        self.assertEqual(out, manifest.render(entries))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/run-tests.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsbase.manifest'`

- [ ] **Step 3: Write minimal implementation**

`docsbase/manifest.py`:

```python
"""Build the routing manifest and route a change to its governing docs."""
from __future__ import annotations

import dataclasses
import fnmatch
import pathlib

from docsbase import frontmatter

BEGIN = "<!-- BEGIN GENERATED - bin/build-manifest.py - do not edit -->"
END = "<!-- END GENERATED -->"


@dataclasses.dataclass(frozen=True)
class Entry:
    path: str
    governs: frontmatter.Governs


def collect(docs_dir: pathlib.Path) -> list[Entry]:
    entries: list[Entry] = []
    for md in sorted(docs_dir.rglob("*.md")):
        governs = frontmatter.parse(md.read_text())
        if governs is None:
            continue
        entries.append(Entry(md.relative_to(docs_dir).as_posix(), governs))
    return sorted(entries, key=lambda e: e.path)


def _matches(pattern: str, touched: str) -> bool:
    """Glob match where `**` spans directory separators.

    fnmatch already treats `*` as crossing `/`, so `libs/domain/**` matches
    `libs/domain/a/b/c.rs`. Normalising a trailing `**` to `*` keeps a bare
    `libs/domain/**` matching the directory's direct children too.
    """
    return fnmatch.fnmatchcase(touched, pattern) or fnmatch.fnmatchcase(
        touched, pattern.rstrip("*") + "*"
    )


def route(
    entries: list[Entry], touched: list[str], shapes: list[str]
) -> list[Entry]:
    hits: dict[str, Entry] = {}
    wanted = set(shapes)
    for entry in entries:
        by_path = any(
            _matches(p, t) for p in entry.governs.paths for t in touched
        )
        by_shape = bool(wanted & set(entry.governs.shapes))
        if by_path or by_shape:
            hits[entry.path] = entry
    return [hits[k] for k in sorted(hits)]


def _cell(values: list[str]) -> str:
    return ", ".join(f"`{v}`" for v in values) if values else "—"


def render(entries: list[Entry]) -> str:
    lines = [
        "# Docs manifest",
        "",
        "Generated from each doc's `governs:` frontmatter. Do not hand-edit "
        "the block below — edit the doc and regenerate.",
        "",
        BEGIN,
        "",
        "| Doc | Governs paths | Shapes | Verify | Status |",
        "|---|---|---|---|---|",
    ]
    for e in entries:
        lines.append(
            f"| `{e.path}` | {_cell(e.governs.paths)} | "
            f"{_cell(e.governs.shapes)} | {e.governs.verify} | "
            f"{e.governs.status or '—'} |"
        )
    lines += ["", END, ""]
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bin/run-tests.py -v`
Expected: PASS — 13 tests total, OK

- [ ] **Step 5: Commit**

```bash
git add docsbase/manifest.py tests/test_manifest.py
git commit -m "feat: build the docs manifest and route changes to governing docs"
```

---

### Task 4: The `build-manifest` CLI

**Files:**
- Create: `bin/build-manifest.py`
- Test: `tests/test_build_manifest_cli.py`

**Interfaces:**
- Consumes: `manifest.collect`, `manifest.render`, `manifest.BEGIN`/`END` from Task 3
- Produces:
  - `build(root: pathlib.Path) -> str` — the manifest text for a repo root
  - `check(root: pathlib.Path) -> bool` — `True` when `docs/MANIFEST.md` matches what would be generated
  - CLI: `bin/build-manifest.py` writes; `bin/build-manifest.py --check` exits 1 on drift

- [ ] **Step 1: Write the failing test**

`tests/test_build_manifest_cli.py`:

```python
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "build_manifest", ROOT / "bin" / "build-manifest.py"
)
build_manifest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_manifest)


class TestCli(unittest.TestCase):
    def _repo(self, tmp):
        root = pathlib.Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "architecture.md").write_text(
            "---\ngoverns:\n  paths: [src/**]\n---\n# A\n"
        )
        return root

    def test_build_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            build_manifest.write(root)
            text = (root / "docs" / "MANIFEST.md").read_text()
            self.assertIn("architecture.md", text)

    def test_check_passes_when_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            build_manifest.write(root)
            self.assertTrue(build_manifest.check(root))

    def test_check_fails_when_a_doc_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            build_manifest.write(root)
            (root / "docs" / "design.md").write_text(
                "---\ngoverns:\n  paths: [ui/**]\n---\n# D\n"
            )
            self.assertFalse(build_manifest.check(root))

    def test_check_fails_when_manifest_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            self.assertFalse(build_manifest.check(root))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/run-tests.py -v`
Expected: FAIL — `FileNotFoundError` for `bin/build-manifest.py`

- [ ] **Step 3: Write minimal implementation**

`bin/build-manifest.py`:

```python
#!/usr/bin/env python3
"""Generate docs/MANIFEST.md from each doc's `governs:` frontmatter.

Usage:
    bin/build-manifest.py           write the manifest
    bin/build-manifest.py --check   exit 1 if it is out of date
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from docsbase import manifest  # noqa: E402

MANIFEST = pathlib.Path("docs") / "MANIFEST.md"


def build(root: pathlib.Path) -> str:
    return manifest.render(manifest.collect(root / "docs"))


def write(root: pathlib.Path) -> None:
    (root / MANIFEST).write_text(build(root))


def check(root: pathlib.Path) -> bool:
    target = root / MANIFEST
    if not target.exists():
        return False
    return target.read_text() == build(root)


def main(argv: list[str]) -> int:
    root = pathlib.Path.cwd()
    if not (root / "docs").is_dir():
        print("no docs/ directory here", file=sys.stderr)
        return 1
    if "--check" in argv:
        if check(root):
            print("ok - manifest is current")
            return 0
        print(
            "DRIFT - docs/MANIFEST.md is out of date. "
            "Run bin/build-manifest.py",
            file=sys.stderr,
        )
        return 1
    write(root)
    print(f"wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `chmod +x bin/build-manifest.py && bin/run-tests.py -v`
Expected: PASS — 17 tests total, OK

- [ ] **Step 5: Commit**

```bash
git add bin/build-manifest.py tests/test_build_manifest_cli.py
git commit -m "feat: add build-manifest CLI with a --check drift gate"
```

---

### Task 5: The detector table and fact derivation

**Files:**
- Create: `docsbase/detectors.toml`
- Create: `docsbase/detect.py`
- Create: `bin/derive-facts.py`
- Test: `tests/test_detect.py`

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces:
  - `QUESTIONS` — the fixed tuple `("units", "gate-commands", "pre-commit-automation", "dependency-manifests")`
  - `Fact` — dataclass with `question: str`, `value: str`, `source: str` (the file it was quoted from)
  - `derive(root: pathlib.Path, table: list[dict] | None = None) -> tuple[list[Fact], list[str]]` — returns facts and the list of questions that went **underived**
  - `load_table() -> list[dict]` — reads `docsbase/detectors.toml`
  - CLI: `bin/derive-facts.py` prints facts grouped by question, then the underived list

- [ ] **Step 1: Write the failing test**

`tests/test_detect.py`:

```python
import pathlib
import tempfile
import unittest

from docsbase import detect


class TestDerive(unittest.TestCase):
    def test_zero_matches_still_works_and_reports_underived(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts, underived = detect.derive(pathlib.Path(tmp))
            self.assertEqual(facts, [])
            self.assertEqual(set(underived), set(detect.QUESTIONS))

    def test_detects_a_glob_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / ".husky").mkdir()
            (root / ".husky" / "pre-commit").write_text("just check\n")
            facts, underived = detect.derive(root)
            hooks = [f for f in facts
                     if f.question == "pre-commit-automation"]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(hooks[0].value, "pre-commit")
            self.assertEqual(hooks[0].source, ".husky/pre-commit")
            self.assertNotIn("pre-commit-automation", underived)

    def test_detects_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text(
                '{"scripts": {"test": "vitest", "build": "tsc"}}'
            )
            facts, _ = detect.derive(root)
            values = {f.value for f in facts
                      if f.question == "gate-commands"}
            self.assertEqual(values, {"test", "build"})

    def test_a_detector_never_infers_from_an_unreadable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text("{ this is not json")
            facts, underived = detect.derive(root)
            self.assertEqual(
                [f for f in facts if f.question == "gate-commands"], []
            )
            self.assertIn("gate-commands", underived)

    def test_every_shipped_detector_names_a_known_question(self):
        for row in detect.load_table():
            self.assertIn(row["question"], detect.QUESTIONS)

    def test_every_fact_can_quote_its_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Justfile").write_text("check:\n\techo hi\n")
            facts, _ = detect.derive(root)
            for f in facts:
                self.assertTrue(f.source)
                self.assertTrue((root / f.source.split(":")[0]).exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/run-tests.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsbase.detect'`

- [ ] **Step 3: Write the detector table**

`docsbase/detectors.toml`:

```toml
# Detectors are DATA. Adding an ecosystem is a change to this file only.
#
# Rules, enforced by tests:
#   - `question` must be one of docsbase.detect.QUESTIONS
#   - a detector extracts only what it can quote literally from a file
#   - nothing here is required; zero matches is a valid, working run
#
# extract:
#   "glob-names"  file names matched by `when`
#   "json-keys"   keys at `pointer` in a JSON file
#   "line-prefix" lines in `when` matching `pattern`, first capture group

[[detector]]
question = "pre-commit-automation"
when = ".husky/*"
extract = "glob-names"

[[detector]]
question = "pre-commit-automation"
when = ".pre-commit-config.yaml"
extract = "glob-names"

[[detector]]
question = "pre-commit-automation"
when = "lefthook.yml"
extract = "glob-names"

[[detector]]
question = "pre-commit-automation"
when = ".git/hooks/*"
extract = "glob-names"

[[detector]]
question = "gate-commands"
when = "package.json"
extract = "json-keys"
pointer = "scripts"

[[detector]]
question = "gate-commands"
when = "Justfile"
extract = "line-prefix"
pattern = "^([a-zA-Z][a-zA-Z0-9_-]*):"

[[detector]]
question = "gate-commands"
when = "Makefile"
extract = "line-prefix"
pattern = "^([a-zA-Z][a-zA-Z0-9_-]*):"

[[detector]]
question = "gate-commands"
when = "Taskfile.yml"
extract = "glob-names"

[[detector]]
question = "units"
when = "pnpm-workspace.yaml"
extract = "glob-names"

[[detector]]
question = "units"
when = "Cargo.toml"
extract = "glob-names"

[[detector]]
question = "units"
when = "go.work"
extract = "glob-names"

[[detector]]
question = "units"
when = "settings.gradle"
extract = "glob-names"

[[detector]]
question = "dependency-manifests"
when = "package.json"
extract = "glob-names"

[[detector]]
question = "dependency-manifests"
when = "Cargo.toml"
extract = "glob-names"

[[detector]]
question = "dependency-manifests"
when = "pyproject.toml"
extract = "glob-names"

[[detector]]
question = "dependency-manifests"
when = "go.mod"
extract = "glob-names"

[[detector]]
question = "dependency-manifests"
when = "pom.xml"
extract = "glob-names"
```

- [ ] **Step 4: Write minimal implementation**

`docsbase/detect.py`:

```python
"""Answer stack-agnostic questions about a repo from a data-driven table.

The QUESTIONS are the interface and are fixed. The detectors that answer
them are data (detectors.toml) so that adding an ecosystem never touches
this file. No ecosystem is privileged and none is required: a repo matching
zero detectors produces zero facts and four underived questions, which is a
valid run - the skill asks instead.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import tomllib

QUESTIONS = (
    "units",
    "gate-commands",
    "pre-commit-automation",
    "dependency-manifests",
)

TABLE_PATH = pathlib.Path(__file__).parent / "detectors.toml"


@dataclasses.dataclass(frozen=True)
class Fact:
    question: str
    value: str
    source: str


def load_table() -> list[dict]:
    return tomllib.loads(TABLE_PATH.read_text())["detector"]


def _glob(root: pathlib.Path, when: str) -> list[pathlib.Path]:
    return sorted(p for p in root.glob(when) if p.is_file())


def _extract(root: pathlib.Path, row: dict) -> list[Fact]:
    """Return facts, quoting each from a real file. Never infers."""
    kind = row["extract"]
    out: list[Fact] = []
    for path in _glob(root, row["when"]):
        rel = path.relative_to(root).as_posix()
        if kind == "glob-names":
            out.append(Fact(row["question"], path.name, rel))
        elif kind == "json-keys":
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue  # unreadable: report nothing rather than guess
            section = data.get(row["pointer"])
            if isinstance(section, dict):
                out += [Fact(row["question"], k, rel) for k in section]
        elif kind == "line-prefix":
            try:
                text = path.read_text()
            except OSError:
                continue
            pattern = re.compile(row["pattern"], re.M)
            out += [
                Fact(row["question"], m.group(1), rel)
                for m in pattern.finditer(text)
            ]
    return out


def derive(
    root: pathlib.Path, table: list[dict] | None = None
) -> tuple[list[Fact], list[str]]:
    rows = load_table() if table is None else table
    facts: list[Fact] = []
    for row in rows:
        facts += _extract(root, row)
    answered = {f.question for f in facts}
    underived = [q for q in QUESTIONS if q not in answered]
    return facts, underived
```

`bin/derive-facts.py`:

```python
#!/usr/bin/env python3
"""Report what can be derived about this repo, and what cannot.

Usage: bin/derive-facts.py [path]
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from docsbase import detect  # noqa: E402


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[0] if argv else ".").resolve()
    facts, underived = detect.derive(root)

    for question in detect.QUESTIONS:
        hits = [f for f in facts if f.question == question]
        print(f"\n## {question}")
        if not hits:
            print("  underived - ask instead")
            continue
        for f in hits:
            print(f"  {f.value:30} <- {f.source}")

    if underived:
        print(f"\nUNDERIVED ({len(underived)}): {', '.join(underived)}")
        print("These must be asked, and recorded as answers - never guessed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `chmod +x bin/derive-facts.py && bin/run-tests.py -v`
Expected: PASS — 23 tests total, OK

- [ ] **Step 6: Sanity-check against a real repo**

Run: `bin/derive-facts.py ~/Workspace/nyayvaani`
Expected: `gate-commands` lists Justfile recipes quoted from `Justfile`; `pre-commit-automation` lists the husky hook files. Confirm every printed source path exists. This is a spot check, not an assertion — record what it printed in the commit message if anything looks wrong.

- [ ] **Step 7: Commit**

```bash
git add docsbase/detect.py docsbase/detectors.toml bin/derive-facts.py tests/test_detect.py
git commit -m "feat: derive repo facts from a data-driven detector table"
```

---

### Task 6: The `doc-scaffold` skill

Prose, not code — so it is verified by a pressure scenario rather than a unit test, per `superpowers:writing-skills`.

**Files:**
- Create: `skills/doc-scaffold/SKILL.md`
- Modify: `.claude-plugin/marketplace.json` (nothing — version bump happens in Task 7)

**Interfaces:**
- Consumes: `bin/derive-facts.py` (Task 5), `bin/build-manifest.py` (Task 4)
- Produces: `/doc-scaffold`, which leaves behind `docs/architecture.md`, `docs/product.md`, `docs/decisions.md` and a current `docs/MANIFEST.md`

- [ ] **Step 1: Write the baseline pressure scenario**

Create `tests/scenarios/doc-scaffold-baseline.md` — this is the RED step and is not a unit test:

```markdown
# Baseline scenario (run WITHOUT the skill)

Dispatch a subagent with this prompt against a repo that has no docs/:

> Set up documentation for this repository so an AI agent can work in it
> effectively. Be thorough.

Record verbatim:
1. Did it invent facts it could not read from the tree (a build command
   that does not exist, an app that is not there)?
2. Did it produce empty or TODO-filled sections?
3. Did it ask anything, or assume everything?
4. Did it impose a directory structure the repo has no need for?

These four are the failures the skill must prevent. Capture the exact
wording of any invented fact - that is what the skill's counters target.
```

- [ ] **Step 2: Run the baseline and record the results**

Dispatch the subagent described above against a scratch copy of a small repo with no `docs/`. Append the verbatim findings to the scenario file under a `## Baseline results (YYYY-MM-DD)` heading. Do not write the skill before this is recorded — an untested skill is a guess.

- [ ] **Step 3: Write the skill**

`skills/doc-scaffold/SKILL.md`:

```markdown
---
name: doc-scaffold
description: Use when a repository has no docs manifest and the issue-to-PR pipeline refuses to run, or when a repo's documentation has never been organised into a structure an agent can route through.
---

# doc-scaffold — bootstrap a repo's docs baseline

Runs **once per repo**. Ends when `docs/MANIFEST.md` exists and `/ship` will run.

## The rule that matters most

**Derive what can be derived. Ask for the rest. Never guess.**

Anything neither derived nor answered is written as **"not recorded"**.

A confident wrong claim in an authoritative doc is the worst output of this
skill — worse than an admitted gap, because the manifest tells every future
agent to trust it. If you cannot quote a fact from a file or from the user,
you do not have it.

## Step 1 — Derive

```bash
bin/derive-facts.py
```

Read what it found and, just as carefully, what it lists as UNDERIVED. Every
fact it prints carries the file it was quoted from. Facts it did not find are
questions for Step 2, never assumptions.

Also derive whether specs and plans are tracked:

```bash
git check-ignore docs/superpowers && echo ignored || echo tracked
```

## Step 2 — Ask

Ask one at a time. These cannot be read off a source tree:

1. **Why does this exist, and who is it for?** → `docs/product.md`
2. **What will the code teach an agent wrong?** → the traps section. Highest
   value per question asked; press for specifics.
3. **What was considered and deliberately rejected?** → `docs/decisions.md`
4. **What is deliberately deferred?**

For anything the derive step marked UNDERIVED, ask directly rather than
inspecting the tree yourself and calling the result derived.

## Step 3 — Write the required core

Three files, always:

| File | Carries |
|---|---|
| `docs/architecture.md` | the placement table — where new code goes |
| `docs/product.md` | why it exists, who for, what is out of scope |
| `docs/decisions.md` | the ADR log, append-only |

Each gets `governs:` frontmatter:

```yaml
---
governs:
  paths: [src/**]
  shapes: [placement]
---
```

`docs/product.md` sets `verify: ask` — nothing about a product can be checked
against a source tree.

## Step 4 — Offer, do not impose

Offer these only when the derive step found the trigger:

| Found | Offer |
|---|---|
| more than one buildable unit | `docs/<units>/<name>.md` |
| deploy or infra config | `docs/ops/` |
| a public-facing surface | `docs/design.md` |
| billing or entitlement code | `docs/product/pricing.md` |
| a published API surface | `docs/product/api-spec.md` |

**Never scaffold a directory because another repo has one.** An empty doc
behind an authoritative manifest is worse than no doc.

## Step 5 — Generate and verify

```bash
bin/build-manifest.py
bin/build-manifest.py --check
```

Report the manifest, and say plainly which sections are "not recorded".

## Red flags — stop and ask instead

- Writing a build command you have not seen in a file
- Filling a section because the template has it
- "The repo probably uses..." / "Standard practice here would be..."
- Copying a structure from another project
- A doc with a heading and no content behind an authoritative manifest
```

- [ ] **Step 4: Re-run the scenario WITH the skill**

Dispatch the same subagent prompt with the skill available. Expected: no invented facts, "not recorded" where information is missing, questions asked rather than assumed, and no unrequested directories. Append the results to the scenario file under `## With-skill results (YYYY-MM-DD)`.

- [ ] **Step 5: Close any new loophole**

If the subagent found a new rationalization, add an explicit counter to the Red flags list and re-run. Repeat until it complies. Record each iteration in the scenario file.

- [ ] **Step 6: Verify the frontmatter contract**

Run:
```bash
python3 - <<'PY'
import pathlib, re, sys
f = pathlib.Path("skills/doc-scaffold/SKILL.md")
fm = re.match(r"^---\n(.*?)\n---\n", f.read_text(), re.S).group(1)
name = re.search(r"^name:\s*(.+)$", fm, re.M).group(1).strip()
desc = re.search(r"^description:\s*(.+)$", fm, re.M).group(1).strip()
assert name == "doc-scaffold", name
assert desc.startswith("Use when"), desc
assert len(fm) <= 1024
print("ok")
PY
```
Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add skills/doc-scaffold tests/scenarios
git commit -m "feat: add doc-scaffold skill with baseline scenario results"
```

---

### Task 7: Rewrite `ship` Stage 0 and the Verify doc rule

**Files:**
- Modify: `skills/ship/SKILL.md` (Stage 0.2, and the "Stale docs" paragraph in Stage 3.1)
- Modify: `skills/auto/SKILL.md` (Step 1, add the manifest precondition)
- Modify: `README.md` (replace the "Where project rules come from" section)
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `gemini-extension.json` (version → `0.2.0`)

**Interfaces:**
- Consumes: `docs/MANIFEST.md` produced by Task 6's skill
- Produces: nothing later tasks depend on — this is the final task

- [ ] **Step 1: Replace Stage 0.2 in `skills/ship/SKILL.md`**

Replace the whole `### 0.2 Load the project rules` section (currently the `*-rules` → `CLAUDE.md` → ask lookup) with:

```markdown
### 0.2 Load the docs manifest

```bash
cat docs/MANIFEST.md
bin/build-manifest.py --check
```

| Result | Action |
|---|---|
| No `docs/MANIFEST.md` | **STOP.** "No docs manifest. Run `/doc-scaffold` first." |
| `--check` reports DRIFT | **STOP.** "Manifest is stale. Run `bin/build-manifest.py`." |
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
```

- [ ] **Step 2: Replace the stale-docs paragraph in Stage 3.1**

Find the paragraph beginning `**Stale docs are a note, never a FAIL.**` and replace it with:

```markdown
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
```

- [ ] **Step 3: Add the precondition to `skills/auto/SKILL.md`**

Insert immediately before `## Step 1 — List open unassigned issues`:

```markdown
## Step 0 — Precondition

`auto` hands to `ship`, which requires a docs manifest. If `docs/MANIFEST.md`
is absent, stop and say: "No docs manifest — run `/doc-scaffold` before
picking an issue." Do not rank issues you cannot then ship.
```

- [ ] **Step 4: Update the README section**

Replace the whole `## Where project rules come from` section with:

```markdown
## Where project rules come from

`ship` carries no project rules. Stage 0 reads `docs/MANIFEST.md` — generated
from each doc's `governs:` frontmatter — and routes the change to the docs
that govern it.

**There is no fallback.** With no manifest, `ship` and `auto` stop and hand
off to `/doc-scaffold`. Project rules were measured to be missing from every
`CLAUDE.md` they were supposed to live in, so a degraded mode would only
guess more confidently.

```bash
/doc-scaffold           # once per repo: derive, ask, generate
bin/build-manifest.py   # regenerate after editing a doc's governs: block
bin/build-manifest.py --check   # drift gate, belongs in CI
```
```

- [ ] **Step 5: Bump the version everywhere**

Run:
```bash
bin/check-versions.py 0.2.0 && bin/check-versions.py
```
Expected: `set 5 manifests to 0.2.0`, then all five listed at `0.2.0` and `ok`.

- [ ] **Step 6: Verify the whole repo**

Run:
```bash
bin/run-tests.py && claude plugin validate . && bin/check-versions.py
```
Expected: tests OK, `Validation passed`, versions ok. All three must pass before committing.

- [ ] **Step 7: Confirm no stale cross-reference survives**

Run:
```bash
grep -rn "\-rules/SKILL.md\|\*-rules skill" skills/ README.md AGENTS.md
```
Expected: **no output.** The `*-rules` lookup is dropped by this plan; any surviving reference is a stale instruction that will send an agent to a file that does not exist.

- [ ] **Step 8: Commit**

```bash
git add skills README.md .claude-plugin .codex-plugin .cursor-plugin gemini-extension.json
git commit -m "feat!: ship Stage 0 reads the docs manifest, with no fallback

BREAKING: ship and auto now refuse to run without docs/MANIFEST.md.
Run /doc-scaffold once per repo to produce one."
```

---

## Self-review

**Spec coverage.** Decision 1 (generated routing) → Tasks 2–4. Decision 2 (hard block) → Task 7 Step 1. Decision 3 (derive then ask) → Tasks 5–6. Decision 4 (contradiction vs gap) → Task 7 Step 2. Decision 6 (detectors as data) → Task 5. `product.md` in the required core → Task 6 Step 3. Optional `status:` → Tasks 2, 3 and Task 7 Step 1. Decision 5 (`doc-refresh`) is deliberately Plan 2 and appears nowhere here, as the spec requires.

**Known gap, carried deliberately:** the spec's always-ask *verification* behaviour ("report unverifiable from source — last confirmed `<date>`") belongs to `doc-refresh` and is Plan 2. Plan 1 only records `verify: ask` in the frontmatter so Plan 2 has something to read.

**Type consistency.** `frontmatter.Governs(paths, shapes, verify, status)` is constructed positionally in `tests/test_manifest.py`'s `_g()` helper and matches the dataclass field order in Task 2. `manifest.Entry(path, governs)` is used consistently in Tasks 3 and 4. `detect.Fact(question, value, source)` is constructed positionally in Task 5's implementation and read by field name in its tests. `build_manifest.write()` / `.check()` are the names the Task 4 tests call.

**Test counts** in the "Expected" lines are cumulative across tasks (6 → 13 → 17 → 23) and assume tasks run in order. If a task is run standalone, the count differs — the pass/fail result is what matters, not the number.
