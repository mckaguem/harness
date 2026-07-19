---

# Refactoring Plan for `harness_core/terminal_io`

This plan addresses the 16 findings (15 smells, 1 hard bug) from the code review of the terminal_io module. Organized by priority and dependency order.

## Phase 0 — Fix the Hard Bug (Do First)
**Blocker: everything else depends on this being resolved.**

| # | Action | Files | Risk |
|---|--------|-------|------|
| 1 | Remove `prompt_user()` from `prompt.py` or restore a stub `prompt()` method on `HarnessTUI`. Audit all callers first — grep for `prompt_user` across the repo. If no callers remain, delete `prompt.py`. | `prompt.py`, `harness_tui.py`, `__init__.py` | Low |

---

## Phase 1 — Remove Debug Artifacts & Dead Code
**Low risk, immediate cleanup.**

| # | Action | Files | Smell Addressed |
|---|--------|-------|-----------------|
| 2 | Delete module-level `thecount = 0` and all references to it in `action_submit_input()`. The count display is debug scaffolding. | `tui_app.py` (lines 16, 244–250) | Mysterious Name |
| 3 | Remove unused imports: `Footer`, `Header` from textual.widgets; any other lint-flagged imports. | `tui_app.py` (line 7) | Mysterious Name |
| 4 | Replace `print(listener)` with `logging.debug()` in `TextualHarnessApp.__init__`. Remove bare `traceback.print_exc()`. | `tui_app.py` (lines 92–95) | Mysterious Name |
| 5 | Delete the dead/abandoned code block in `update_sidebar_tasks_from_payload` (commented-out `_do()` and `call_from_thread`). | `tui_app.py` (lines 141, 148–151) | Divergent Change |

---

## Phase 2 — Extract Repeated Patterns
**Medium risk. Reduces code volume significantly.**

| # | Action | Files | Smell Addressed |
|---|--------|-------|-----------------|
| 6 | Extract `_marshal(fn, app)` helper in `harness_tui.py` that handles the thread-id check + branch on equality. Replace 4 copies of this pattern in `write()`, `begin_tool_panel()`, `complete_tool_panel()`, and its standalone fallback. | `harness_tui.py` | Duplicated Code |
| 7 | Extract `_with_sidebar(callback)` helper in `TextualHarnessApp` that handles the `is_running` guard + query_one sidebar pattern shared by `update_sidebar_usage`, `update_sidebar_tasks_from_payload`, and `update_sidebar_model_name`. | `tui_app.py` (lines 109–165) | Duplicated Code |
| 8 | Rename `_theme_border()` to a clearer name or inline it — it's only called from `display_message_panel()`. | `display.py` (line 121) | Mysterious Name |

---

## Phase 3 — Improve Naming & Readability
**Low risk. Pure refactoring.**

| # | Action | Files | Smell Addressed |
|---|--------|-------|-----------------|
| 9 | Rename parameter `input` → `user_input` in `HarnessTUI.bind()`. | `harness_tui.py` (line 58) | Mysterious Name |
| 10 | Rename `_LAST_TOOL_PANEL` to a typed class or rename to `_pending_tool_panel` with clearer field names. Better long-term: move ownership of this state into `HarnessTUI` so it lives alongside the tool stack. | `display.py` (line 24) | Mysterious Name |
| 11 | Rename `subscribeToStuff()` → `register_subscriptions()` in `event_listener.py`. | `event_listener.py` (line 104) | Mysterious Name |

---

## Phase 4 — Reduce Handler Boilerplate
**Medium risk. Requires understanding of the event dispatch chain.**

| # | Action | Files | Smell Addressed |
|---|--------|-------|-----------------|
| 12 | Replace the repetitive handler methods in `TopicHandlers` with a topic→handler registry pattern. Define a mapping like `{ "agent.tasklist.initialize": (_refresh, TaskListPayload), ... }` and a single dispatch method that type-checks payload and calls the right handler. This eliminates ~80% of the 13 handler methods. | `event_handlers.py` | Duplicated Code |
| 13 | Remove `_make_refresh_handler()` and `_make_system_message_handler()` factory closures — no longer needed with a registry pattern. | `event_handlers.py` (lines 23–44) | Mysterious Name / Duplicated Code |

---

## Phase 5 — Improve Cohesion
**Higher risk. Consider doing incrementally.**

| # | Action | Files | Smell Addressed |
|---|--------|-------|-----------------|
| 14 | Split `TaskListSidebar` in `widgets.py` into separate concerns: model-name display, usage text display, task list rendering. Each can remain as methods on one class (they're all "sidebar" related), but document the boundaries clearly and consider extracting the markdown rendering into a dedicated helper. | `widgets.py` | Divergent Change |
| 15 | Convert TUI controller's passthrough methods (`update_sidebar_usage`, `update_sidebar_tasks_from_payload`, `update_sidebar_model_name`) — either inline them at call sites (if callers are few) or document why the indirection exists. The methods currently own no logic beyond forwarding. | `harness_tui.py` (lines 220–248) | Middle Man |
| 16 | Document `_on_exit` parameter in `TextualHarnessApp.__init__` — either wire it to a real callback mechanism or remove it as speculative generality that never materialized. | `tui_app.py` (line 74) | Speculative Generality |

---

## Execution Order Summary

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
   │          │         │         │         │          │
  Bug fix   Cleanup    Reduce     Names   Refactor   Cohesion
            (fast)    duplication              (boiler-   (design)
                                          plate)
```

**Estimated effort:** Phases 0–1 (~30 min), Phase 2 (~45 min), Phase 3 (~15 min), Phase 4 (~60 min), Phase 5 (~90 min). Total ~4 hours.

---

## Validation Strategy

After each phase:
1. Run existing tests in `tests/test_terminal_io.py` and `tests/test_tui.py`.
2. Verify the TUI still launches (non-blocking smoke test).
3. Check that no new import errors appear (`python -c "from harness_core.terminal_io import *"` ) after each phase.

## Notes

- No coding standards exist in this repo, so the baseline is Fowler's smell catalog only. Linting tools (ruff/flake8) are not configured — consider adding one as a separate task to catch these issues automatically in the future.