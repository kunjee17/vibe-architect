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
