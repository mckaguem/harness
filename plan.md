# TUI Layer Restructuring Implementation Plan

## Context / Problem

The TUI layer in `harness_core/terminal_io/` (`tui_app.py`, `harness_tui.py`,
`event_handlers.py`, `event_listener.py`) is tightly coupled and routes events
through a two-hop bridge: the event bus publishes an `EventBusMessage`, which is
re-posted onto the Textual message bus and finally handled by `TopicHandlers`.
This indirection obscures the data flow, splits event handling across multiple
layers, and forces the App (`tui_app.py`) to own subscription wiring and hold a
reference to the listener it should not know about.

Additional issues:
- `tui_app.py` imports and subscribes `event_listener` directly in `__init__`,
  violating separation of concerns.
- `widgets.py` defines `TOOL_SEPARATOR` locally to dodge a circular import with
  `display.py`, leaving duplicated/divergent constants.
- `HarnessTUI` carries dead code and exposes private `_app` access paths that
  external modules reach into.

The goal is a modular, maintainable design where events are handled in ONE place
and dispatched directly to rendering.

## Goals

1. **Eliminate the two-hop `EventBusMessage` bridge** (event bus → Textual message
   bus → `TopicHandlers`). Events are handled in ONE place and dispatched directly
   to rendering.
2. **The App (`tui_app.py`) must NOT import `event_listener` or subscribe in its
   constructor/`start()`.** Subscription/wiring belongs in a dedicated module.
3. **`HarnessTUI` controller = clean presenter** the App binds to; no dead code;
   no private `_app` access from outside.
4. **Preserve the public API** tests/callers rely on: `TextualHarnessApp`,
   `HarnessTUI`, `get_tui`, `make_event_listener`/`subscribe_event_listener`,
   `display.*`, `publish_user_input`.
5. **Fix the circular import:** `widgets.py` defines `TOOL_SEPARATOR` locally to
   dodge a cycle with `display.py` — move `TOOL_SEPARATOR` into `display.py` and
   break the cycle.

## New Event Flow

```
EventBus.publish_to_topic(sender, topic, payload)
  -> HarnessEventListener.handle_<topic>            (in wiring.py, sender-filtered at subscription)
  -> renders directly via display.* or get_tui() controller methods
  -> Widget (output pane / spinner / sidebar)
```

No `Message` subclass, no `post_message`, no `on_event_bus_message`.

## Module-by-Module Implementation Steps

### 1. `tui_app.py` — KEPT, simplified
- **Action:** Reduce to build-and-bind only.
- **Key edits:**
  - Remove from `__init__`: `subscribe_event_listener` import + call,
    `TopicHandlers()` instantiation, `_event_listener` reference, and the
    `try/except print(listener)` block.
  - Constructor stores only `_agent_id`, `_on_exit`, and widget slots.
  - Delete `on_event_bus_message` entirely.
  - `start()` becomes `async def start(self): await self.run_async()`.
  - Imports only `widgets` + `harness_tui.get_tui` (lazy in
    `on_mount`/`action_submit_input`) + `event_types.TaskListPayload`.
  - Exports: `TextualHarnessApp`, `launch`.

### 2. `harness_tui.py` — KEPT, cleaned presenter
- **Action:** Make `HarnessTUI` a pure presenter singleton.
- **Key edits:**
  - `HarnessTUI` singleton via `get_tui()`.
  - Public methods only: `bind`, `is_active`, `reset`, `write_count`, `write`,
    `begin_tool_panel`, `complete_tool_panel`, `show_spinner`, `hide_spinner`,
    `update_sidebar_*`, `publish_user_input`.
  - Keep `_app` private; remove dead/commented code.
  - Import `TOOL_SEPARATOR` from `display`.
  - Exports: `HarnessTUI`, `get_tui`.

### 3. `wiring.py` — NEW (single owner of wiring)
- **Action:** Create the only place that creates the listener, subscribes
  topics, applies sender filtering, and dispatches events directly to rendering.
