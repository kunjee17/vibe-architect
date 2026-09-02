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
        elif kind == "toml-list":
            try:
                data = tomllib.loads(path.read_text())
            except (tomllib.TOMLDecodeError, OSError):
                continue  # unreadable: report nothing rather than guess
            node = data
            for part in row["pointer"].split("."):
                if not isinstance(node, dict):
                    node = None
                    break
                node = node.get(part)
            if isinstance(node, list):
                out += [Fact(row["question"], str(v), rel) for v in node]
        else:
            raise ValueError(
                f"unknown extract kind {kind!r} in detectors.toml"
            )
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
