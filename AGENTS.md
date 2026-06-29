# Project: Harness — Local Ollama Agent CLI

## What this is
A terminal-based chat harness that connects to a local LLM (via **Ollama**) and gives it five tools: `execute_bash`, `write_file`, `read_file`, `edit_file`, and `grep`. It's the runtime you're running inside.

## Running it
```bash
python harness.py            # uses OLLAMA_HOST env var, or http://localhost:11435
OLLAMA_HOST=http://… python harness.py   # custom Ollama endpoint
```

The model is hardcoded in `harness.py::main()` — change `MODEL_NAME` to switch.

## Operating constraints (enforced at runtime)
- All file reads/writes must stay **within the current working directory** (`is_safe_path` guard).
- Bash commands have a 30-second timeout.
- System prompt is prepended on every Ollama call — keep `system_prompt.txt` lean; put project conventions here instead of cramming them into it.

## Source-file summaries

### Top-level

| File | Purpose |
|------|---------|
| **`harness.py`** | Entry point. Builds the system prompt (base text + cwd listing + AGENTS.md), configures the Ollama client, and launches `run_loop`. |
| **`agent_loop.py`** | Interactive chat loop. Handles `/exit`, `/quit`, dispatches LLM responses to tool-call handlers (`execute_bash`, `write_file`, `read_file`, `edit_file`, `grep`), accumulates conversation history in a session file, and prints ANSI-colored boxes for each step. |
| **`tools.py`** | Tool schema definitions (`AGENT_TOOLS`) + implementations. Includes path-traversal safety checks, the edit engine (ordered search-and-replace), and a recursive `grep` with regex/glob/filter support and binary-file skipping. |
| **`model_utils.py`** | Ollama utilities: resolves the client's base URL, tokenizes prompts via `/api/tokenize`, and fetches the model's context length from `show` (with deep nested-key search and an 8K fallback). |
| **`system_prompt.txt`** | Base text of the system prompt, injected and extended by `harness.py::build_system_prompt()` each session. |
| **`requirements.txt`** | Python dependencies (ollama, etc.). |

### `terminal_io/` — Terminal I/O layer

| File | Purpose |
|------|---------|
| **`__init__.py`** | Package surface: re-exports the public API from all submodules so callers can do `from terminal_io import print_box, prompt_user`. |
| **`colors.py`** | ANSI color constants (`RESET`, `BOLD`, `DIM`, `CYAN`, `GREEN`, `BLUE`, `YELLOW`, `RED`, `MAGENTA`) and the `c(text, colour)` helper for wrapping text in color. |
| **`boxes.py`** | Box-drawing UI: `print_box()` renders a colored box with title bar, wrapping body text (ANSI-aware), and Unicode borders per style (`system`, `user`, `agent`, `tool_call`, `tool_result`). |
| **`display.py`** | High-level display helpers (`print_system`, `display_user_prompt`, `display_tool_call`, `display_tool_result`, `display_tool_success`, `display_error`) that coordinate boxes, markdown rendering, and truncation. |
| **`prompt.py`** | User-input prompt with readline support (arrow keys, history). |
| **`trunc.py`** | Text truncation helpers — caps displayed output to `MAX_DISPLAY_LINES` lines so long tool results don't flood the terminal. |
| **`speed.py`** | Formats token-per-second speed for Ollama chat responses. |

### `terminal_io/markdown/` — Markdown rendering subpackage

| File | Purpose |
|------|---------|
| **`__init__.py`** | Re-exports the three main renderers: `display_agent_response`, `_render_table`, `_render_code_block`. |
| **`helpers.py`** | Orchestrates markdown rendering — splits content into inline/block regions, renders them, formats speed/context metadata, and prints the final colored box. |
| **`blocks.py`** | Block-level renderers for tables (using Unicode box-drawing chars with alignment) and fenced code blocks. |
| **`inline.py`** | Inline transforms — bold (`**x**`) → BOLD ANSI, italic/strong-italic (`*x*`, `***x***`) → DIM ANSI, inline code → blue+bold monospace. |

### `terminal_io_backup.py`
Legacy backup of the old terminal I/O module (pre-subpackage refactor). Safe to ignore.

### `tests/` — Test suite

| File | Purpose |
|------|---------|
| **`__init__.py`** | Empty package marker. |
| **`test_tools.py`** | Tests for tool implementations: path safety, read/write/edit/grep behavior, error paths. |
| **`test_edit_file.py`** | Focused tests on the `edit_file` engine — chained edits, missing old_text errors, empty-edits guard. |
| **`test_grep.py`** | Tests for `grep`: literal/regex matching, file filters, binary skipping, path-traversal rejection, max_matches capping. |
| **`test_terminal_io.py`** | Tests for terminal I/O helpers: ANSI-safe length measurement, box printing, markdown rendering outputs. |

## Conventions to follow
1. **Prefer the existing box-print helpers** (`print_box`, role-specific wrappers) for any output that touches the terminal — they handle ANSI-aware wrapping, colour coding, and truncation. Don't raw `print` long text.
2. **Keep tool calls in `tools.py`** — new capabilities go there as both a schema entry (so Ollama knows about them) *and* an implementation function.
3. **Tests mirror source layout.** Add a test class alongside any new logic, and run with `pytest tests/`.
4. **Don't modify `system_prompt.txt` lightly** — the harness augments it automatically each session (cwd listing + AGENTS.md). Overcrowding it bloats every request.
