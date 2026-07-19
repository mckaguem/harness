---

# Code Review: `harness_core/terminal_io` Module

**Scope:** All 12 Python files in `/workspaces/harness/harness_core/terminal_io/` (~1,663 lines total)
**Standards baseline used:** Fowler code smells from *Refactoring*, Ch. 3 (no repo-level coding standards exist).
**Verdict on hard violations:** None — no documented coding standards were found in the repository to violate. All findings below are smell judgement calls.

---

## display.py

### Smell: Mysterious Name
- `_LAST_TOOL_PANEL` (line 24) — a module-level mutable `dict | None` with no documentation of its contract or lifecycle beyond "single source of truth." Its name reveals nothing about what the dict contains (it holds `{"renderable", "title", "result"}` keys).

> **Hunk:**
> ```python
> _LAST_TOOL_PANEL: "dict | None" = None
> ```

**Recommendation:** Rename to `_pending_tool_panel` or better, encapsulate in a typed dataclass with clear fields (`call_renderable`, `title`, `result`). Better yet — the entire global should be owned by the controller (see harness_tui.py).

### Smell: Mysterious Name
- `_theme_border()` — prefix underscores imply "private" but it's used only once as a helper. The name describes implementation, not intent.

> **Hunk:**
> ```python
> def _theme_border(theme: str) -> str:
>     """Return a Rich border style string for the given theme."""
>     return {"error": "red", ...}.get(theme, "white")
> ```

**Recommendation:** Inline it or rename to `_border_style_for` to match Rich's vocabulary.

---

## event_listener.py

### Smell: Mysterious Name
- `subscribeToStuff()` (line 104) — camelCase in a Python codebase is a smell; "stuff" is vague and reveals nothing about the method's purpose.

> **Hunk:**
> ```python
> def subscribeToStuff(self):
>     self.subscribe([
>         "agent.tasklist.initialize",
>         ...
>     ])
> ```

**Recommendation:** Rename to `subscribe_topics()` or `register_subscriptions()`. Document the list of topics in a constant.

### Smell: Speculative Generality (minor)
- The inner-class factory pattern for `HarnessEventListener` adds indirection without clear benefit — each call creates a new class definition, which is unusual Python and can confuse linters/debuggers.

---

## tui_app.py

### Smell: Mysterious Name
- Module-level global `thecount = 0` (line 16) — cryptic name, module-level mutable state, used only inside one action method for a debug/count display that should not exist in production code.

> **Hunk:**
> ```python
> thecount = 0
> ...
> global thecount
> thecount += 1
> display_user_message(message + f'Count = {thecount}')
> ```

**Recommendation:** Delete this entirely. It's clearly debug scaffolding leaking into production code. If a message counter is needed, it should be an instance attribute on `TextualHarnessApp`.

### Smell: Mysterious Name
- Unused imports for `Footer` and `Header` (lines 6-7) — imported but never referenced in the file body. Linter would flag these; they persist through copy-paste.

> **Hunk:**
> ```python
> from textual.widgets import Footer, Header, TextArea
> ```

**Recommendation:** Remove unused imports.

### Smell: Duplicated Code
- `update_sidebar_usage`, `update_sidebar_tasks_from_payload`, and `update_sidebar_model_name` all follow the identical pattern: guard on `is_running`, try/except-query-one-sidebar, then call sidebar method. Three nearly-identical methods that could share a helper.

> **Hunk:**
> ```python
> def update_sidebar_usage(self, text: str | None) -> None:
>     if not self.is_running: return
>     try:
>         sidebar = self.query_one("#task-sidebar", TaskListSidebar)
>     except Exception:
>         return
>     sidebar.set_usage(text)
>     sidebar.refresh_tasks()
> ```

**Recommendation:** Extract a private helper `_with_sidebar(callback)` that handles the guard + query pattern once.

### Smell: Divergent Change
- `update_sidebar_tasks_from_payload` (lines 131–151) contains dead/abandoned code: commented-out `def _do()` block and commented-out `self.call_from_thread(_do)` — evidence of a half-reverted change that leaves the method in an inconsistent state.

> **Hunk:**
> ```python
>     #def _do() -> None:
>     try:
>         sidebar = self.query_one("#task-sidebar", TaskListSidebar)
>     except Exception:
>         return
>     sidebar.refresh_tasks_from_payload(payload)
> 
>     # try:
>     #     self.call_from_thread(_do)
>     # except Exception:
>     #     pass
> ```

**Recommendation:** Remove the dead code entirely. It creates false expectations about thread safety.

### Smell: Mysterious Name
- `print(listener)` (line 92) and bare `import traceback; traceback.print_exc()` in `__init__` — debug artifacts that should not be present in shipped code.

> **Hunk:**
> ```python
> listener = subscribe_event_listener(self._agent_id)
> self._event_listener = listener
> print(listener)
> except Exception as e:
>     import traceback
>     traceback.print_exc()
> ```

