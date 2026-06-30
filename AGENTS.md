# Project: Harness — Local Ollama Agent CLI

## What this is
A terminal-based chat harness that connects to a local LLM (via **Ollama**) and gives it tools for executing bash commands, reading/writing/editing files, recursive grep search, and spawning specialized sub-agents. It's the runtime you're running inside.

## Running it
```bash
python harness.py            # uses OLLAMA_HOST env var, or http://localhost:11435
OLLAMA_HOST=http://… python harness.py   # custom Ollama endpoint
```

The model is hardcoded in `harness.py::main()` — change `MODEL_NAME` to switch. The default is `hf.co/deepreinforce-ai/Ornith-1.0-35B-GGUF:Q6_K` with a 2^17 (131072) token context window.

## Operating constraints (enforced at runtime)
- All file reads/writes must stay **within the current working directory** (`is_safe_path` guard).
- Bash commands have a 30-second timeout.
- Only one tool call per LLM response — loop repeats until the model yields a plain RESPONSE.
- System prompt is prepended on every Ollama call — keep `system_prompt.txt` lean; put project conventions here instead of cramming them into it.

## Agent Types

Five agent configurations are defined as YAML files in `agents/`. Each specifies a name, model, system prompt path, and allowed tool set.

| Agent | Model | Tools | Role / Purpose |
|-------|-------|-------|----------------|
| **main** | Ornith-1.0-35B (Q6_K) | All (`*`) | Primary conversational agent loaded by `harness.py`. Full autonomy. |
| **analyst** | Ornith-1.0-35B | `read_file`, `grep` | Code analysis and research — reads files, searches codebases. |
| **coder** | Ornith-1.0-35B | `execute_bash`, `write_file`, `read_file`, `edit_file` | Writing and executing code changes on disk. |
| **writer** | Ornith-1.0-35B | `write_file`, `read_file` | Document and content writing without shell access. |

Sub-agents are launched via the `/sub <name>` slash command (interactive) or the `run_subagent` tool (programmatic). Each has a dedicated system prompt in `agents/prompts/`.

You should make use of the `run_subagent` tool for tasks where you don't need to know all of the details, such as:

- summarise the contents of a file
- make a git commit
- summarise the contents of a directory
- other tasks which would require looking at a lot of data, but where you only want 

If you are a subagent, you can also make calls to `run_subagent` for sub-tasks, such as:

- summarising a single file when asked to summarise a directory (repeated for each file)
- updating documentation in a single file when asked to update documentation in a directory (repeated for each file)
- other tasks which can be divided up into smaller tasks that are mostly independent, and for which you don't need to know the details.

Prefer to run several subagents whenever the task can be reasonably broken down into subtasks.


## Source-file summaries

### Top-level

| File | Purpose |
|------|---------|
| **`harness.py`** | Entry point. Wires up configuration, builds the system prompt (base text + cwd listing + AGENTS.md), creates the main `AgentType`, and launches `user_loop`. |
| **`model_utils.py`** | Ollama utilities: resolves the client's base URL, tokenizes prompts via `/api/tokenize` for accurate counting, and fetches context length from `show` (with deep nested-key search and an 8K fallback). |
| **`original_source.py`** | Archive of the original monolithic single-file implementation the project was refactored from. Reference only — do not modify. |
| **`system_prompt.txt`** | Base system prompt text, augmented at runtime by `build_system_prompt()` with cwd listing + AGENTS.md contents each session. Role definition and operating rules live here. |
| **`requirements.txt`** | Python dependencies: `ollama`, `pyyaml`. |

### `agent/` — Agent runtime package

