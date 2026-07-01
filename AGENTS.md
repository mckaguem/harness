# Project: Harness — Local Ollama Agent CLI

## 1. Project Overview & Mission

- **Core Objective:** Provide a terminal-based, self-contained agent runtime that connects to a local LLM (via Ollama) and equips it with sandboxed tools — bash execution, file I/O, recursive grep, and sub-agent delegation — enabling autonomous coding, analysis, and system administration tasks without cloud dependencies.
- **Target Audience/Use Case:** Developers who want an extensible, offline-capable AI coding assistant that can read/write code, run commands, spawn specialized workers (analyst, coder, writer), and operate entirely within the current working directory for safety.

## 2. Technical Stack & Architecture

| Layer | Technology |
|-------|-----------|
| **Language & Runtime** | Python 3.10+ (uses type hints like `str | None`, walrus operators) |
| **LLM Client** | `ollama` — connects to local Ollama instance (default `http://localhost:11435`, overridable via `OLLAMA_HOST`) |
| **Terminal UI** | `rich` for colored output, Unicode box-drawing, syntax highlighting; `prompt_toolkit` for readline-style input with history and tab completion |
| **Config Parsing** | `pyyaml` — agent definitions are YAML files in `agents/` |
| **Architecture Pattern** | Monolithic modular package — generator-driven conversation loop with clear separation between agent logic (`agent/`) and display logic (`terminal_io/`). Zero-registration auto-discovery for tools and sub-agents. |

### Key Runtime Flow

1. `harness.py::main()` resolves Ollama host, creates client, loads `agents/main.yaml` via `AgentType.from_file()`, filters tool schemas, instantiates `Agent`, launches `user_loop()`.
2. `handle_prompt()` is a generator yielding typed tuples `(RESPONSE | TOOL_CALL | TOOL_RESULT | ERROR, *args)` — one per LLM interaction cycle.
3. Each cycle: append user message → call Ollama chat API (with tools if model supports them) → dispatch tool calls via `tools.dispatcher` → append results → repeat until plain RESPONSE or max-loop ceiling (5).

## 3. Agent Persona & Operational Rules

- **Role:** You are an autonomous, senior full-stack engineer operating within a terminal agent runtime. You have sandboxed access to shell commands and file operations, all bounded by path-safety guards.
- **Tone & Behavioral Guardrails:**
  - Be concise and direct. Do not engage in conversational filler.
  - Prioritize readability and maintainability over clever micro-optimizations unless performance is a stated requirement.
  - **Do not guess:** If a requirement, API contract, or library version is ambiguous, stop and ask the user for clarification.
  - Prefer targeted edits (`edit_file`) over full rewrites — atomicity matters; partial failures should leave files untouched.
- **Runtime Constraints (enforced at code level):**
  - All file reads/writes are gated by `is_safe_path()` — path traversal outside CWD is blocked.
  - Bash commands have a 30-second timeout (`TimeoutExpired` → RED error).
  - Sub-agent spawns create isolated sessions with no shared conversation history.
  - System prompt is auto-augmented each session: base prompt + CWD listing + full AGENTS.md contents.

## 4. Coding Standards & Style Guide

### Patterns to Follow

- **Functional-ish, procedural where it matters.** Tools are standalone functions (not methods). The agent core uses a generator pattern for its loop — separate concerns between logic (`agent/core.py`) and rendering (`terminal_io/`).
- **Type hints on public APIs.** Use `str | None` union syntax. Document function signatures via docstrings only when non-obvious; keep code self-documenting.
- **No manual registration.** Tool skills are auto-discovered: any `.py` file in `tools/` with a top-level `function_def` dict is loaded at import time. New capabilities = one new file, done. Same for sub-agents (YAML + optional prompt).
- **Fail closed on security.** Every path operation calls `is_safe_path()` first. Return `( "_error_", RED_message )` — never raise uncaught exceptions that could leak paths to the LLM.

### Formatting & Linting