- **Key edits:**
  - `HarnessEventListener(EventListener)` with explicit `handle_<topic>` methods
    (13 topics) that validate payload type then call `display.*` / `get_tui()`
    directly (NO `EventBusMessage`, NO `post_message`, NO `tui._app` access).
  - Sender filtering applied at subscription time.
  - `make_event_listener(agent_id, bus=None)` and
    `subscribe_event_listener(agent_id, bus=None)` — the latter calls
    `make_event_listener` + `run()` + `subscribeToStuff()`.
  - Subscribe-list constant (13 topics) lives here.
  - Delegates rendering logic to a `TopicHandlers` strategy imported from
    `event_handlers.py` (single owner of rendering logic).
  - Exports: `make_event_listener`, `subscribe_event_listener`, plus
    `make_task_list_listener` / `subscribe_task_list_listener` aliases.

### 4. `event_handlers.py` — KEPT, simplified
- **Action:** Convert to a pure rendering strategy.
- **Key edits:**
  - `TopicHandlers` class — no knowledge of `EventBusMessage`.
  - Each method validates payload and calls `display.*` / `get_tui()`.
  - Used exclusively by `wiring.py`.
  - Import `TOOL_SEPARATOR` from `display`.
  - Exports: `TopicHandlers`.

### 5. `event_listener.py` — KEPT as shim
- **Action:** Re-export from `wiring.py` so existing imports resolve.
- **Key edits:**
  - `from .wiring import make_event_listener, subscribe_event_listener,
    make_task_list_listener, subscribe_task_list_listener`
  - This keeps `from harness_core.terminal_io.event_listener import
    make_event_listener, subscribe_event_listener` working for tests.

### 6. `widgets.py` — KEPT, cycle broken
- **Action:** Remove the cycle-inducing import and local constant.
- **Key edits:**
  - Remove `from .display import print_system` import.
  - `TaskListSidebar` builds its own `Group` without `print_system`.
  - Remove local `TOOL_SEPARATOR` (now owned by `display.py`).
  - Exports: `StatusSpinner`, `TaskListSidebar`.

### 7. `display.py` — KEPT, minor
- **Action:** Add the shared separator constant.
- **Key edits:**
  - Add `TOOL_SEPARATOR = Rule(style="dim")`.
  - Keep all `display_*` / `print_*` / `reset_pending_tool_panel` exports.

### 8. `tui.py` — KEPT shim (unchanged)
- Re-exports `HarnessTUI`, `get_tui`, `TextualHarnessApp`, `launch`,
  `StatusSpinner`, `TaskListSidebar`. No changes.

### 9. Unchanged files
- `event_publisher.py`, `speed.py`, `task_display.py`, `prompt.py` — no changes.

## File Layout

```
harness_core/terminal_io/
├── __init__.py
├── tui.py                      (shim, unchanged)
├── tui_app.py                  (KEPT, simplified)
├── harness_tui.py              (KEPT, cleaned presenter)
├── wiring.py                   (NEW — listener + subscription + dispatch)
├── event_listener.py           (KEPT, shim → wiring)
├── event_handlers.py           (KEPT, simplified — rendering strategy)
├── widgets.py                  (KEPT, cycle broken)
├── display.py                  (KEPT, minor — TOOL_SEPARATOR added)
├── event_publisher.py          (unchanged)
├── speed.py                    (unchanged)
├── task_display.py             (unchanged)
└── prompt.py                   (unchanged)
```

## Public API / Test Contract

The following symbols must keep working:

- **`terminal_io.tui`**: `TextualHarnessApp`, `HarnessTUI`, `get_tui`, `launch`
- **`terminal_io`**: `display` module + `print_system`, `display_tool_call`,
  `display_tool_result`, `display_error`, `display_agent_response`,
  `display_user_message`, `display_turn_stats`, `reset_pending_tool_panel`
- **`terminal_io.event_listener`**: `make_event_listener`, `subscribe_event_listener`
- **`harness_tui`**: `get_tui()` → controller with `reset` / `is_active` /
  `write_count` / `publish_user_input` / `bind` / `show_spinner` / `hide_spinner`

