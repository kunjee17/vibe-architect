---
name: review-changes
description: Use when assessing a diff, branch or pull request for risk and test coverage before it merges.
---

# review-changes

A risk-aware review driven by change detection and blast radius. Requires the
`code-review-graph` MCP server; without it, fall back to Serena's symbol tools, then
plain file search.

**Note:** this skill is graph-based risk and coverage triage; `superpowers:requesting-code-review`
and this plugin's `code-review` skill are the fresh-eyes review passes. They compose
rather than compete.

## Steps

1. `detect_changes_tool` — risk-scored change analysis.
2. `get_affected_flows_tool` — impacted execution paths.
3. For each high-risk function, `query_graph_tool` with `pattern="tests_for"` — coverage.
4. `get_impact_radius_tool` — blast radius.
5. For anything untested, propose specific test cases.

## Output format

Group findings by risk level (high / medium / low). For each:

- What changed and why it matters
- Test coverage status
- Suggested improvement
- Overall merge recommendation

Do not flag what the project's linter already catches. A conscious trade-off carrying a
code comment is a note, not a finding.

## Token efficiency

- **Always start with `get_minimal_context_tool(task="<your task>")`** before any other graph tool.
- Use `detail_level="minimal"` on every call. Escalate only when minimal is insufficient.
- Target: ≤5 tool calls, ≤800 total output tokens.
- Read the implementation and its tests before changing code — the graph narrows scope,
  it does not replace the source.
