#!/usr/bin/env python3
"""Every manifest carries the version independently. Fail loudly when they drift.

Usage:  bin/check-versions.py            # verify
        bin/check-versions.py 0.2.0      # set all manifests to 0.2.0
"""
import json
import pathlib
import sys

MANIFESTS = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    "gemini-extension.json",
]
MARKETPLACE = ".claude-plugin/marketplace.json"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(rel):
    return json.loads((ROOT / rel).read_text())


def save(rel, data):
    (ROOT / rel).write_text(json.dumps(data, indent=2) + "\n")


def versions():
    found = {rel: load(rel)["version"] for rel in MANIFESTS}
    mkt = load(MARKETPLACE)
    for plugin in mkt["plugins"]:
        found[f"{MARKETPLACE}:{plugin['name']}"] = plugin["version"]
    return found


def main():
    if len(sys.argv) > 2:
        sys.exit(__doc__)

    if len(sys.argv) == 2:
        target = sys.argv[1]
        for rel in MANIFESTS:
            data = load(rel)
            data["version"] = target
            save(rel, data)
        mkt = load(MARKETPLACE)
        for plugin in mkt["plugins"]:
            plugin["version"] = target
        save(MARKETPLACE, mkt)
        print(f"set {len(MANIFESTS) + 1} manifests to {target}")
        return

    found = versions()
    distinct = set(found.values())
    for rel, v in found.items():
        print(f"  {v:10} {rel}")
    if len(distinct) == 1:
        print(f"\nok — all manifests at {distinct.pop()}")
        return
    print(f"\nDRIFT: {len(distinct)} distinct versions {sorted(distinct)}")
    sys.exit(1)


if __name__ == "__main__":
    main()
