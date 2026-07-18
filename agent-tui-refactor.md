
# Agent → Events Refactor Plan for `terminal_io`

## Goal

Remove all direct references to an `Agent` object from `harness_core/terminal_io`. Currently, the TUI layer holds a live reference to the `Agent` instance (via `tui_app.py::TextualHarnessApp._agent`, `widgets.py::TaskListSidebar._agent`) and reads state directly off it (`task_list`, `_agent_type.model_name`). The refactor replaces these direct reads with an event-driven model: all agent-related UI updates flow through existing or new `EventPayload` types on the EventBus.

## Current State (Findings)

### Where `agent` is referenced in `terminal_io/`:

| File | Reference Type | Details |
|------|---------------|---------|
| `tui_app.py:72–74` | **Direct Agent reference** | `TextualHarnessApp.__init__(self, agent=None)` stores `self._agent = agent`. This is the root of all agent coupling. |
| `tui_app.py:169–170` | Passes agent to sidebar | `sidebar.set_agent(self._agent)` in `on_mount()` |
| `tui_app.py:185–189` | Uses agent.id for event filter | `subscribe_event_listener(self._agent.id)` — currently the only agent-derived value used here. Can be replaced by a "TUI_READY" or similar bootstrap event that carries the agent_id. |
| `tui_app.py:203, 208` | Calls agent.loop() directly | `_start_loop()` guards on `self._agent is None` and calls `self._agent.loop(on_exit=...)`. This is how the TUI drives the main loop. |
| `widgets.py:63–68` | **Direct Agent reference** | `TaskListSidebar.__init__()` has `self._agent = None`; `set_agent(agent)` stores it. |
| `widgets.py:78–86` | Reads `_agent._agent_type.model_name` | `_get_model_name()` traverses the agent object to get model name. Called from both refresh paths (lines 96, 140). |
| `widgets.py:117–122` | Reads `self._agent.task_list` directly | `refresh_tasks()` polls the live task list. This is a polling pattern that duplicates what `TaskListPayload` events already provide via `event_listener.py`. |
| `display.py:37, 81, 93, 291–319` | "Agent" as string label only | Panel titles like `"Tool: {func_name}"`, `"Agent"`, `"🤖 Agent Response"` — these are cosmetic strings, no object reference. Safe to keep. |
| `event_listener.py:67–195` | Uses `agent_id` string (not Agent obj) | All handlers filter by sender regex pattern. No direct agent object access — only the string id. Safe as-is. |

### Where `agent` is referenced from OUTSIDE `terminal_io/`:

| File | Reference | Details |
|------|-----------|---------|
| `__main__.py:245` | `launch(agent)` | Passes full Agent instance to TUI entry point. Must be changed to pass only the agent's id string (or a bootstrap event payload). |
| `harness_tui.py::show_spinner/hide_spinner` | No direct agent ref | Methods are named for "agent busy" but operate on widget state only. Safe as-is. |

### What is ALREADY event-driven (no changes needed):

- **Tool calls/results/errors**: Already driven by `agent.tool.call`, `agent.tool.result`, `agent.tool.error` events → `event_listener.py` handlers → `display_tool_call()` / `display_tool_result()`.
- **Task list updates**: Already driven by `agent.tasklist.initialize/update/reset` events → `update_sidebar_tasks_from_payload()`. The sidebar has both a polling path (`refresh_tasks`) AND an event-driven path (`refresh_tasks_from_payload`). After refactor, only the event-driven path should remain.
- **Turn stats/responses/errors/ready**: Already driven by their respective `agent.*` events.

## Refactor Plan (5 Steps)

### Step 1: Remove `Agent` object from `TextualHarnessApp.__init__()` and `launch()`

**Files:** `tui_app.py`, `harness_tui.py`, `__main__.py`

- Change `TextualHarnessApp.__init__(self, agent=None)` → `TextualHarnessApp.__init__(self, agent_id: str | None = None)`. Store only `self._agent_id: str | None`.
- Remove `self._agent.loop(on_exit=...)` call from `_start_loop()`. The main loop should be started by the caller (`__main__.py`) directly — the TUI should not own the agent lifecycle. Add a comment explaining that loop ownership lives in `__main__.py`.
- Change `launch(agent)` → `launch(agent_id: str | None = None)`. Pass only the id string.
- Update `__main__.py` to call `launch("Agent.main")` (or pass `agent._id`) instead of `launch(agent)`.

**Event-driven replacement for agent.id:** The existing `subscribe_event_listener(self._agent.id)` call in `on_mount()` is replaced by subscribing using the stored `self._agent_id` string. No new event needed — just pass the id as a constructor parameter.

### Step 2: Remove `_agent` from `TaskListSidebar` and eliminate polling-based refresh

**Files:** `widgets.py`, `task_display.py`