- No explicit linter config is present in this repo. Follow standard Python conventions:
  - **Black-style** line length (88 chars) as default; don't exceed ~120 without justification.
  - **f-strings** for all string formatting — no `.format()` or `%` operators unless compatibility demands it.
  - **Single quotes** for strings, double quotes for docstrings.
  - Keep imports top-of-file: stdlib → third-party (`ollama`, `rich`, `pyyaml`, `prompt_toolkit`) → local (`from tools import ...`).

### Error Handling

- Tools return typed tuples: `(type_tag, content)` where `type_tag` is `"text"`, `"json"`, `"diff"`, `"bash"` for Rich syntax rendering, or `"_error_"` to trigger red error display.
- Never silently swallow exceptions in tool code. Catch specific ones (FileNotFoundError, PermissionError, TimeoutExpired) and wrap with descriptive context.
- `edit_file` uses atomic semantics: if any edit's `old_text` isn't found, the file is left completely untouched and a structured error reports the problematic edit plus first 3 lines of expected text for debugging.

### Testing Requirements

- **Framework:** pytest (no fixtures beyond stdlib — tests use `tmp_path`, manual CWD switching via `os.chdir()`, and `unittest.mock.patch` for subprocess/client mocks).
- **Coverage expectations:** Every new tool or agent must have corresponding tests in `tests/`. Mirror the naming convention: `test_<module_name>.py`.
- **Test structure pattern:** Use class-based organization (`class TestEditFileSafety:`) grouping related cases. Assert on both return values and side effects (file content, directory state).
- Run with: `pytest tests/`

## 5. Repository Structure Context

```
harness/
├── harness.py                  # Entry point — wires config, creates Agent, launches user_loop
├── model_utils.py              # Ollama client helpers — URL resolution, tokenize-based count, context-length detection
├── original_source.py          # ARCHIVE ONLY. The monolithic single-file this was refactored from. Do NOT modify.
├── system_prompt.txt           # Base prompt text (auto-augmented with CWD + AGENTS.md each session)
├── requirements.txt            # Runtime deps: ollama, prompt_toolkit, pyyaml, rich
│
├── agent/                      # Agent runtime package
│   ├── core.py                 # Core Agent class — conversation state, handle_prompt() generator loop, spawn_subagent(), summarize()
│   ├── loop.py                 # user_loop() interactive chat driver with slash-command handling
│   ├── types.py                # AgentType dataclass + YAML loading (from_file), prompt augmentation
│   └── utils.py                # filter_tool_schemas(), build_system_prompt() — shared across all agent instances
│
├── agents/                     # Sub-agent definitions (declarative)
│   ├── main.yaml               # Primary orchestrator: all tools, main.txt system prompt
│   ├── analyst.yaml            # Read-only analysis: read_file + grep (+ run_subagent)
│   ├── coder.yaml              # Code implementation: execute_bash + write_file + read_file + edit_file (+ run_subagent)
│   ├── writer.yaml             # Documentation/content: write_file + read_file (+ run_subagent)
│   └── prompts/                # Per-agent .txt system prompt files (main.txt, analyst.txt, coder.txt, writer.txt)
│
├── commands/                   # Slash-command handlers (/exit, /quit, /sub)
│   ├── __init__.py             # COMMANDS dict registry — maps name → handler(rest, agent) -> bool
│   └── sub.py                  # /sub <name> — spawns interactive sub-agent session with summary injection on exit
│
├── tools/                      # Auto-discovered tool skills (see §4 patterns)
│   ├── __init__.py             # Skill auto-loader — scans *.py for top-level function_def, builds AGENT_TOOLS + DISPATCH_REGISTRY
│   ├── dispatcher.py           # Runtime: dispatch(func_name, args) → fn(**args), raises KeyError on unknown tools
│   ├── utils.py                # is_safe_path() — path traversal guard used by ALL file-modifying tools
│   ├── execute_bash.py         # Shell execution with 30s timeout, combined stdout+stderr output
│   ├── write_file.py           # Atomic file write with safety guard
│   ├── read_file.py            # File read with char-count display
│   ├── edit_file.py            # Ordered search-and-replace with atomic rollback on partial failure
│   ├── grep.py                 # Recursive pattern search (literal/regex), binary skipping, max_matches cap
│   └── run_subagent.py         # Programmatic non-interactive sub-agent invocation via handle_prompt() generator
│
├── terminal_io/                # Terminal display layer — keep all print/rendering here
│   ├── __init__.py             # Public API re-export surface
│   ├── colors.py               # ANSI constants + c(text, colour) helper
│   ├── boxes.py                # print_box() with Unicode borders — use this for ALL terminal output
│   ├── display.py              # High-level: display_user_prompt(), display_tool_call(), display_error(), etc.
│   ├── prompt.py               # Readline-enabled user input prompt (arrow keys, history, tab completion)
│   ├── trunc.py                # MAX_DISPLAY_LINES cap with "[...]" indicators for long outputs
│   └── markdown/               # Markdown→terminal renderer (tables as Unicode boxes, code blocks highlighted)
│       ├── helpers.py          # display_agent_response() orchestrator — splits inline/block regions
│       ├── blocks.py           # _render_table(), _render_code_block() with monospace/bg coloring
│       └── inline.py           # Bold/italic/strong-italic → ANSI BOLD/DIM, inline code → blue+bold mono
│
├── tests/                      # pytest suite — mirrors source layout exactly
│   ├── test_tools.py           # execute_bash, write_file, read_file (execution + timeouts + path safety)
│   ├── test_edit_file.py       # Chained edits, atomic rollback, error messages, line counting
│   ├── test_grep.py            # Literal vs regex, file_filter, binary skipping, traversal rejection
│   ├── test_terminal_io.py     # ANSI length measurement, box wrapping, markdown rendering output
│   ├── test_agent.py           # AgentType.from_file(), filter_tool_schemas() logic
│   ├── test_commands.py        # /exit and /quit handler return values
│   ├── test_dispatcher.py      # dispatch() function lookup + KeyError for unknown names
│   └── test_harness.py         # End-to-end: build_system_prompt augmentation, user_loop flow with mocks
└── AGENTS.md                   # ← You are reading this file. Agents get it injected into every session prompt.
```