**Test expectations:**
- `TextualHarnessApp(agent_id=None)`
- `get_tui().reset()` / `is_active()` / `write_count()`
- `display.print_system`, `display.display_message_panel`
- `tui.publish_user_input`
- `subscribe_event_listener(agent_id, bus)`
- Posting `agent.turn.start` / `agent.turn.stop` triggers spinner toggle.

## Definition of Done

- [ ] No `EventBusMessage` subclass, `post_message`, or `on_event_bus_message`
      remains in the TUI layer.
- [ ] `tui_app.py` does not import `event_listener` and performs no subscription
      in `__init__`/`start()`.
- [ ] All 13 topics are handled in `wiring.py` and dispatched directly to
      `display.*` / `get_tui()`; rendering logic lives in `event_handlers.TopicHandlers`.
- [ ] `HarnessTUI` is a clean presenter with no dead code and no external `_app`
      access.
- [ ] `TOOL_SEPARATOR` is defined once in `display.py`; `widgets.py` no longer
      imports `print_system` and the circular import is gone.
- [ ] All public symbols in the Test Contract resolve and behave as before.
- [ ] `event_listener.py` shim resolves existing test imports.

## Verification

```bash
# Static type checking
mypy harness_core tests

# Run the test suite (focus on TUI + display)
pytest tests/
pytest tests/test_tui.py tests/test_terminal_display.py
```

All of the above must pass with the existing public API intact.

## Addendum — Final Event-Wiring Decision & "App is not running" Fix

### The two-hop bridge WAS removed
- `EventBusMessage` (Textual `Message` subclass) and the `on_event_bus_message` bridge in `tui_app.py` were deleted.
- Events now flow: `EventBus.publish_to_topic` → `HarnessEventListener` (in `wiring.py`, id `'tui'`) mailbox listener → `TopicHandlers` method (in `event_handlers.py`) → `display.*` / `get_tui()` controller methods → widget.
- `event_listener.py` is now a thin backward-compat shim re-exporting `make_event_listener` / `subscribe_event_listener` from `wiring.py`.

### Where the listener is started (final decision)
- NOT in `__main__.blarg` and NOT in `tui_app.py`'s constructor/`start()` (both were tried and caused bugs).
- FINAL: the listener is started inside `TextualHarnessApp.on_mount`, lazily and only when `self._agent_id is not None`. This runs on the app thread while the Textual loop is already running, so handler callbacks always execute on the live app loop.
- `on_mount` stores the listener on `self._event_listener` to keep it referenced.

### Why starting it in `__main__` crashed with "App is not running"
- `subscribe_event_listener` calls `EventListener.run()`, which binds the mailbox task to whatever loop is running in the calling thread. When called from `__main__`'s coroutine thread, it shared the same loop as the app — but it could fire `agent.status.ready` (published by `agent.run_loop()`) in the race BEFORE `app.run_async()` set `app._thread_id`/`_loop`.
- `HarnessTUI.write()` keyed off `app._thread_id` (which is `0`/unset pre-run) and concluded "different thread", calling `app.call_from_thread()` while `app._loop is None` → `RuntimeError: App is not running`.

### The controller hardening (harness_tui.py)
- `HarnessTUI` now buffers writes until the app is active: `__init__` has `self._write_buffer`, `write()` queues renderables when `self._app`/`self._output` is `None`, and `bind()` flushes the buffer after attaching the output pane.
- A new `run_on_app_thread(fn)` helper replaces the inline `_thread_id`/`call_from_thread` checks in `write`/`begin_tool_panel`/`complete_tool_panel`. It gates on `app.is_running`: if the loop isn't live it returns without calling `call_from_thread` (the buffer covers pre-bind writes).
- This makes the controller robust to early events regardless of thread.

### Outcome
- Inline integration test passes: `agent.turn.start` → spinner visible, `agent.tool.call` → collapsible rendered into the output pane, `agent.turn.stop` → spinner hidden. No `RuntimeError`.
- `__main__.blarg` no longer references `subscribe_event_listener`.
