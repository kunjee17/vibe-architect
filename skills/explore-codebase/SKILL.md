---
name: explore-codebase
description: Use when orienting in an unfamiliar codebase, mapping its architecture or module structure, or locating a function or class whose file you do not already know.
---

# explore-codebase

Navigate and understand a codebase through the code-review-graph tools rather than by
reading files.

## Steps

1. `list_graph_stats_tool` — overall codebase metrics.
2. `get_architecture_overview_tool` — high-level community structure.
3. `list_communities_tool` to find major modules, then `get_community_tool` for details.
4. `semantic_search_nodes_tool` — find specific functions or classes.
5. `query_graph_tool` with `callers_of`, `callees_of`, `imports_of` to trace relationships.
6. `list_flows_tool` / `get_flow_tool` — execution paths.

## Tips

- Start broad (stats, architecture), then narrow.
- `children_of` on a file lists all its functions and classes.
- `find_large_functions_tool` surfaces complexity hotspots.

## Token efficiency

- **Always start with `get_minimal_context(task="<your task>")`** before any other graph tool.
- Use `detail_level="minimal"` on every call. Escalate to `"standard"` only when minimal
  is genuinely insufficient.
- Target: finish in ≤5 tool calls and ≤800 total output tokens.