- Remove `self._agent = None` from `TaskListSidebar.__init__()`.
- Remove `set_agent(agent)` method entirely.
- Remove `_get_model_name()` — model name will come from events (see Step 3).
- Modify `refresh_tasks()` to remove all references to `self._agent.task_list`:
  - If no task list is available, show `_No tasks yet._` placeholder.
  - The sidebar should only ever render via the event-driven path (`refresh_tasks_from_payload`), so `refresh_tasks()` can be simplified or removed entirely.
- Remove the periodic `set_interval(1.0, sidebar.refresh_tasks)` from `tui_app.py:on_mount()`.

### Step 3: Add a `ModelInfoPayload` event and push model name via events

**Files:** `event_types.py`, `event_listener.py`, `widgets.py`

- Add a new payload class in `event_types.py`:
  ```python
  @dataclass(kw_only=True)
  class ModelInfoPayload(EventPayload):
      model_name: str = ""
  ```
- In the agent's startup flow (wherever `agent.status.ready` is published), include the model name. Either extend `SystemMessagePayload` with a `model` field (it already has one — see line 150) or add a dedicated event topic like `agent.model.info`. **Recommendation:** Use the existing `agent.status.ready` event which already carries `payload.model` in `SystemMessagePayload`. The TUI should consume this to set sidebar model text.
- In `event_listener.py::handle_agent_status_ready`, after calling `print_system()`, also push the model name to the sidebar via a new method:
  ```python
  get_tui().update_sidebar_model(payload.model)
  ```
  (This already exists — no code change needed here.)
- In `widgets.py::TaskListSidebar`, add a `_model_name` attribute and update the render logic in both refresh paths to use it. Remove the call to `_get_model_name()`.

### Step 4: Clean up remaining agent references in `display.py` comments/naming

**Files:** `display.py`

- The function `display_agent_response()` is named with "agent" but takes only string/data parameters — no Agent object reference. Rename to `display_response()` for consistency? **Recommendation: Keep as-is.** The name refers to the display theme (agent's response panel), not an object dependency. Renaming would require updating all call sites and tests, which is low-value churn.
- Similarly, keep `_combine_reasoning` naming as-is — it describes the UI layout pattern.

### Step 5: Update `harness_tui.py` — remove any agent lifecycle references

**Files:** `harness_tui.py`

- The controller (`HarnessTUI`) already has no direct agent reference (only `show_spinner()`/`hide_spinner()` methods named for the agent's busy state). Verify that `_start_loop()` in `tui_app.py` is removed or converted to a passive observer.
- Ensure `reset()` method doesn't reference any agent-specific cleanup.

## Verification Checklist

After implementing all steps:

1. ✅ `grep -r "self._agent" harness_core/terminal_io/` returns zero matches (excluding comments)
2. ✅ `grep -r "\.loop(" harness_core/terminal_io/` returns zero matches
3. ✅ `grep -r "set_agent\|get_tui.*\.id\b"` returns zero matches in terminal_io
4. ✅ All sidebar updates come from events (no polling via `refresh_tasks()`)
5. ✅ `__main__.py` no longer passes an Agent object to `launch()`
6. ✅ Existing tests (`test_terminal_io.py`, `test_tui.py`, `test_terminal_display.py`) still pass
7. ✅ The TUI still renders: tool calls/results, agent responses, task lists, model name, usage stats, spinner

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| `_start_loop()` removal breaks TUI startup | Ensure `__main__.py` calls `agent.loop()` directly if not already doing so. Check current flow — the agent loop is likely started by the dispatcher/session layer, not the TUI. |
| Sidebar model name might be delayed (event-driven) | The existing `SystemMessagePayload.model` field on `agent.status.ready` should fire before any tool calls, so timing is fine. |
| Periodic refresh removal might miss stale state | Event-driven updates are more reliable than polling; the heartbeat was a safety net that's no longer needed when events are guaranteed. |

## Files to Modify (Summary)

| File | Action |
|------|--------|
| `harness_core/terminal_io/tui_app.py` | Remove `_agent`, change constructor param, remove `_start_loop()`, remove periodic refresh |
| `harness_core/terminal_io/widgets.py` | Remove `_agent` from TaskListSidebar, remove polling-based `refresh_tasks()` logic, use event-driven model name |
| `harness_core/event_types.py` | Add `ModelInfoPayload` (optional — may reuse existing payload) |
| `harness_core/__main__.py` | Pass agent_id string to launch() instead of Agent object |
| `tests/test_tui.py`, `tests/test_terminal_io.py`, etc. | Update any tests that construct TextualHarnessApp with an agent parameter |

## Files NOT Modified (confirmed no changes needed)

- `harness_core/terminal_io/event_listener.py` — already event-driven, uses only string agent_id
- `harness_core/terminal_io/display.py` — only cosmetic "Agent" strings in panel titles
- `harness_core/terminal_io/harness_tui.py` — controller has no direct agent reference
- `harness_core/terminal_io/task_display.py` — rendering logic, no agent dependency
- `harness_core/agent/` — already decoupled from terminal_io

