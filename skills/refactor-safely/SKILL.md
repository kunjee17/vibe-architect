---
name: refactor-safely
description: Use when renaming a symbol across a codebase, removing dead code, or restructuring a module and the full set of affected call sites is not yet known.
---

# refactor-safely

Plan and execute refactors from dependency analysis, not from search-and-replace.

## Steps

1. `refactor_tool` with `mode="suggest"` — community-driven refactoring candidates.
2. `refactor_tool` with `mode="dead_code"` — unreferenced code.
3. For renames, `refactor_tool` with `mode="rename"` to **preview** every affected location.
4. `apply_refactor_tool` with the `refactor_id` to apply.
5. `detect_changes_tool` afterwards to verify the impact matched the preview.

## Safety checks

- **Always preview before applying.** Rename mode returns an edit list; read it.
- `get_impact_radius_tool` before any major restructure.
- `get_affected_flows_tool` to confirm no critical path broke.
- `find_large_functions_tool` to pick decomposition targets.
- A refactor changes structure, never behaviour. If the test suite needed edits to pass,
  it was not a refactor — stop and say so.

## Token efficiency

- **Always start with `get_minimal_context(task="<your task>")`** before any other graph tool.
- Use `detail_level="minimal"` on every call. Escalate only when minimal is insufficient.
- Target: ≤5 tool calls, ≤800 total output tokens.
