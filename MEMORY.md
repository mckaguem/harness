

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

# Goal (active)
- Modify __main__.py and Manager class: Manager creates the agent via a generic launch helper; __main__ calls it with "main" + AGENT_TOOLS; Manager runs it. Manager's TUI start moved to a separate function (headless option reserved for future, not implemented). __main__ owns config loading, agent/skill discovery.

# Goal (resolved)
- COMPLETED: Refactored __main__.py + Manager. Manager now owns agent creation via `launch_agent()` (generic helper: starts run folder + Agent.from_agent_name). Manager.__init__(agent=None). TUI start isolated in `_launch_tui()` with TODO(headless) marker (headless NOT implemented). __main__.py owns config/skill/agent discovery in `setup()`; `blarg()` calls Manager().launch_agent("main", AGENT_TOOLS) then run(). Committed as c5d4e00. (Prior commit 74bd838 = grep .gitignore + dispatcher truncation + log path.)


## TUI listener subscription timing — FIXED (initial "Agent Ready" banner + model name missing)
- Root cause of the missing startup message / model name: the TUI listener (`id='tui'`) subscribed to the event bus inside `TextualHarnessApp.on_mount`. `on_mount` fires only AFTER `app.run_async()` begins mounting — which is several awaits into the `_tui_task`. Meanwhile the agent's `run_loop` publishes `agent.status.ready` SYNCHRONOUSLY at the very start (before its first await). The EventBus does NOT replay missed messages, so the event was dropped → no 🚀 banner and no `update_sidebar_model_name` (sidebar stuck at "-").
- Fix (applied): moved `subscribe_event_listener(self._agent._id, event_bus)` OUT of `tui_app.py:on_mount` and INTO `Manager.run()` (`harness_core/runtime/manager.py`), placed BEFORE `asyncio.create_task(self._agent.run_loop())` (and before `_tui_task` creation). Stored as `self._tui_event_listener` so it isn't GC'd. Now the `"tui"` subscription exists on the bus before `agent.status.ready` is published.
- Why no "App is not running" crash: the TUI controller (`harness_tui.py`) buffers widget writes until the app is bound & running (`run_on_app_thread` / `write` guard on `app.is_running`), so handlers firing before `run_async` starts simply buffer and flush on `bind()` in `on_mount`. So moving the subscription earlier is safe.
- `on_mount` now ONLY does `controller.bind(...)`, `sidebar.refresh_tasks()`, output cache, input focus. No `event_bus`/`subscribe_event_listener`/`self._event_listener` references remain in `tui_app.py`.
- Verified: imports OK; only one runtime `subscribe_event_listener` call site (manager.py:126); listener id is `"tui"`; subscribes `TUI_TOPICS` incl. `agent.status.ready`. No duplicate registration → no "Agent already registered".
- OLD MEMORY NOTE about `__main__.blarg` owning the subscribe call is stale: ownership moved to `Manager.run()` (not `__main__`), and the App's `on_mount` no longer subscribes. Update any text referencing "start the listener INSIDE on_mount" as a fix direction — that approach caused this exact missed-startup-event race.


## TUI sidebar model name — FIXED (was stuck at "-")
- After the subscription-timing fix, the 🚀 banner appeared (it routes through `HarnessTUI.write` which buffers+replays on `bind()`), but the sidebar model name stayed "-". Root cause: `update_sidebar_model_name` (tui_app.py) had TWO defects: (1) it early-returned on `not self.is_running`, so when the `agent.status.ready` handler fired before `on_mount` finished, the value was dropped; (2) even when running it stored `_model_name` but never called `sidebar.refresh_tasks()`, so the once-painted sidebar was never repainted. `payload.model` is correct ("hy3" via default_model), so Candidate-A (empty model) was NOT the cause.
- Fix: persist the model name on the controller (`HarnessTUI._model_name` + `set_model_name()`/`get_model_name()` in harness_tui.py) so it survives before the app is mounted. `update_sidebar_model_name` now calls `get_tui().set_model_name(model_name)` FIRST (before the `is_running` guard), then updates the widget + `refresh_tasks()` when running. `on_mount` seeds the sidebar from `controller.get_model_name()` before its initial `refresh_tasks()`. This is race-safe both ways (handler first OR on_mount first).
- Files changed: `harness_core/terminal_io/harness_tui.py` (added `_model_name` field + `set/get_model_name`), `harness_core/terminal_io/tui_app.py` (`update_sidebar_model_name` + `on_mount`). `widgets.TaskListSidebar.set_model_name` only stores (no refresh) — that is fine now that callers refresh.
- Verified: imports OK; `refresh_tasks()` now called after `set_model_name` in both paths; no leftover `is_running` early-return drops the name.


