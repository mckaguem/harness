# Code Review Report: harness_core

## Hard Violations (AGENTS.md Standards)

| File:Line | Issue | AGENTS.md Reference |
|-----------|-------|---------------------|
| `agent/core.py:44-60` | Broad `Exception` catch + raw `print()` warning | §4: "Fail closed on security", "Never raw-print long text" |
| `session/session.py:114-142` | `_auto_save_session()` catches bare `Exception`, prints to stderr | §4: "Catch specific exceptions... wrap with descriptive but non-path-disclosing context" |
| `agent/loop.py:82-85` | Bare `except Exception: pass` silently swallows errors | §4: "never silently swallow" |
| `tools/execute_bash.py:31-33`, `grep.py:121-126` | Catch-all `Exception` returning error results | §4: "Catch specific exceptions" |
| `eventbus.py:294-311` | Deeply nested try/except with multiple bare catches + silent `pass` | §4: "Catch specific exceptions", "never silently swallow" |

**All 5 violations** stem from the same root cause: using bare `except Exception` instead of specific exception types, combined with improper output handling (raw `print`/`stderr` vs. `terminal_io` helpers).

---

## Fowler Smells (Judgement Calls)

| Smell | Locations | Impact |
|-------|-----------|--------|
| **Mysterious Name** | `types.py:16` (`_SYSTEM_VARIABLES`), `loop.py:31` (`_count_approx_tokens` used publicly) | Reduced readability |
| **Data Clumps** | `types.py:124-178` (5 params to `_build_system_prompt`), `config.py:200-247` (dict vs. dataclass) | Coupling, refactor resistance |
| **Feature Envy** | `core.py:293-309` (`spawn_subagent` reaches across modules), `types.py:293-298` | Misplaced responsibility |
| **Message Chains** | `core.py:84-90` → `session.py:26-47` (6+ constructor params) | Fragile instantiation |
| **Primitive Obsession** | `types.py:31-32` (raw `str`/`ProviderConfig`), `config.py:226-247` (raw dict return) | Domain logic leakage |
| **Shotgun Surgery** | Agent creation in `Agent.__init__`, `from_file`, `spawn_subagent`, `AgentType.from_file` | Change amplification |
| **Middle Man** | `executor.py` `ToolExecutor` only delegates to `dispatcher.dispatch` | Unnecessary indirection |
| **Speculative Generality** | `eventbus.py` dynamic `handle_<topic>` dispatch | Over-engineering |
| **Duplicated Code** | `execute_bash.py` & `grep.py` identical error-handling pattern | Maintenance burden |
| **Divergent Change** | `loop.py` mixes TUI, compression, commands, REPL | Low cohesion |

---

## One-Line Summary

**Hard violations require immediate fix (bare exception handling + raw prints); Fowler smells indicate architectural refactoring opportunities to improve cohesion and reduce coupling.**