# Project: Harness — Local Ollama Agent CLI

## 1. Project Overview & Mission

- **Core Objective:** A terminal-based, self-contained agent runtime that connects to a local LLM (via Ollama) and equips it with sandboxed tools — bash execution, file I/O, recursive grep, and sub-agent delegation — for autonomous coding, analysis, and sysadmin work with zero cloud dependencies.
- **Operating Boundary:** Everything runs inside the current working directory. Path traversal outside CWD is blocked by design.

## 2. Technical Stack & Architecture (brief)

| Layer | Technology |
|-------|-----------|
| **Language & Runtime** | Python 3.14+ (uses `str | None` hints, walrus operators, and strict typing) |
| **LLM Client** | `ollama` — local Ollama instance (default host overridable via `OLLAMA_HOST`) |
| **Terminal UI** | `rich` (color, Unicode boxes, highlighting); `prompt_toolkit` for input history/tab completion |
| **Config** | `pyyaml` — agent definitions and skills live as YAML under `.harness_py/` |
| **Pattern** | Modular package with a generator-driven conversation loop; zero-registration auto-discovery for tools and sub-agents |

**Layout (verify live with `list_dir` — do not rely on a hardcoded tree):**
- `harness_core/` — the Python package. Entry point is `harness_core/__main__.py` (run with `python -m harness_core`). Subpackages: `agent/`, `commands/`, `model/`, `session/`, `skills/`, `terminal_io/`, `tools/`.
- `.harness_py/` — runtime config: agent YAMLs under `agents/`, skills under `skills/`, plus `config.yaml`.
- `tests/` — pytest suite mirroring source (`test_<module>.py`).
- `docs/` — `original_source.py` (the archived monolith this was refactored from — do NOT modify), `skills_spec.md`, `speculative_features.md`.
- `sample_config/`, `plan.md`, `PROGRESS.md`, `TODO.md`, `pyproject.toml`, `requirements.txt`, `uv.lock`.


### Event System

Harness uses an async mailbox-pattern EventBus (`harness_core/eventbus.py`). All event topics are documented in [`docs/events.md`](docs/events.md) — see that file for the full catalog (16 topics across `agent.session.*`, `agent.status.*`, `agent.tool.*`, `agent.turn.*`, `agent.tasklist.*`, `process_control.*`, and `tui.*` namespaces).

Key facts:
- **No centralized topic constants.** Topic strings are defined inline at each publish site. The only exceptions are `PROCESS_CONTROL_QUIT` / `PROCESS_CONTROL_QUIT_CONFIRM` in `event_types.py:321-322`.
- **Three subscribers:** (1) TUI listener (`HarnessEventListener`, id `"tui"`) subscribes to 13 topics via `TUI_TOPICS` in `wiring.py`; (2) Agent's own `EventListenerLoopMixin` auto-discovers `tui.user.input`; (3) `Manager._ShutdownListener` explicitly listens on the two process_control topics.
- **No tools or skills publish events.** Only `agent/mixin.py`, `agent/task_list.py`, `commands/exit_quit.py`, and `terminal_io/tui_app.py` are publish sites.
- **Sender filtering** is applied at subscription time via `filter_by_sender()` decorator in `eventbus.py`.

## 3. Agent Persona & Operational Rules

- **Role:** Autonomous, senior engineer in a terminal runtime with sandboxed shell/file access, bounded by path-safety guards.
- **Behavior:** Be concise and direct; skip filler. Prioritize readability over clever micro-opts. **Do not guess** — if a requirement or API contract is ambiguous, stop and ask. Prefer targeted edits (`edit_file`) over full rewrites; partial failures should leave files untouched.
- **Enforced constraints:**
  - All file ops gated by `is_safe_path()` — traversal outside CWD is blocked.
  - Bash commands have a **30-second timeout** (`TimeoutExpired` → red error).
  - Sub-agent spawns are **isolated sessions** with no shared conversation history.
  - Tools/skills are **auto-discovered** — adding a file is enough; no manual registration.

## 4. Coding Standards (lean)

