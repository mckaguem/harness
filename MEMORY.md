# Oldstuff.md Report - Classic REPL / Non-TUI Code Paths

This report documents all occurrences of code related to the "classic REPL" (Rich/prompt_toolkit based REPL) that serves as a fallback when the TUI is not active. The goal is to identify what can be removed if we only support the TUI going forward.

## Summary

The codebase maintains a **dual-mode architecture**: the Textual TUI is the primary interface, but there's a fully functional fallback to the "classic REPL" (Rich console + prompt_toolkit) when the TUI fails or isn't available. This is **not dead code** — it's actively maintained and tested.

### Key Files with Classic REPL / Non-TUI Code Paths

| File | Type | Lines | Description |
|------|------|-------|-------------|
| `harness_core/__main__.py` | Entry point | 5-6, 259-271 | Main fallback logic: tries TUI, falls back to `user_loop()` (classic REPL) |
| `harness_core/agent/loop.py` | REPL loop | 50, 65, 226-231, 269 | `user_loop()` — the classic REPL loop; branches on `get_tui().is_active()` |
| `harness_core/terminal_io/display.py` | Display routing | 37-53, 116, 138, 152-154, 237-238, 280-282, 304-308 | `_tui_write()` routes to TUI or console; multiple branching points |
| `harness_core/terminal_io/prompt.py` | Input routing | 3-6, 11, 37-42, 44-73 | `prompt_user()` delegates to TUI or prompt_toolkit |
| `harness_core/terminal_io/tui.py` | TUI controller | 3-4, 16-17, 218, 440-476 | `HarnessTUI.is_active()` gate; `prompt()` method for TUI |
| `harness_core/commands/sub.py` | Sub-agent | 68 | Calls `user_loop()` directly for sub-agent conversations |

### Direct prompt_toolkit Usage

| File | Lines | Purpose |
|------|-------|---------|
| `harness_core/terminal_io/prompt.py` | 11, 44, 59, 64 | Creates `PromptSession` with `FileHistory("~/.history")` for classic REPL |
| `requirements.txt` | 1 | `prompt_toolkit` runtime dependency |
| `uv.lock` | 539-541 | Locked `prompt_toolkit-3.0.52` |

### Active Branching on `get_tui().is_active()`

The codebase has **15+ branching points** where behavior differs based on TUI availability:

1. `_emit_system_event` (loop.py:65) - falls back to `print_system()` for non-TUI
2. `_emit_control_event` (loop.py:75) - no-op in non-TUI
3. `user_loop` user message echo (loop.py:230) - only in non-TUI
4. Spinner events (loop.py:269) - no-op in non-TUI
5. `_tui_write` (display.py:37-53) - routes to console in non-TUI
6. `display_tool_call` (display.py:152-154) - standalone panel in non-TUI
7. `display_tool_result` (display.py:280-282) - standalone panel in non-TUI
8. `display_user_message` (display.py:304) - explains why echo needed in non-TUI
9. `prompt_user` (prompt.py:37-42) - delegates to prompt_toolkit in non-TUI

### Test Coverage for Classic REPL

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `tests/test_harness.py` | 8+ methods | Tests `user_loop()` directly with mocked `prompt_user` and display functions |
| `tests/test_user_loop_resilient.py` | 2 methods | Tests classic REPL loop survives provider errors (uses `_FakeTui.is_active() → False`) |
| `tests/test_tui.py` | 7+ methods | Verifies TUI routing (ensures classic path NOT taken when TUI active) |
| `tests/test_terminal_display.py` | 1+ methods | Tests display fallback rendering |

### Documentation/Comments Referencing Classic REPL

- `harness_core/__main__.py:5-6` — "falling back to the classic Rich/prompt_toolkit REPL. This is the historical behaviour."
- `harness_core/agent/loop.py:50, 65, 226, 269` — Multiple comments referencing "classic REPL"
- `harness_core/terminal_io/display.py:116, 237, 304` — "classic REPL mode", "classic (non-TUI) REPL"
- `harness_core/terminal_io/prompt.py:3-6, 23-30` — Documents both paths
- `harness_core/terminal_io/tui.py:3-4, 16-17` — "replaces the plain Rich/prompt_toolkit REPL"
- Wiki pages (8 files) and `AGENTS.md`, `code-review.md`

## What Would Need Removal for TUI-Only

If removing classic REPL support entirely:

1. **Delete** `harness_core/terminal_io/prompt.py` (or strip to TUI-only)
2. **Remove** `prompt_toolkit` from `requirements.txt` / `uv.lock`
3. **Simplify** `harness_core/__main__.py:259-271` — remove try/except fallback, just `launch(agent)`
4. **Simplify** `harness_core/agent/loop.py` — remove all `get_tui().is_active()` branches
5. **Simplify** `harness_core/terminal_io/display.py` — remove `_tui_write` branching, always route to TUI
6. **Simplify** `harness_core/terminal_io/tui.py` — remove `is_active()` gating, assume always active
7. **Update/Remove** tests in `test_harness.py`, `test_user_loop_resilient.py` that test classic REPL
8. **Update** documentation/comments throughout codebase and wiki
