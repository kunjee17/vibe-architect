---
name: debug-issue
description: Use when tracing the cause of a bug, test failure or unexpected behaviour and the responsible code path is not yet known.
---

# debug-issue

Trace a defect through the code graph instead of grepping for symptoms.

**Note:** for the *discipline* of debugging — reproduce, hypothesise, isolate before fixing —
use `superpowers:systematic-debugging`. This skill is the navigation half.

## Steps

1. `semantic_search_nodes_tool` — find code related to the symptom.
2. `query_graph_tool` with `callers_of` and `callees_of` — trace the call chain both ways.
3. `get_flow_tool` — full execution paths through the suspected area.
4. `detect_changes_tool` — check whether a recent change caused it.
5. `get_impact_radius_tool` on suspected files — what else is affected.

## Tips

- Check callers *and* callees; one direction alone hides the context.
- Affected flows point at the entry point that triggers the bug.
- Recent changes are the most common source of new failures.

## Token efficiency

- **Always start with `get_minimal_context(task="<your task>")`** before any other graph tool.
- Use `detail_level="minimal"` on every call. Escalate only when minimal is insufficient.
- Target: ≤5 tool calls, ≤800 total output tokens.
