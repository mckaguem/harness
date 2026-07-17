

## Aug 29, 2025 — Removed `harness_core.agent.tool_context` module

- `harness_core/agent/tool_context.py` and `tests/test_tool_context.py` were deleted: the module (`ToolContext`, `current_tool_context()`) was no longer imported or used anywhere in production code.
- The dispatcher now injects agent directly via signature introspection (no more `ctx`/`ToolContext` wrapping).
- `initialize_task_list.py` and `update_task_status.py` also lost their `ctx` parameter — they take `(agent, ...)` directly now.
- 5 orphaned wiki pages under `wiki/pages/harness_core_agent_tool_context*.md` were deleted (source module gone).
- 3 wiki pages were updated to remove stale ToolContext references:
  - `harness_core_tools_dispatcher_dispatch.md` — rewritten description paragraph
  - `harness_core_tools_initialize_task_list_initialize_task_list.md` — fixed signature block
  - `harness_core_tools_update_task_status_update_task_status.md` — fixed signature block
- Commit: `059f8a1` ("chore: remove unused tool_context module"). Not yet pushed.

This is a test to see if multiple tasks can be marked as in_progress at the same time.

This is a test to see if multiple tasks can be marked as in_progress at the same time.

This is a test to see if multiple tasks can be marked as in_progress at the same time.

This is a test to see if multiple tasks can be marked as in_progress at the same time.