**Recommendation:** Use `logging.debug()` instead of `print()`. Remove the bare traceback.

### Smell: Speculative Generality (minor)
- The `_on_exit` parameter in `__init__` is stored but never wired to any callback mechanism — it's dead storage added for future use that never materialized.

---

## harness_tui.py

### Smell: Mysterious Name
- Parameter named `input` shadows the Python builtin (line 58).

> **Hunk:**
> ```python
> def bind(self, app, output, input, spinner):
> ```

**Recommendation:** Rename to `input_widget` or `user_input`.

### Smell: Duplicated Code
- The thread-marshal pattern (`app_thread = getattr(app, "_thread_id", ...)` → branch on equality) is repeated verbatim in `write()`, `begin_tool_panel()`, `complete_tool_panel()`, and the standalone fallback in `complete_tool_panel()`. Four copies of the same guard.

> **Hunk (in write):**
> ```python
> app_thread = getattr(app, "_thread_id", None)
> if app_thread is not None and app_thread == threading.current_thread().ident:
>     _do()
> else:
>     app.call_from_thread(_do)
> ```

**Recommendation:** Extract a helper `_marshal(fn)` that handles the branch once.

### Smell: Middle Man (mild)
- `update_sidebar_usage`, `update_sidebar_tasks_from_payload`, and `update_sidebar_model_name` all do nothing but delegate to the app — they're transparent passthroughs. The TUI controller could call the app directly, or the methods should own meaningful logic beyond forwarding.

---

## event_handlers.py

### Smell: Duplicated Code
- `_make_refresh_handler()` and `_make_system_message_handler()` factory closures create near-duplicate async wrappers that each check `isinstance(payload, X)` then delegate to a shared function. The pattern repeats for every handler in the class — each handler is ~5 lines of boilerplate (extract payload → type-check → call display).

> **Hunk:**
> ```python
> async def handle_agent_tasklist_initialize(self, event: Event) -> None:
>     await self._refresh(self, event)
> 
> async def handle_agent_tasklist_update(self, event: Event) -> None:
>     await self._refresh(self, event)
> ```

**Recommendation:** Consider a single generic dispatch that maps topic → handler function with automatic payload type checking via a registry pattern. This would eliminate 80% of the handler methods.

### Smell: Feature Envy (mild)
- `_make_refresh_handler` reaches into `self._refresh = _make_refresh_handler()` and calls it as `await self._refresh(self, event)` — passing `self` explicitly to a closure that was created with no reference to it is awkward. The factory pattern here creates unnecessary indirection.

---

## prompt.py / HarnessTUI.prompt()

### Hard Issue: Runtime Crash
- `prompt.py` calls `controller.prompt(...)` on line 20, but **no `prompt()` method exists** on `HarnessTUI`. The class's own docstring confirms input is now event-driven via `publish_user_input`, so the old blocking prompt was removed — but this file still references it. Any caller that triggers `prompt_user()` will get an `AttributeError` at runtime.

> **Hunk (prompt.py:20):**
> ```python
> return controller.prompt(prompt if prompt is not None else "")
> ```

**Recommendation:** Either remove `prompt.py` entirely (if no callers remain) or restore a stub `prompt()` method on `HarnessTUI`. Given the event-driven architecture, deletion is cleaner.

---

## widgets.py

### Smell: Divergent Change
- `TaskListSidebar` knows about display rendering (`from .display import display_user_message`, used in sidebar), task list markdown rendering, model name updates, usage text — four unrelated concerns in one widget class. Adding a "model change notification" is a different reason to edit this file than adding a new task-list field format.

---

## Speed & Task Display Modules (speed.py, task_display.py)

These are the cleanest files in the module. Minor observation:
- `format_tool_elapsed` uses Rich markup (`[dim]...[/dim]`) inside its return value — callers must render it as a string, not parse it, which is implicit coupling. Document this contract or accept it.

---

## Summary

| Category | Count | Worst Finding |
|----------|-------|---------------|
| Mysterious Name | 6 | `thecount` global in tui_app.py (debug artifact); `subscribeToStuff` in event_listener.py |
| Duplicated Code | 4 | Thread-marshal guard repeated 4×; sidebar update pattern repeated 3×; handler boilerplate ~80% repetitive |
| Speculative Generality | 2 | Dead `_on_exit`; half-reverted thread safety code block |
| Divergent Change | 2 | `TextualHarnessApp.update_sidebar_tasks_from_payload` with dead code; `TaskListSidebar` doing 4 things |
| Middle Man | 1 | TUI controller methods that are pure passthroughs to the app |
| Runtime Bug | 1 | `prompt_user()` → `controller.prompt()` calls a deleted method — **will crash** if invoked |

**Total findings: 16 (15 judgement-call smells, 1 hard runtime bug)**

**Worst issue:** `prompt.py` calls a non-existent method on `HarnessTUI`. Any code path that reaches `prompt_user()` will crash with `AttributeError`. This is the only finding that represents an actual broken program state rather than a style/design smell.