#!/usr/bin/env python3
"""Report what can be derived about this repo, and what cannot.

Invoke by absolute path; the working directory decides which repo is read.
${CLAUDE_PLUGIN_ROOT} is set by the plugin runtime. From a clone, use the
clone's absolute path -- do not cd into the clone to run it against another
repo, or you will operate on the clone's own docs instead.

Usage:
    ${CLAUDE_PLUGIN_ROOT}/bin/derive-facts.py [path]
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
