

# Project Memory

## terminal_io TUI Refactor (2025)
- Restructured tightly-coupled TUI files into `wiring.py` (single event dispatch, no two-hop bridge), `event_listener.py` (shim), cleaned `tui_app.py`/`harness_tui.py`, broke circular import in `widgets.py`.
- `start()` in `tui_app.py` must NOT call `self._event_listener.run()` — the listener MUST be created/run by the caller (`__main__.blarg`) using `subscribe_event_listener(agent_id, event_bus)`, not inside the App. The App's own `__init__` must NOT subscribe (avoids "Agent already registered" from duplicate `register_agent` calls with id 'tui').
- The TUI listener registers id `'tui'` on the event bus; `harness_core/__main__.py` blarg() is responsible for creating+running it once before `await asyncio.gather(tui_launch(...), agent.run_loop())`.

# TUI Event-Threading Constraints (CRITICAL)

## The "app not running" / "call_from_thread from wrong thread" problem
The TUI's `HarnessTUI` controller methods (`write`, `begin_tool_panel`, `complete_tool_panel`, `show_spinner`, `hide_spinner`, `update_sidebar_*`) MUTATE Textual widgets and MUST run on the Textual app's event loop. After removing the EventBus→Textual message-bus bridge, events are handled by `HarnessEventListener`'s mailbox listener, which runs on **whatever thread called `EventListener.run()`**.

## Current bug (as of last fix)
`__main__.blarg` calls `subscribe_event_listener(agent._id, event_bus)` from the `__main__` thread (the one running `asyncio.run(blarg)` / `asyncio.gather`). Meanwhile `tui_launch` runs `app.run_async()` on the SAME thread (Textual uses the running loop). So the listener mailbox task and the Textual app share the same loop/thread — meaning handlers run ON the app thread and `call_from_thread` should be safe. BUT: if the listener is started on a DIFFERENT thread than the app (e.g. app runs on main thread, listener started from a worker thread), then `get_tui().write()` etc. call `app.call_from_thread` from a non-app thread, which is correct — UNLESS the app isn't running yet (bound but not `is_running`) → "app not running" error.

## The display.* path
`display.py` calls `get_tui().write()` / `begin_tool_panel()` / `complete_tool_panel()`. These guard on `self._app is None` but NOT on `is_running`. When called before `run_async()` starts the loop, `call_from_thread` raises "App is not running". 

## Fix direction (if "app not running" recurs)
- Ensure `subscribe_event_listener` is called AFTER the app is actually running, OR
- The controller should marshal via `app.call_from_thread` only when on a different thread, and when on the same thread just call directly (already done via `_thread_id` check) — but if called before `run_async`, `is_running` is False and Textual rejects `call_from_thread`.
- Consider starting the TUI listener INSIDE `on_mount` (app thread, app running) rather than in `__main__`, but that reintroduces App owning the listener. Alternative: start listener lazily on first event, or guard `write`/`begin_tool_panel` to buffer until running.
