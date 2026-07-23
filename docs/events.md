# Harness Event Topics Reference

> **Auto-generated catalog.** Every event topic used by `harness_core/` and where it lives in code. Last updated: 2026-04-15.

## Table of Contents

- [Overview](#overview)
- [Topic Catalog](#topic-catalog) — sorted by namespace prefix
- [Consumers](#consumers) — who subscribes to what and how
- [Payload Types](#payload-types) — index of every `EventPayload` subclass
- [Publishing Patterns](#publishing-patterns) — conventions used

---

## Overview

Harness uses an **asynchronous mailbox-pattern EventBus** (`harness_core/eventbus.py`) with dot-separated topic names. There is no central constants file for topic strings; each subsystem defines its own prefixes inline (see *Topic Definition Locations* below). Three subscriber mechanisms co-exist:

| Subscriber | `id` | What it listens on | Dispatching |
|---|---|---|---|
| `HarnessEventListener` in `terminal_io/wiring.py` | `"tui"` | 13 topics in `TUI_TOPICS` (wiring.py:23-37) | Single-hop dispatch via `handle_default()` → `TopicHandlers.*` methods by topic-name-to-method name mapping (`agent.tool.call` → `handle_agent_tool_call`) |
| `EventListenerLoopMixin` (in `agent/mixin.py`) | agent's id | Discovered automatically from method name `handle_tui_user_input` via `eventbus.py:519-527` naming convention | Subscribes lazily at start of `run_loop()` |
| `Manager._ShutdownListener` (in `runtime/manager.py`) | manager-owned | `[PROCESS_CONTROL_QUIT, PROCESS_CONTROL_QUIT_CONFIRM]` explicitly | Two explicit handler methods (`handle_process_control_quit`, `handle_process_control_quit_confirm`) |

All event **payloads** live in `harness_core/event_types.py`. Every payload is a `@dataclass(kw_only=True)` subclass of `EventPayload`.

---

## Topic Catalog

### `agent.session.*` (2 topics)

| # | Topic | Payload class | Publisher | File:Line | Description |
|---|-------|---------------|-----------|-----------|-------------|
| 1 | `agent.session.autocompress` | `SystemMessagePayload(title="Auto-Compression", message=<utilization>, model="")` | Agent (via `_check_and_compress_if_needed`) | `agent/mixin.py:57` | Emitted when context compression succeeds. Contains pre/post utilization percentages. Displayed as a system banner via `print_system`. |
| 2 | `agent.session.error` | `SessionErrorPayload(message=<error text>, title="Auto-Compression Error")` | Agent (via `_check_and_compress_if_needed` + exception handler) | `agent/mixin.py:68, 177` | Emitted when auto-compression fails. Two publish sites: explicit error from compression dict (`mixin.py:68`) and catch-all exception wrapper (`mixin.py:177`). Displayed as an error panel via `display_error`. |

### `agent.status.*` (1 topic)

| # | Topic | Payload class | Publisher | File:Line | Description |
|---|-------|---------------|-----------|-----------|-------------|
| 3 | `agent.status.ready` | `SystemMessagePayload(title="🚀 Agent Ready — {name} ({model_name})", message="Type a message to begin...", model=<model_name>)` | Agent (via `_publish_ready_status`) | `agent/mixin.py:191` | Emitted synchronously at the very start of `run_loop()` **before any await**. Publishes the agent's name and model. Triggers both the 🚀 system banner AND `update_sidebar_model_name`. **Must be subscribed to before `run_loop()` starts** or the message is dropped (see MEMORY.md). |

### `agent.tool.*` (3 topics)

| # | Topic | Payload class | Publisher(s) | File:Line | Description |
|---|-------|---------------|--------------|-----------|-------------|
| 4 | `agent.tool.call` | `ToolCallPayload(func_name, args_str, summary, pre_content, reasoning)` | Agent (via `_publish_tool_call`) | `agent/mixin.py:338` | Emitted when the LLM returns a TOOL_CALL kind output. Renders as an in-progress tool-call panel (`display_tool_call`). |
| 5 | `agent.tool.error` | `ToolErrorPayload(message=<text>)` | Agent (3 publish sites) | `agent/mixin.py:255, 303, 376` | Emitted for ERROR kind output from LLM, skill interceptor RESTRICTED outcome, and exception handler wrapping. Renders as an error panel + resets pending tool panel. |
| 6 | `agent.tool.result` | `ToolResultPayload(func_name, result_title, result_display_text, result_theme, result_type_tag)` | Agent (via `_handle_and_publish_tool_result`) | `agent/mixin.py:364` | Emitted after a tool call completes successfully. Renders as a tool-result panel (`display_tool_result`). |

### `agent.turn.*` (5 topics)

| # | Topic | Payload class | Publisher(s) | File:Line | Description |
|---|-------|---------------|--------------|-----------|-------------|
| 7 | `agent.turn.start` | `ControlPayload(action={})` (empty dict) | Agent (via `_run_turn`) | `agent/mixin.py:271` | Emitted at the start of each turn. TUI shows spinner via `show_spinner()`. |
| 8 | `agent.turn.stop` | `ControlPayload(action={})` (empty dict) | Agent (finally block in `_run_turn`) | `agent/mixin.py:275` | Always fires after a turn completes (try/finally). TUI hides spinner via `hide_spinner()`. |
| 9 | `agent.turn.response` | `AgentResponsePayload(content, response, context_length, reasoning)` | Agent (via `_publish_response`) | `agent/mixin.py:317` | Emitted when the LLM returns RESPONSE kind output. Renders as an agent-response panel (`display_agent_response`). |
| 10 | `agent.turn.stats` | `TurnStatsPayload(response, context_length, elapsed_seconds)` | Agent (3 sites) | `agent/mixin.py:53, 326, 348` | Emitted after each response, after each tool call (`elapsed_seconds=0.0`), and on successful auto-compression (`response=None`). Renders sidebar turn-stats display (`display_turn_stats`). |

### `agent.tasklist.*` (3 topics)

| # | Topic | Payload class | Publisher(s) | File:Line | Description |
|---|-------|---------------|--------------|-----------|-------------|
| 11 | `agent.tasklist.initialize` | `TaskListPayload(from_task_list)` | `TaskList._emit()` in `initialize_tasks()` | `agent/task_list.py:155` | Emitted when a task list is first populated from user input. Sidebar refreshes via `_refresh()`. |
| 12 | `agent.tasklist.update` | `TaskListPayload(from_task_list)` | `TaskList._emit()` in `update_status()` | `agent/task_list.py:188, 193` | Emitted after any task status change (whether or not the task was found). Sidebar refreshes. |
| 13 | `agent.tasklist.reset` | `TaskListPayload(from_task_list)` | `TaskList._emit()` in `reset()` | `agent/task_list.py:160` | Emitted when all tasks are cleared (all become completed/failed → list auto-clears). Sidebar refreshes. |

> **Note:** All three tasklist topics use the **same** payload type (`TaskListPayload`) and the same publishing helper (`TaskList._emit()`), which bypasses `EventPublisher` and calls `event_bus.publish(...)` directly. The topic string is hardcoded in each `_emit()` call — there's no shared constant.

### `process_control.*` (2 topics)

| # | Topic | Payload class | Publisher(s) | File:Line | Definition location |
|---|-------|---------------|--------------|-----------|---------------------|
| 14 | `process_control_quit` | `AppControlPayload(action="quit_request", message="")` | `/exit` or `/quit` command (via `cmd_exit`) | `commands/exit_quit.py:20-23` | Constant defined at `event_types.py:321` (`PROCESS_CONTROL_QUIT`) |
| 15 | `process_control_quit_confirm` | `AppControlPayload(action="quit_confirm", message="")` | TUI quit confirmation dialog (via `publish_quit_confirm`) | `terminal_io/tui_app.py:281-284` | Constant defined at `event_types.py:322` (`PROCESS_CONTROL_QUIT_CONFIRM`) |

These two topics are **not** in `TUI_TOPICS`. They're subscribed to exclusively by `Manager._ShutdownListener` (manager.py:114) which runs on a worker thread and bridges the confirmation into `app.exit()`.

### `tui.*` (1 topic — published BY TUI, not consumed by it)

| # | Topic | Payload class | Publisher(s) | File:Line | Description |
|---|-------|---------------|--------------|-----------|-------------|
| 16 | `tui.user.input` | `UserInputPayload(message=<text>, source="tui")` | TUI (via `TuiEventPublisher.publish_user_input`) | `terminal_io/event_publisher.py:55-58`, called from `harness_tui.py:249` / `tui_app.py:316-324` | Published when user types a message and submits it. Consumed by the agent's `EventListenerLoopMixin` (auto-discovered via method-name convention). **NOT in TUI_TOPICS** — this topic flows *into* the agent, not out of it. |

---

## Consumers

### Subscriber: `HarnessEventListener` ("tui") — wiring.py:40-68

Subscribes to all 13 topics listed below and dispatches each via a **single-hop** method-name mapping (`agent.tool.call` → `TopicHandlers.handle_agent_tool_call`). Runs on the event loop's thread (same as Textual app).

| Topic | Handler Method | File:Line | Action |
|-------|---------------|-----------|--------|
| `agent.tasklist.initialize` | `handle_agent_tasklist_initialize` | `event_handlers.py:59` | Calls `_refresh()` → `get_tui().update_sidebar_tasks_from_payload(payload)` |
| `agent.tasklist.update` | `handle_agent_tasklist_update` | `event_handlers.py:62` | Same as above |
| `agent.tasklist.reset` | `handle_agent_tasklist_reset` | `event_handlers.py:65` | Same as above |
| `agent.session.autocompress` | `handle_agent_session_autocompress` | `event_handlers.py:68` | Calls `_system_message()` → `print_system(payload.title, payload.message)` |
| `agent.status.ready` | `handle_agent_status_ready` | `event_handlers.py:71` | `_system_message()` + `get_tui().update_sidebar_model_name(payload.model)` (if non-empty) |
| `agent.turn.start` | `handle_agent_turn_start` | `event_handlers.py:81` | `get_tui().show_spinner()` |
| `agent.turn.stop` | `handle_agent_turn_stop` | `event_handlers.py:84` | `get_tui().hide_spinner()` |
| `agent.tool.error` | `handle_agent_tool_error` | `event_handlers.py:87` | `display_error(payload.message)` + resets pending tool panel |
| `agent.session.error` | `handle_agent_session_error` | `event_handlers.py:95` | `display_error(payload.message)` |
| `agent.tool.call` | `handle_agent_tool_call` | `event_handlers.py:101` | `display_tool_call(func_name, args_str, summary=..., pre_content=..., reasoning=...)` |
| `agent.tool.result` | `handle_agent_tool_result` | `event_handlers.py:113` | `display_tool_result(func_name, result_title, result_display_text, result_theme, result_type_tag)` |
| `agent.turn.response` | `handle_agent_turn_response` | `event_handlers.py:125` | `display_agent_response(content, response, context_length, reasoning=...)` |
| `agent.turn.stats` | `handle_agent_turn_stats` | `event_handlers.py:136` | `display_turn_stats(response, context_length, elapsed_seconds=...)` |

### Subscriber: `EventListenerLoopMixin` (in agent/mixin.py) — the Agent's own listener

Subscribes to **one** topic discovered automatically from its method name:
- Method `handle_tui_user_input(self, event)` → auto-discovers topic `"tui.user.input"` via `eventbus.py:519-527`. Subscribed lazily at start of `run_loop()` (mixin.py:122).

### Subscriber: `Manager._ShutdownListener` (in runtime/manager.py) — process-level coordination

Subscribes explicitly to 2 topics on a worker thread:
- `PROCESS_CONTROL_QUIT` → handler `_on_shutdown_requested()` at manager.py:249 → shows TUI confirmation dialog
- `PROCESS_CONTROL_QUIT_CONFIRM` → handler `_on_quit_confirmed()` at manager.py:258 → triggers `app.exit()`

---

## Payload Types

Every payload is a `@dataclass(kw_only=True)` subclass of `EventPayload` (defined in `harness_core/event_types.py`). All payloads carry optional `metadata: dict[str, Any]`.

| Payload Class | Fields (excluding metadata) | Used by Topics |
|---------------|----------------------------|----------------|
| `TaskListPayload` | `tasks: list[TaskInfo]`, `total_tasks`, `completed_tasks`, `has_incomplete` | `agent.tasklist.initialize`, `.update`, `.reset` |
| `SystemMessagePayload` | `title: str`, `message: str`, `model: str` | `agent.session.autocompress`, `agent.status.ready` |
| `SessionErrorPayload` | `title: str = "Auto-Compression Error"`, `message: str` | `agent.session.error` |
| `AgentResponsePayload` | `content: str`, `response: dict\|None`, `context_length: int`, `reasoning: str\|None` | `agent.turn.response` |
| `TurnStatsPayload` | `response: dict\|None`, `context_length: int`, `elapsed_seconds: float\|None` | `agent.turn.stats` |
| `ToolCallPayload` | `func_name: str`, `args_str: str`, `summary: str\|None`, `pre_content: str`, `reasoning: str\|None` | `agent.tool.call` |
| `ToolResultPayload` | `func_name: str`, `result_title: str\|None`, `result_display_text: str`, `result_theme: str = "info"`, `result_type_tag: str = "text"` | `agent.tool.result` |
| `ToolErrorPayload` | `message: str` | `agent.tool.error` |
| `UserInputPayload` | `message: str`, `source: str = "tui"` | `tui.user.input` |
| `ControlPayload` | `action: dict\|None` (empty dict in practice) | `agent.turn.start`, `.stop` |
| `AppControlPayload` | `action: str`, `message: str` | `process_control_quit`, `.quit_confirm` |

---

## Publishing Patterns

### 1. Topic definition — no centralized constants file

Topic strings are defined **inline** at each publish site, not in a shared constants module. Exceptions (the only literal constants) are the two process-control topics:
- `PROCESS_CONTROL_QUIT = "process_control_quit"` → `event_types.py:321`
- `PROCESS_CONTROL_QUIT_CONFIRM = "process_control_quit_confirm"` → `event_types.py:322`

Imported by `runtime/manager.py` and `commands/exit_quit.py`.

### 2. Direct vs. EventPublisher publish

- **`TaskList._emit()`** bypasses the `EventPublisher` mixin entirely and calls `event_bus.publish(Event(topic=..., sender=self._sender_id, payload=...))` directly (task_list.py:96-103).
- **All other publishers** use the `Agent.publish(topic, payload)` method inherited from `EventPublisher` (which wraps in an `Event` dataclass and calls `self._bus.publish(...)`).

### 3. Naming convention for auto-discovery

The EventBus's `EventListener` base class supports a naming convention: any handler method named `handle_<topic_with_dots_underscored>` is auto-registered as a subscriber to that topic. Implemented at `eventbus.py:519-527`. Used by `EventListenerLoopMixin.handle_tui_user_input` → subscribes to `"tui.user.input"`.

### 4. Sender filtering

All TUI listeners and the agent's user-input listener filter events by sender id. The TUI listener only processes events whose `sender == <agent_id>`; the `_ShutdownListener` has no sender filter (it listens globally). Implemented via `filter_by_sender()` decorator in `eventbus.py:43-60`.

### 5. Thread model for widget mutation

The TUI's `HarnessTUI.run_on_app_thread()` method wraps all widget mutations:
- **Same-thread calls** (listener runs on app loop): wrap the callback in `with app._context(): fn()` to set Textual's `active_app` context.
- **Cross-thread calls**: use `app.call_from_thread(fn)`.

This is critical — see MEMORY.md for the "NoActiveAppError" crash history.

### 6. No tool/skill publishes events

None of the modules in `harness_core/tools/` or `harness_core/skills/` publish any event. Only `agent/mixin.py`, `agent/task_list.py`, `commands/exit_quit.py`, and `terminal_io/tui_app.py` are publish sites.
