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
    """Glob match where `*` already spans directory separators.

    fnmatch treats `*` as crossing `/`, so `libs/domain/**` and
    `libs/domain/*` are equivalent and both match `libs/domain/a/b/c.rs`.
    The second call exists only for a pattern written as a bare directory
    name with no glob suffix: `libs/domain` should match everything under
    `libs/domain/`, but must NOT match the sibling `libs/domain-other/`.
    Appending `/*` rather than `*` is what enforces that boundary.
    """
    return fnmatch.fnmatchcase(touched, pattern) or fnmatch.fnmatchcase(
        touched, pattern.rstrip("/*") + "/*"
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