| File | Purpose |
|------|---------|
| **`__init__.py`** | Re-exports public API: `AgentType`, `Agent`, `CURRENT_AGENT`, status constants (`RESPONSE`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`), and utilities (`filter_tool_schemas`, `build_system_prompt`, `user_loop`). |
| **`core.py`** | Core `Agent` class (~240 lines). Manages conversation state via a `messages` list. `handle_prompt()` is a generator yielding `(kind, *args)` tuples that drive the LLM call loop: calls Ollama → checks for tool_calls → dispatches via `tools.dispatcher` → appends results → repeats until RESPONSE. `inject_text()` enables cross-agent communication; `spawn_subagent()` classmethod creates an agent from `agents/*.yaml` inheriting host/context length; `summarize()` builds a temporary transcript and sends it to the LLM for a bulleted summary without persisting. |
| **`loop.py`** | Interactive chat loop (`user_loop`). While-True: prompts user via `prompt_user()`, checks slash commands (`/exit`, `/quit`, `/sub`) from `COMMANDS` dict, otherwise calls `agent.handle_prompt(user_input)` and displays each yielded output based on kind. Supports optional `on_exit` callback for post-session summarization. |
| **`types.py`** | `AgentType` dataclass (~90 lines): `name`, `model_name`, `system_prompt_path`, `system_prompt`, `agent_tools`. `_build_system_prompt()` static method loads the base prompt and injects cwd + AGENTS.md. `from_file(path)` classmethod loads YAML config, validates required fields (model_name mandatory), and builds the augmented system prompt. |
| **`utils.py`** | Shared utilities (~50 lines). `filter_tool_schemas(agent_type, all_schemas)` returns only schemas whose function names match the agent's tool list (raises ValueError for missing tools). `build_system_prompt(base_prompt_path="system_prompt.txt")` reads the base file and appends cwd listing + AGENTS.md. |

### `agents/` — Agent definitions directory

| File / Dir | Purpose |
|------------|---------|
| **`main.yaml`** | Primary agent config: all tools, system prompt from root `system_prompt.txt`. Loaded by harness.py as the default agent. |
| **`analyst.yaml`** | Analyst sub-agent: code analysis and research with `read_file`, `grep`. Prompt at `agents/prompts/analyst.txt`. |
| **`coder.yaml`** | Coder sub-agent: writing/executing code changes with `execute_bash`, `write_file`, `read_file`, `edit_file`. Prompt at `agents/prompts/coder.txt`. |
| **`sysadmin.yaml`** | Sysadmin sub-agent: system administration tasks with `execute_bash`, `read_file`. Prompt at `agents/prompts/sysadmin.txt`. |
| **`writer.yaml`** | Writer sub-agent: document and content writing with `write_file`, `read_file`. Prompt at `agents/prompts/writer.txt`. |
| **`prompts/`** | Directory containing `.txt` system prompt files for each specialized agent. |

### `commands/` — Slash command handlers

| File | Purpose |
|------|---------|
| **`__init__.py`** | Slash command handler registry (~40 lines). Maps `'exit'`, `'quit'`, `'sub'` to handler functions via the `COMMANDS` dict. Handlers receive `(rest, agent)` and return bool (True = break loop for exit/quit). |
| **`sub.py`** | Sub-agent interactive session handler (~70 lines). Implementation of `/sub <name>`: validates name, lazy-imports `Agent` + `user_loop`, calls `Agent.spawn_subagent()`, handles `FileNotFoundError` gracefully, prints a status banner with model name. Defines `_on_exit` callback that calls `agent.summarize()` then injects the formatted summary back into the parent agent via `parent_agent.inject_text()`. |

### `tools/` — Tool implementations

A file in this package is treated as a "skill" if it defines `function_def` at the top level. The package auto-discovers these files to build `AGENT_TOOLS` and its dispatch registry — no manual registration needed.

| File | Purpose |
|------|---------|
| **`__init__.py`** | Self-discovering skill loader (~60 lines). Scans the package directory for modules with a top-level `function_def`, loads each `.py` via `importlib.util.spec_from_file_location`, validates it's a dict, and uses `function.name` as the registry key. Populates module-level `AGENT_TOOLS` (schema list) and `DISPATCH_REGISTRY` (name→module). Calls `_build()` at import time for auto-discovery. `__getattr__` re-exports tool callables for backwards compatibility (`from tools import execute_bash`). |
| **`dispatcher.py`** | Runtime tool invocation router (~15 lines). `dispatch(func_name, args)` looks up the function in `DISPATCH_REGISTRY`, retrieves it by attribute name from the corresponding module, calls it with keyword arguments via `fn(**args)`, and returns the result string. Raises KeyError for unknown tools. |
| **`utils.py`** | Shared path safety guard (~15 lines). `is_safe_path(filename)` resolves both cwd and target paths and checks that the target is relative to cwd. Returns False on any exception (catches permission errors, invalid paths). Used by all file-modifying tools to prevent directory traversal attacks. |
| **`execute_bash.py`** (~35 lines) | Shell command execution. `execute_bash(command)` runs `subprocess.run` with shell=True, capture_output=True, text=True, 30-second timeout. Combines stdout+stderr (prefixed "STDERR:" marker). Returns colored error messages for TimeoutExpired or general exceptions. Schema: name="execute_bash", parameters={command:string required}. |
| **`write_file.py`** (~30 lines) | File writing with safety guard. `write_file(filename, content)` validates path safety first (returns RED error if unsafe), then writes in write mode ('w') with utf-8 encoding. Returns GREEN success or RED error on exception. Schema: name="write_file", parameters={filename:string required, content:string required}. |
| **`read_file.py`** (~35 lines) | File reading with safety guard. `read_file(filename)` validates path first (returns RED error if unsafe), then reads in read mode ('r') utf-8. Prints a terminal message showing filename + character count (DIM colored). Returns content string or RED error for FileNotFoundError/other exceptions. Schema: name="read_file", parameters={filename:string required}. |
| **`edit_file.py`** (~100 lines) | Ordered search-and-replace engine with validation. `edit_file(filename, edits)` validates the edits list is non-empty, checks path safety once upfront, reads existing content, then iterates through edits sequentially — each finds first occurrence of old_text in current (already-modified) content and replaces it with new_text. Tracks changes_made with line counts. If any old_text not found, returns RED error listing the problematic edit and first 3 lines of expected text for debugging. Writes only if different from original. Schema: name="edit_file", parameters={filename:string required, edits:[{old_text:string, new_text:string}] array required}. |
| **`grep.py`** (~180 lines) | Recursive file search with regex support and filtering. `grep(pattern, path, use_regex=False, file_filter=None, max_matches=50)` validates inputs, resolves target within cwd (returns RED error if outside), compiles regex if requested. Decides between single-file or recursive directory walk via os.walk(). Prunes __pycache__, .git/, and dot-directories from traversal. Skips binary files (_is_binary checks for null bytes in first 8KB). Applies file_filter glob/suffix matching. Reads line-by-line, caps matches at max_matches. Returns "file:line — content" format per match with a GREEN summary showing count and "(limited to N)" if capped. Schema: name="grep", parameters={pattern:string required, path:string required, use_regex:boolean optional, file_filter:string optional, max_matches:int optional}. |
| **`run_subagent.py`** (~50 lines) | Programmatic (non-interactive) sub-agent invocation. `run_subagent(sub_agent, task)` calls `Agent.spawn_subagent()` without an explicit parent (falls back to CURRENT_AGENT ContextVar). Iterates through `sub.handle_prompt(task)` generator, captures the final RESPONSE yield as result_text. Returns "(sub-agent produced no output)" if empty. Catches FileNotFoundError and general exceptions. Schema: name="run_subagent", parameters={sub_agent:string required, task:string required}. |

### `terminal_io/` — Terminal I/O layer

| File | Purpose |
|------|---------|
| **`__init__.py`** | Package surface: re-exports the full public API from all submodules — display helpers, colors, boxes, markdown rendering, prompt handling, truncation, and speed formatting. Single import point for callers. |
| **`colors.py`** | ANSI color constants (`RESET`, `BOLD`, `DIM`, `CYAN`, `GREEN`, `BLUE`, `YELLOW`, `RED`, `MAGENTA`) and the `c(text, colour)` helper wrapping text in escape sequences. Used throughout tools/ for error/success messaging. |
| **`boxes.py`** | Box-drawing UI component. `print_box(title, content, style)` renders a colored box with title bar, ANSI-aware body text wrapping, and Unicode borders. Styles: `'system'`, `'user'`, `'agent'`, `'tool_call'`, `'tool_result'` — each with different border characters and colors for visual distinction between message types. |
| **`display.py`** | High-level display coordination (~5 functions). `print_system(title, content)` renders system message box; `display_user_prompt(text)` shows user input in styled box; `display_tool_call(func_name, args_str)` displays tool calls with function name and formatted JSON args; `display_tool_result(func_name, result)` shows execution output; `display_error(description)` renders error messages in red. |
| **`prompt.py`** | User input prompt with readline support. `prompt_user()` returns user-typed string with arrow key navigation, command history, and tab completion via Python's readline module. |
| **`trunc.py`** | Text truncation helpers for display control. Caps output to `MAX_DISPLAY_LINES` lines so long tool results don't flood the terminal. Preserves beginning/end of truncated text with "[...]" indicators. Used by display functions before rendering large outputs. |
| **`speed.py`** | Token-per-second speed formatting for Ollama chat responses. Extracts timing metrics from the response object and formats as "X tokens/sec" string for display in agent response headers. |

### `terminal_io/markdown/` — Markdown rendering subpackage

| File | Purpose |
|------|---------|
| **`__init__.py`** | Re-exports three main renderers: `display_agent_response`, `_render_table`, `_render_code_block`. Public API for markdown content rendering. |
| **`helpers.py`** | Orchestrates the markdown-to-terminal rendering pipeline. `display_agent_response(content, ollama_response, context_length, speed)` splits content into inline/block regions, renders them appropriately (tables as Unicode boxes, code blocks with syntax highlighting), formats speed/context metadata headers, and prints the final colored box via `terminal_io.print_box`. |
| **`blocks.py`** | Block-level renderers for complex markdown elements. `_render_table(rows)` uses Unicode box-drawing characters (┌─┬┐│├─┼┤└─┴┘) with column alignment based on content width; `_render_code_block(content, language)` displays fenced code blocks with optional language label, monospace formatting, and background color differentiation. |
| **`inline.py`** | Inline element transformers. Handles bold (`**text**`) → BOLD ANSI, italic (`*text*`) → DIM ANSI, strong italic (`***text***`) → DIM+BOLD combination, inline code (`` `code` ``) → blue+bold monospace formatting. |

### `tests/` — Test suite

| File | Purpose |
|------|---------|
| **`__init__.py`** | Empty package marker. |
| **`test_tools.py`** | Tests for core tool implementations: execute_bash (command execution, timeout handling), write_file (write operations, path safety), read_file (read operations, missing file errors). Validates basic functionality and error paths. |
| **`test_edit_file.py`** | Focused tests on the edit_file engine: chained edits apply sequentially with correct line counts, old_text not found returns descriptive error listing expected text snippet, empty edits list rejected, no effective changes detected when content unchanged. |
| **`test_grep.py`** | Tests for grep: literal vs regex pattern matching, file_filter glob/suffix application, binary file skipping via null byte detection, path traversal rejection for out-of-cwd targets, max_matches capping behavior. |
| **`test_terminal_io.py`** | Tests for terminal I/O helpers: ANSI-safe string length measurement (accounts for escape codes), box printing with proper wrapping and border characters, markdown rendering output formatting for tables/code blocks/inline elements. |
| **`test_agent.py`** | Tests for agent module: AgentType.from_file() YAML loading, build_system_prompt augmentation, filter_tool_schemas tool filtering logic. |
| **`test_commands.py`** | Tests for slash command handlers: /exit and /quit breaking the loop, /sub spawning sub-agents correctly. |
| **`test_dispatcher.py`** | Tests for tools.dispatcher.dispatch(): correct function lookup by name, keyword argument passing, KeyError raised for unknown tool names. |
| **`test_harness.py`** | Tests for harness.py entry point: build_system_prompt() augmentation (base prompt content, cwd listing, AGENTS.md injection), user_loop behavior (slash commands /exit and /quit break loop, display functions called for response/tool_call/tool_result/error kinds). Validates end-to-end flow with mocked agent and client. |

## Conventions to follow

1. **Prefer existing box-print helpers** (`print_box`, role-specific wrappers) for terminal output — they handle ANSI-aware wrapping, color coding, and truncation. Don't raw print long text.
2. **Keep tool calls in the `tools/` package** — new capabilities go there as both a schema entry (so Ollama knows about them) *and* an implementation function. Auto-discovery means no manual registration needed.
3. **Tests mirror source layout.** Add test files alongside any new logic, and run with `pytest tests/`.
4. **Don't modify `system_prompt.txt` lightly** — the harness augments it automatically each session (cwd listing + AGENTS.md). Overcrowding it bloats every request; put project conventions in this file instead.
