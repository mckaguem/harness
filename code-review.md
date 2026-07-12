# Code Review — Harness Codebase

Reviewed against `/workspaces/harness/AGENTS.md` (authoritative standards) plus the Fowler smell baseline. The git working tree is clean (committed at `007fe2a`), so the full committed source under `harness_core/` and `tests/` was reviewed directly. Auto-discovery modules (`tools/__init__.py`, `agent/discovery.py`, `skills/discovery.py`) remain zero-registration compliant.

## Documented-standard breaches (HARD, per AGENTS.md)

1. **Rule 3 — Fail closed / path leak (AGENTS.md §4):** `tools/grep.py:57` skips `is_safe_path()` (inline re-implementation); `:105` leaks an absolute path to the LLM; `tools/run_subagent.py:181` embeds absolute paths in `FileNotFoundError` messages; `tools/list_dir.py:147` duplicates the safety guard instead of calling it.
2. **Rule 4 — No silent swallow (AGENTS.md §4):** `tools/grep.py:119` `except Exception: continue`; `session/session.py:113` `except Exception: pass` silently drop errors.
3. **Rule 1 — Type hints (AGENTS.md §4):** Pervasive use of `Optional/List/Dict` and `str=None` / `dict=None` defaults instead of the required `X | None` union syntax.
4. **Rule 8 — Display rules (AGENTS.md §6):** Raw `print()` calls in `agent/loop.py`, `skills/discovery.py`, `commands/compress.py`, and `terminal_io/prompt.py:68`, bypassing the `terminal_io` helpers.
5. **Concrete defects:**
   - `terminal_io/display.py:262` mutable `dict={}` default argument.
   - `agent/core.py` `loop_count` never increments on the normal path → dead loop ceiling (potential infinite loop).
   - `model/provider.py:347` async path omits the sync `_to_responses_input` normalization (latent HTTP 400).
6. **Testing (Rule 7 — AGENTS.md §4):** Missing mirror test files; function-style suites instead of class-based `class TestX:`; `test_harness.py` loop tests with zero assertions; `test_dispatcher.py` writes to the real CWD without asserting results.

## Baseline smells (JUDGEMENT CALLS only — possible X, not violations; repo standard overrides)

- **Duplicated Code:** `session/session_utils.py` identical sibling branches; sync/async drift between the two `provider.py` code paths.
- **Speculative Generality:** `provider_type="auto"` is accepted but ignored; dead collision/pattern helper functions.
- **Feature Envy:** `agent/core.py:220` reaches into `_session._injected_text`; `commands/compress.py:21` does `getattr(agent, '_session', None)`.
- **Middle Man:** `initialize_task_list` / `update_task_status` carry a dead `tuple | ToolResult` union that is never constructed.

Total findings: 10 (6 hard standard breaches, 4 judgement-call smells). Worst issue: `agent/core.py` loop ceiling never increments — a potential infinite loop, compounded by path-leak violations of the fail-closed security rule.