- **Type hints on public APIs** (`str | None`). Keep code self-documenting; docstrings only when non-obvious.
- **Fail closed on security.** Every path op calls `is_safe_path()` first. Return a typed error tuple — never raise uncaught exceptions that could leak paths to the LLM.
- **Formatting:** ~88-char line length (don't exceed ~120 unjustified); f-strings; single quotes for strings, double quotes for docstrings. Imports top-of-file: stdlib → third-party → local.
- **Don't fabricate.** Verify specifics by reading the code or using `list_dir`/`grep`; don't invent file paths or APIs.

## 5. Testing & Workflow Guardrails

- **Tests:** pytest. Run `pytest tests/`. Mirror naming: `test_<module>.py`. Tests use `tmp_path`, manual `os.chdir()`, and `unittest.mock.patch`. Every new tool/agent needs a mirror test.
- **Type checking:** `mypy` is the project's static type checker. Run `mypy harness_core tests` from the repo root and ensure it reports zero errors before committing. Keep type hints accurate on public APIs; add missing `typing` imports (`Dict`, `Callable`, `Optional`) and package type imports as needed, and prefer `Optional[...]` / `X | None` over implicit `Optional` defaults. If you must suppress a third-party import without stubs, record it in the `[tool.mypy]` section of `pyproject.toml` (prefer installing real stubs like `types-PyYAML` first).
- **Edits:** Use targeted `edit_file` (supports multiple ordered replacements atomically) over full rewrites.
- **Breaking changes:** Alert the user if a change breaks type definitions, tool schemas, or architectural boundaries. Never remove a `tools/` file that has tests, and never modify an agent YAML's tool list without confirming intent.
- **Adding tools:** drop a `.py` in `harness_core/tools/` with a module-level `function_def` + matching callable — auto-discovered. Add a mirror test.
- **Adding agents:** add YAML under `.harness_py/agents/` (required: `name`, `model_name`); missing `model_name` fails at load time.
- **Display:** Always render terminal output through `terminal_io` helpers (`print_box`, role-specific display functions, `display_agent_response()` for Markdown). Never raw-print long text.

## 6. Non-Obvious Security Rules

- **Fail closed on security / never leak paths.** Catch specific exceptions (FileNotFoundError, PermissionError, TimeoutExpired) and wrap with descriptive but non-path-disclosing context.
- Treat `docs/original_source.py` as archive-only; it is the pre-refactor monolith and must not be edited.

## Logging Standards

The harness uses Python's stdlib `logging` module for all diagnostic output. Never use bare `print()` or `sys.stderr.write(...)` as a substitute for logging in production code paths (only interactive prompts and user-facing CLI help are exempt).

### Unified Log Format

All log handlers MUST use this format string:
```
%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s
```
- `%(asctime)s` — ISO-8601 timestamp (use `datefmt='%Y-%m-%dT%H:%M:%S'` to control formatting).
- `%(name)-20s` — module-level logger name, left-aligned for easy column scanning.
- `%(levelname)-7s` — DEBUG/INFO/WARNING/ERROR/CRITICAL padded to 7 chars.
- `%(message)s` — the formatted message text.

Example output line:
```
2025-01-15T14:32:01 | harness_core.eventbus    | INFO    | Starting EventListener for agent main
```

### Log-Level Standard (when to use each level)

| Level   | When to log                                                                 |
|---------|-----------------------------------------------------------------------------|
| DEBUG   | Internal state changes, variable dumps, branch selection, handler lookup.  |
| INFO    | Start/stop of subsystems, agent status transitions, user-facing milestones.|
| WARNING | Recoverable problems: missing optional config, retrying a failed call, non-fatal validation failure. |
| ERROR   | Failures that abort an operation but let the system keep running (tool dispatch error, failed network call). |
| CRITICAL| System is unusable and must shut down immediately. Rare.                    |

### Logger Pattern

Every module MUST declare a named logger at module top level:
```python
import logging
logger = logging.getLogger(__name__)
```
Never call `logging.debug(...)` / `logging.info(...)` etc. directly — always go through the module-level `logger`. Never import `logging` inside a function body; keep it at file scope.

### Logging Exception Blocks

Every `except:` block MUST log the exception with full traceback:
```python
except Exception as e:
    logger.exception("Failed to do X for agent %s", agent_id)
```
Use `logger.exception(...)` (NOT `logging.exception(exc)` — that is a bug; see below). The call reads from `sys.exc_info()` automatically so no argument is passed. Include enough context in the message template so the log line is self-describing.

**Anti-pattern to avoid:**
```python
logging.exception(exc)   # ❌ TypeError: exception() takes no arguments (1 given)
                          #    Also, the TypeError gets swallowed by this try/except → silent failure.
```

### Configuration (set in `__main__.py`)

`basicConfig` is called once at import time with two handlers: a file handler (`<CWD>/.sessions/harness.log`, append mode) and a StreamHandler on stderr for console output during development. Both share the unified format. The root logger level honors the `--log-level` CLI flag (default INFO); DEBUG-only messages go to the log file regardless.

### What NOT to do
- Do not use `warnings.warn()` as a logging substitute. Use `logger.warning(...)` instead.
- Do not add new bare `print()` / `sys.stderr.write()` for diagnostics. Interactive prompts and help text are fine; anything else goes through `logging`.
