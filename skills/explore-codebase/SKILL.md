---
name: explore-codebase
description: Use when orienting in an unfamiliar codebase, mapping its architecture or module structure, or locating a function or class whose file you do not already know.
---

# explore-codebase

Navigate and understand a codebase through the code-review-graph tools rather than by
reading files. Requires the `code-review-graph` MCP server; without it, fall back to
Serena's symbol tools, then plain file search.

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
- Serena's `find_symbol` / `get_symbols_overview` are the symbol-level complement to the
  graph's structural view — pair them, don't pick one.

## Token efficiency

- **Always start with `get_minimal_context_tool(task="<your task>")`** before any other graph tool.
- Use `detail_level="minimal"` on every call. Escalate to `"standard"` only when minimal
  is genuinely insufficient.
- Target: finish in ≤5 tool calls and ≤800 total output tokens.
- Read the implementation and its tests before changing code — the graph narrows scope,
  it does not replace the source.
