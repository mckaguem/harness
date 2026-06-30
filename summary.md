# Harness Project — Structure & Architecture Summary

## What this project is

Harness is a **terminal-based chat harness** that connects to a local large language model (via the [Ollama](https://ollama.ai/) runtime) and equips it with tools for executing shell commands, reading/writing/editing files, recursive `grep` search, and spawning specialized sub-agents. It's meant to be a self-contained, extensible agent runtime you can run against any local model.

---

## Top-level layout

```
harness/
├── harness.py              # Entry point
├── model_utils.py          # Ollama client & tokenization helpers
├── system_prompt.txt       # Base system prompt (augmented at runtime)
├── requirements.txt        # Python deps: ollama, pyyaml
├── original_source.py      # Archived monolith (reference only)
├── AGENTS.md               # Project conventions — injected into every session
│
├── agent/                  # Agent runtime package
│   ├── __init__.py         # Re-exports public API
│   ├── core.py             # Agent class — conversation loop & tool dispatch
│   ├── types.py            # AgentType dataclass + YAML loading
│   ├── utils.py            # filter_tool_schemas, build_system_prompt
│   └── loop.py             # Interactive user_loop chat loop
│
├── agents/                 # Agent definitions (YAML configs)
│   ├── main.yaml           # Primary agent — all tools
│   ├── analyst.yaml        # Analyst sub-agent — read_file, grep
│   ├── coder.yaml          # Coder sub-agent — execute_bash, write/read/edit_file
│   ├── writer.yaml         # Writer sub-agent — write_file, read_file
│   └── prompts/            # Per-agent base system prompt files (.txt)
│       ├── analyst.txt
│       ├── coder.txt
│       └── writer.txt
│
├── commands/               # Slash-command handlers
│   ├── __init__.py         # Registry of /exit, /quit, /sub → handler functions
│   └── sub.py              # Interactive sub-agent session implementation
│
├── tools/                  # Tool implementations ("skills")
│   ├── __init__.py         # Auto-discovers skills, builds registries
│   ├── dispatcher.py       # Runtime tool invocation router
│   ├── utils.py            # Path safety guard (is_safe_path)
│   ├── execute_bash.py     # Shell command execution
│   ├── write_file.py       # Write files with cwd-safety check
│   ├── read_file.py        # Read files with cwd-safety check
│   ├── edit_file.py        # Ordered search-and-replace engine
│   ├── grep.py             # Recursive pattern search (regex, glob filter)
│   └── run_subagent.py     # Programmatic sub-agent invocation
│
├── terminal_io/            # Terminal I/O layer
│   ├── __init__.py         # Re-exports all public API
│   ├── colors.py           # ANSI color constants + c() helper
│   ├── boxes.py            # Box-drawing UI component (print_box)
│   ├── display.py          # High-level display helpers (system/user/agent/tool boxes)
│   ├── prompt.py           # User input with readline history & tab-completion
│   ├── trunc.py            # Text truncation for display control
│   ├── speed.py            # Token-per-second formatting
│   └── markdown/           # Markdown rendering subpackage
│       ├── __init__.py     # Re-exports renderers
│       ├── helpers.py      # Orchestrates markdown-to-terminal pipeline
│       ├── blocks.py       # Table & code-block rendering (Unicode boxes)
│       └── inline.py       # Bold, italic, inline-code transformers
│
└── tests/                  # Test suite (mirrors source layout)
    ├── test_tools.py       # execute_bash, write_file, read_file
    ├── test_edit_file.py   # edit_file chained edits & error paths
    ├── test_grep.py        # grep literal vs regex, filters, binary skip
    ├── test_terminal_io.py # ANSI length, box wrapping, markdown rendering
    ├── test_agent.py       # AgentType.from_file(), filter_tool_schemas
    ├── test_commands.py    # /exit, /quit loop breaking
    ├── test_dispatcher.py  # dispatch lookup & KeyError handling
    └── test_harness.py     # End-to-end: build_system_prompt + user_loop flow
```

---

## How it works — the high-level flow

1. **`harness.py::main()`** boots everything up: it creates an Ollama client, builds a system prompt (base text + cwd listing + AGENTS.md), constructs an `AgentType` for the "main" agent, and passes it to an `Agent` instance along with all tool schemas.
2. **`user_loop(agent)`** enters a forever loop: it prompts the user via readline-enabled input, checks for slash commands (`/exit`, `/quit`, `/sub`), otherwise forwards the text to `agent.handle_prompt()`.
3. **`Agent.handle_prompt()`** is a generator that drives the conversation loop — calling Ollama's chat API, checking if the response contains tool calls, dispatching them through `tools.dispatcher.dispatch()`, appending results back into the message history, and yielding tuples of `(kind, ...)` until the model finally returns plain text.
4. **The terminal I/O layer** listens to those yielded kinds (`RESPONSE`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`) and renders them in styled colored boxes with markdown rendering for agent responses.

---

## File-by-file walkthrough

### Entry point & configuration

#### `harness.py` — The entry point
The single file you run: `python harness.py`. It resolves the Ollama host from environment variables (`OLLAMA_HOST`, then `OPENAI_BASE_URL`, defaulting to `http://localhost:11435`), strips trailing `/v1` if present, creates an `ollama.Client`, builds the augmented system prompt via `build_system_prompt()`, constructs a hardcoded `AgentType("main")` with all tools (`["*"]`), instantiates an `Agent`, and hands it to `user_loop()`. The model is currently hardcoded as `hf.co/deepreinforce-ai/Ornith-1.0-35B-GGUF:Q6_K` with a 2¹⁷ (131,072) token context window — change these to use different models.

#### `model_utils.py` — Ollama connection utilities
Provides helpers for resolving the client's base URL, tokenizing prompts via `/api/tokenize` (for accurate token counting rather than naive character-based estimates), and fetching the model's actual context length from `ollama show` (with deep nested-key search and an 8K fallback). Used internally by agent construction paths.

#### `system_prompt.txt` — The base system prompt
The raw text that forms the foundation of every conversation. It defines the agent's role, operating rules, and constraints. **Don't modify it lightly** — Harness augments it automatically each session by appending a listing of the current working directory plus the full contents of `AGENTS.md`. Project-specific conventions belong in `AGENTS.md`, not here, to avoid bloating every request.

#### `requirements.txt` — Dependencies
Only two: `ollama` (the Python client library) and `pyyaml` (for loading agent YAML configs).

#### `original_source.py` — Archived monolith
The original single-file implementation the project was refactored from. Kept as a reference artifact; do not modify.

---

### `agent/` — The agent runtime package

#### `agent/__init__.py` — Public API surface
Re-exports all public symbols: `Agent`, `AgentType`, status constants (`RESPONSE`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`), and utilities (`filter_tool_schemas`, `build_system_prompt`, `user_loop`). Callers import from here, not from submodules directly.

#### `agent/core.py` — The Agent class (the heart of the system)
~240 lines that own the conversation state. Key responsibilities:

- **`__init__`**: Stores agent type, Ollama client, context length, filters tool schemas via `filter_tool_schemas`, initializes a `messages` list seeded with the system prompt, and binds itself as `CURRENT_AGENT` (a `ContextVar`) so tools can spawn sub-agents without an explicit parent reference.
- **`inject_text()`**: Queues cross-agent text to be prepended to the next user input with delimiter markers (`<<INJECTED>>`...`<<END_INJECTED>>`). Used by `/sub` to inject a sub-agent's summary back into the parent's conversation.
- **`_chat()`** / chat call: Sends `messages` to Ollama with model name, filtered tool schemas (if any), and `num_ctx` option set to context length. Returns response content string.
- **`handle_prompt(user_input)`**: The main generator. Prepends injected text if queued, appends the user message, then loops: calls Ollama → checks for `tool_calls` in response → if none, yields `(RESPONSE, content, response)` and breaks → if tool calls present, yields `(TOOL_CALL, func_name, args_str)`, dispatches via `tools.dispatcher.dispatch()`, catches errors as `(ERROR, description)`, appends tool result to messages, yields `(TOOL_RESULT, func_name, result)`, then loops back. Never calls display functions itself — that's the loop's job.
- **`spawn_subagent()`** (classmethod): Factory that loads a sub-agent YAML from `agents/<name>.yaml`, inherits parent's Ollama host and context length, filters its tool schemas, and returns a fresh `Agent`. Falls back to `CURRENT_AGENT` if no parent is given.
- **`summarize()`**: Builds a temporary message list from conversation history (filtering out system messages), asks the LLM for a bulleted summary, and returns it without modifying `self.messages`. Used as the exit callback for `/sub` sessions.

#### `agent/types.py` — AgentType definition
~90-line dataclass with fields: `name`, `model_name`, `system_prompt_path`, `system_prompt`, `agent_tools`. The static method `_build_system_prompt()` loads a base file and augments it (cwd listing + AGENTS.md). The classmethod `from_file(path)` is the YAML loader — reads config, validates `model_name` is present, builds the augmented system prompt from the referenced base file, falls back to inline `system_prompt` if provided. Raises `FileNotFoundError` or `ValueError` for missing/malformed configs.

#### `agent/utils.py` — Shared utilities
Two functions:

- **`filter_tool_schemas(agent_type, all_schemas)`**: If `agent_tools == ["*"]`, returns everything. Otherwise builds a name→schema lookup and keeps only matching ones. Raises `ValueError` if requested tool names don't exist in available schemas.
- **`build_system_prompt(base_prompt_path)`**: Reads the base file, appends sorted cwd directory listing, and conditionally appends full AGENTS.md contents (if present). Centralizes this augmentation logic so both `harness.py` and YAML-loaded agents get identical prompt enrichment.

#### `agent/loop.py` — Interactive chat loop
The `user_loop(agent, ollama_client, on_exit)` function: prints a startup banner with agent name + model, then runs forever. Each iteration reads user input via `prompt_user()`, checks if it starts with `/` and dispatches to the matching handler from `COMMANDS`. If no handler matches or after sub-agent returns, calls `agent.handle_prompt(user_input)` and renders each yielded tuple based on its kind (`response` → `display_agent_response`, `tool_call` → `display_tool_call`, `tool_result` → `display_tool_result`, else → `display_error`). Supports an optional `on_exit` callback invoked before breaking (used by `/sub` to run summarization).

---

### `agents/` — Agent definitions & prompts

#### YAML configs (`main.yaml`, `analyst.yaml`, `coder.yaml`, `writer.yaml`)
Declarative agent definitions. Each specifies:
- **`name`**: Display name for the banner
- **`model_name`**: The Ollama model identifier (all currently use Ornith-1.0-35B)
- **`system_prompt_path`**: Base prompt file (usually `system_prompt.txt`, or a dedicated one like `agents/prompts/analyst.txt`)
- **`agent_tools`**: Either `["*"]` for all tools, or an explicit list like `["read_file", "grep"]`

`main.yaml` is the primary agent loaded by `harness.py`. The others are sub-agents launched via `/sub <name>` or `run_subagent()`.

#### `agents/prompts/` — Per-agent base system prompts
Dedicated prompt files for specialized agents (analyst, coder, writer). Each instructs the model on its role and constraints. Loaded by `AgentType.from_file()` and augmented with cwd listing + AGENTS.md just like the main agent's prompt.

---

### `commands/` — Slash command handlers

#### `commands/__init__.py` — Handler registry
Maps slash-command names to handler functions via the `COMMANDS` dict:
- **`cmd_exit`** / **`cmd_quit`**: Print goodbye message, return `True` (signals loop to break)
- **`cmd_sub`**: Lazy-imports and delegates to `commands.sub.cmd_sub`, passing the sub-agent name from the command argument

#### `commands/sub.py` — Interactive sub-agent session (~70 lines)
Implementation of `/sub <name>`: validates that a non-empty name was provided, lazy-imports `Agent` + `user_loop` (to avoid circular imports), calls `Agent.spawn_subagent(sub_name)` to create the child agent, prints a status banner with model info, then runs an interactive `user_loop()` on it. Defines `_on_exit` as the loop's exit callback: calls `agent.summarize()` to get a bulleted summary, formats it nicely, and injects it back into the parent agent via `parent_agent.inject_text()`. The parent then sees this summary as if the user typed it.

---

### `tools/` — Tool implementations ("skills")

#### `tools/__init__.py` — Auto-discovery & registry builder (~60 lines)
The package's central nervous system. At import time, `_discover_skills()` walks `tools/*.py`, dynamically loads each file via `importlib.util.spec_from_file_location()`, and checks for a top-level `function_def` attribute. If present and is a dict, the module becomes a "skill" — its schema goes into `AGENT_TOOLS` (list) and the module itself goes into `DISPATCH_REGISTRY` (dict mapping name→module). Skips `__init__.py` and `utils.py`. `_build()` calls `_discover_skills()` at module load time. `__getattr__` provides backwards-compat re-exports so existing code like `from tools import execute_bash` still works by lazily resolving names through the registry.

#### `tools/dispatcher.py` — Runtime router (~15 lines)
Single function: `dispatch(func_name, args)` looks up the tool name in `DISPATCH_REGISTRY`, gets the module's attribute matching the function name (e.g., `mod.execute_bash`), calls it with keyword arguments via `fn(**args)`, and returns the result string. Raises `KeyError` for unknown tools — callers treat this as an error condition.

#### `tools/utils.py` — Path safety guard (~15 lines)
Shared utility used by every file-modifying tool. `is_safe_path(filename)` resolves both cwd and target paths via `.resolve()` and checks that the target is relative to cwd using `Path.is_relative_to()`. Returns False on any exception (catches permission errors, invalid paths). Prevents directory traversal attacks.

#### `tools/execute_bash.py` (~35 lines) — Shell command execution
Runs arbitrary bash commands via `subprocess.run(shell=True, capture_output=True, text=True, timeout=30)`. Combines stdout+stderr (prefixed "STDERR:" for stderr output). Returns colored error messages using `terminal_io.c()` + `RED` for `TimeoutExpired` or general exceptions. Schema declares name `"execute_bash"` with `{command: string required}` parameter.

#### `tools/write_file.py` (~30 lines) — File writing
Validates path safety via `is_safe_path()`, returns RED error if unsafe, then writes content in `'w'` mode with utf-8 encoding (overwriting). Returns GREEN success or RED error. Schema: `{filename: string required, content: string required}`.

#### `tools/read_file.py` (~35 lines) — File reading
Same safety pattern as write_file. Prints a terminal message showing filename + character count in DIM color before returning content. Handles `FileNotFoundError` gracefully with RED error. Schema: `{filename: string required}`.

#### `tools/edit_file.py` (~100 lines) — Ordered search-and-replace engine
The most complex single tool. Validates edits list is non-empty, checks path safety once upfront, reads existing content, then iterates through edits sequentially (each operates on already-modified content so chained edits compose). Tracks changes with line counts. If any `old_text` isn't found, returns RED error listing the problematic edit and first 3 lines of expected text for debugging. Only writes if content actually differs from original. Schema: `{filename: string required, edits: [{old_text: string, new_text: string}] array required}`.

#### `tools/grep.py` (~180 lines) — Recursive pattern search
The most feature-rich tool. Validates inputs, resolves target within cwd (rejects out-of-cwd paths), compiles regex if `use_regex=True`. Decides between single-file read or recursive `os.walk()` traversal, pruning `__pycache__`, `.git/`, and dot-directories. `_is_binary` check detects null bytes in first 8KB to skip binary files. Applies `file_filter` via glob/suffix matching. Reads line-by-line, caps at `max_matches`. Returns `"file:line — content"` format with GREEN summary showing count + "(limited to N)" if capped. Schema: `{pattern: string required, path: string required, use_regex: boolean optional, file_filter: string optional, max_matches: int optional}`.

#### `tools/run_subagent.py` (~50 lines) — Programmatic sub-agent invocation
The non-interactive counterpart to `/sub`. Calls `Agent.spawn_subagent()` with no explicit parent (falls back to `CURRENT_AGENT` ContextVar), iterates through the sub's `handle_prompt(task)` generator, captures the final `RESPONSE` yield as result text. Returns sentinel string if empty or catches exceptions gracefully. Allows the main agent to delegate work to analyst/coder/writer sub-agents without leaving its own loop. Schema: `{sub_agent: string required, task: string required}`.

---

### `terminal_io/` — Terminal I/O layer

#### `terminal_io/__init__.py` — Public API re-export
Re-exports the full public surface from all submodules in a single import point. Keeps existing imports like `from terminal_io import print_box, prompt_user` working unchanged. Organized into categories: colors & boxes, markdown rendering, speed formatting, user input, display helpers, truncation.

#### `terminal_io/colors.py` — ANSI color constants
Defines RESET, BOLD, DIM, CYAN (user), GREEN (agent/success), BLUE (tool calls), YELLOW (warnings), RED (errors), MAGENTA (system), BG_YELLOW, BG_RED. The `c(text, colour, bold=False)` helper wraps text in ANSI escape sequences. Used throughout tools/ for error/success messaging and by display layer for colored boxes.

#### `terminal_io/boxes.py` — Box-drawing UI component
`print_box(title, content, colour=None, width=0, style=None)` renders a styled box with title bar, ANSI-aware body text wrapping (preserves ANSI escapes across wraps), and Unicode borders. Styles: `"system"` / `"user"` / `"agent"` (solid `-` borders) and `"tool_call"` / `"tool_result"` (`+-` corner characters). `_safe_len()` measures string length ignoring ANSI codes for proper alignment.

#### `terminal_io/display.py` — High-level display coordination
Thin wrappers that coordinate boxes, markdown rendering, and truncation:
- **`print_system(title, message)`** → system-style box (MAGENTA)
- **`display_user_prompt(text)`** → user-style box with char count
- **`display_tool_call(func_name, args_str)`** → tool_call box (BLUE)
- **`display_tool_result(func_name, result)`** → truncated tool_result box (YELLOW)
- **`display_tool_call_with_result(...)`** → combined call+result single box with divider
- **`display_tool_success(func_name, message)`** → one-line green confirmation
- **`display_error(message)`** → red error text

#### `terminal_io/prompt.py` — User input with readline
`prompt_user()` returns user-typed string with arrow key navigation and command history via Python's `readline` module. Provides a polished interactive experience (tab completion, up/down history).

#### `terminal_io/trunc.py` — Text truncation helpers
Caps output to `MAX_DISPLAY_LINES` lines so long tool results don't flood the terminal. Preserves beginning/end of truncated text with "[...]" indicators. Used by display functions before rendering large outputs.

#### `terminal_io/speed.py` — Token-per-second formatting
Extracts timing metrics from Ollama chat responses and formats as "X tokens/sec" string for display in agent response headers.

#### `terminal_io/markdown/__init__.py` — Markdown renderer re-exports
Re-exports: `display_agent_response`, `_render_table`, `_render_code_block`. Public API for markdown content rendering.

#### `terminal_io/markdown/helpers.py` — Rendering pipeline orchestrator
`display_agent_response(content, ollama_response, context_length, speed)` splits agent response into inline/block regions, renders them appropriately (tables as Unicode boxes, code blocks with syntax highlighting labels), formats speed/context metadata headers, and prints the final colored box via `print_box`.

#### `terminal_io/markdown/blocks.py` — Block-level renderers
- **`_render_table(rows)`**: Renders markdown tables using Unicode box-drawing characters (`┌─┬┐│├─┼┤└─┴┘`) with column alignment based on content width.
- **`_render_code_block(content, language)`**: Displays fenced code blocks with optional language label, monospace formatting, and background color differentiation.

#### `terminal_io/markdown/inline.py` — Inline element transformers
Handles: bold (`**text**`) → BOLD ANSI, italic (`*text*`) → DIM ANSI, strong italic (`***text***`) → DIM+BOLD combination, inline code (`` `code` ``) → blue+bold monospace formatting.

---

### `tests/` — Test suite

Tests mirror the source layout and are run via `pytest tests/`:

| File | Coverage |
|------|----------|
| `test_tools.py` | execute_bash execution + timeout; write_file/read_file operations + path safety |
| `test_edit_file.py` | Chained edits, old_text-not-found errors, empty edits rejection, no-op detection |
| `test_grep.py` | Literal vs regex patterns, file_filter glob/suffix, binary skipping, path traversal rejection, max_matches capping |
| `test_terminal_io.py` | ANSI-safe string length, box wrapping with borders, markdown rendering output |
| `test_agent.py` | AgentType.from_file() YAML loading, build_system_prompt augmentation, filter_tool_schemas filtering |
| `test_commands.py` | /exit and /quit loop-breaking behavior |
| `test_dispatcher.py` | Correct function lookup by name, keyword arg passing, KeyError for unknown tools |
| `test_harness.py` | End-to-end: system prompt augmentation (base + cwd + AGENTS.md), user_loop flow with mocked agent/client |

---

## Key architectural patterns

### 1. Skill auto-discovery (zero-registration tool loading)
New tools just need a `.py` file in `tools/` with a top-level `function_def` dict — no manual registration anywhere. The package scans, loads via `importlib`, validates the schema shape, and populates both the JSON-schema list (`AGENT_TOOLS`) and the dispatch registry (`DISPATCH_REGISTRY`) at import time.

### 2. Generator-driven conversation loop
`Agent.handle_prompt()` yields typed tuples `(kind, ...)` rather than printing directly or blocking on display. The `user_loop` consumes these and renders them via terminal_io helpers. This separation lets tests mock individual steps without running a full TUI.

### 3. ContextVar-based agent binding
A module-level `ContextVar("current_agent")` binds the active agent instance so deeply-nested tool code (like `run_subagent.py`) can spawn sub-agents without threading an explicit parent reference through every call.

### 4. Prompt augmentation pipeline
Every session, regardless of which agent is loaded, gets its base system prompt augmented with: (1) a sorted listing of cwd files/directories, and (2) the full contents of `AGENTS.md` if present. This keeps project conventions accessible to the model without bloating every LLM request.

### 5. Path safety enforcement
All file-modifying tools (`write_file`, `read_file`, `edit_file`, `grep`) gate on `is_safe_path()`, which resolves both cwd and target paths and verifies containment. Prevents directory traversal attacks even if the model is tricked into requesting writes outside the working directory.

### 6. Sub-agent delegation
Two pathways for delegating to specialized agents: `/sub <name>` runs an interactive session with its own loop; `run_subagent()` (callable as a tool) launches a one-shot non-interactive session, captures the final response text, and returns it — enabling the main agent to delegate research/writing tasks without leaving its conversation.
