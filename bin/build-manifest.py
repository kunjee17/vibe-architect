#!/usr/bin/env python3
"""Generate docs/MANIFEST.md from each doc's `governs:` frontmatter.

Invoke by absolute path; the working directory decides which repo is read.
${CLAUDE_PLUGIN_ROOT} is set by the plugin runtime. From a clone, use the
clone's absolute path -- do not cd into the clone to run it against another
repo, or you will operate on the clone's own docs instead.

Usage:
    ${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py           write the manifest
    ${CLAUDE_PLUGIN_ROOT}/bin/build-manifest.py --check   exit 1 if it is out of date
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from docsbase import frontmatter, manifest  # noqa: E402

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


def state(root: pathlib.Path) -> str:
    """One of: "absent", "empty", "stale", "current"."""
    target = root / MANIFEST
    if not target.exists():
        return "absent"
    current = build(root)
    if target.read_text() != current:
        return "stale"
    if not manifest.collect(root / "docs"):
        return "empty"
    return "current"


def main(argv: list[str]) -> int:
    root = pathlib.Path.cwd()
    if not (root / "docs").is_dir():
        print("no docs/ directory here", file=sys.stderr)
        return 1
    try:
        if "--check" in argv:
            result = state(root)
            if result == "current":
                print("ok - manifest is current")
                return 0
            if result == "absent":
                print(
                    "ABSENT - no docs/MANIFEST.md. Run /doc-scaffold",
                    file=sys.stderr,
                )
                return 1
            if result == "empty":
                print(
                    "EMPTY - docs/MANIFEST.md exists but no doc carries "
                    "governs: frontmatter. Run /doc-scaffold",
                    file=sys.stderr,
                )
                return 1
            print(
                "DRIFT - docs/MANIFEST.md is out of date. "
                "Run bin/build-manifest.py",
                file=sys.stderr,
            )
            return 1
        write(root)
    except frontmatter.ParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