## TUI sidebar model name — FIXED AGAIN (proxy method was short-circuiting)
- The first model-name fix failed: it correctly edited `TextualHarnessApp.update_sidebar_model_name` (tui_app.py) to persist+refresh_tasks, but the handler `event_handlers.py:79` calls `get_tui().update_sidebar_model_name(payload.model)` — i.e. the `HarnessTUI` CONTROLLER proxy in `harness_tui.py`, NOT the app method directly. The proxy had `if self._app is None: return` BEFORE delegating, so when `agent.status.ready` fired before `on_mount` bound the app (`self._app` still None), the proxy returned early and the value was never persisted or rendered. That is why behaviour was unchanged.
- Real fix: in `harness_tui.py`, `HarnessTUI.update_sidebar_model_name` now calls `self.set_model_name(text)` BEFORE the `if self._app is None` guard, then delegates to the app method when bound. `set_model_name`/`get_model_name` persist `HarnessTUI._model_name`; `on_mount` (tui_app.py) seeds `sidebar.set_model_name(controller.get_model_name())` before its initial `refresh_tasks()`. Race-safe both orderings.
- LESSON: when editing a `get_tui()`-exposed method, verify WHICH method the call site actually hits (the HarnessTUI controller proxy vs. the TextualHarnessApp app method). The event handler resolves `get_tui()` = the controller, so the proxy must persist before any `self._app is None` guard. Don't repeat the prior mistake of only patching the app method.



## TUI NoActiveAppError fix (Collapsible tool panel mount)
- Root cause: `HarnessTUI.run_on_app_thread` (harness_core/terminal_io/harness_tui.py:112) had a same-thread branch that called the widget-mutation callback `fn()` directly WITHOUT wrapping it in Textual's `active_app` context. The TUI event-listener mailbox task runs as a plain asyncio task on the app's own loop (same thread), so `output.mount(Collapsible)` ran with `active_app` unset → `Collapsible.compose` raised `NoActiveAppError` and crashed the TUI when a tool-call panel was mounted.
- Fix: the same-thread branch now does `with app._context(): fn()` (sets `active_app` via Textual's `_context()` context manager). The cross-thread branch is unchanged: `else: app.call_from_thread(fn)` (which raises if called from the same thread and already wraps in `_context` internally). Verified: `hasattr(App, '_context')` is True; imports OK.
- WARNING: When invoking Textual widget mount/compose/update from the event-listener mailbox task or ANY plain asyncio task on the app loop, you MUST set `active_app` (via `app._context()` for same-thread, or `app.call_from_thread` for cross-thread). `call_from_thread` raises if called from the same thread. Do NOT add new `fn()`-bare same-thread mutation paths — funnel all widget mutations through `run_on_app_thread` (now context-safe).
- Note: `update_sidebar_model_name` / `update_sidebar_usage` / `update_sidebar_tasks_from_payload` in `tui_app.py` call `query_one` / `refresh_tasks` directly (guarded by `is_running`). `TaskListSidebar.refresh_tasks` (widgets.py:88) only builds `Group`/`Text`/`Rule`/`Markdown` (no `Collapsible`), so it does NOT trigger this crash. But any FUTURE sidebar update that mounts widgets must also go through `run_on_app_thread` / `app._context()`.
- All widget mutations in harness_tui.py (write, begin_tool_panel, complete_tool_panel, show/hide_spinner, sidebar updates) funnel through `run_on_app_thread` (lines 110, 169, 198, 222) — no other bare same-thread mutation paths found in harness_core/terminal_io.