## 6. Workflow & Git Guardrails

- **File Modifications:** Never rewrite entire files if only modifying a specific function. Use targeted edits (`edit_file` tool or manual precise search-and-replace). The `edit_file.py` engine supports multiple ordered replacements in one call — prefer it over separate write operations.
- **Commit Messages:** Follow Conventional Commits format: `type(scope): description`. Examples:
  - `feat(tools): add run_subagent with isolated session spawning`
  - `fix(agent): prevent infinite loop when model returns empty tool_calls`
  - `refactor(terminal_io): extract markdown rendering into subpackage`
  - `test(edit_file): add atomic rollback test case for partial old_text failures`
  - `docs(AGENTS.md): restructure with operational rules and architecture map`
- **Breaking Changes:** Alert the user immediately if a requested change breaks existing type definitions, tool schemas (OpenAI function-calling format), or architectural boundaries. Specifically: never modify an existing agent's YAML without confirming its current tool list is intentional; never remove a file from `tools/` that has corresponding tests in `tests/`.
- **Adding New Tools:** Create one `.py` file in `tools/`, define `function_def` at module level (OpenAI schema dict) and the callable matching that function name. No registration needed — import triggers auto-discovery. Add a mirror test file in `tests/`.
- **Adding New Agents:** Create YAML in `agents/` with required fields (`name`, `model_name`, `system_prompt_path`). Optionally add `agents/prompts/<name>.txt`. Use `"*"` for all tools or list specific names. The harness does validation at load time — missing `model_name` raises immediately.
- **Display Rules:** Always use `terminal_io` helpers (`print_box`, role-specific display functions) for terminal output. Never raw-print long text — box printers handle ANSI-aware wrapping, color coding, and truncation. Markdown from the LLM is rendered through `display_agent_response()` which handles tables as Unicode boxes and code blocks with syntax highlighting.
- **System Prompt Discipline:** Don't modify `system_prompt.txt` lightly — it gets auto-augmented each session (CWD listing + AGENTS.md). Keep role definitions lean here; put project conventions in this AGENTS.md instead to avoid bloating every LLM request.
