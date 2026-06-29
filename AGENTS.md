# Project: Harness — Local Ollama Agent CLI

## What this is
A terminal-based chat harness that connects to a local LLM (via **Ollama**) and gives it three tools: `execute_bash`, `write_file`, and `read_file`. It's the runtime you're running inside.

## File layout

| File | Role |
|---|---|
| `harness.py` | Entry point — configures Ollama, builds the system prompt, starts the loop. **Edit here for connection/model settings.** |
| `agent_loop.py` | Conversation loop — dispatches tool calls and collects responses. |
| `terminal_io.py` | UI layer — ANSI colours, box printing, user prompt with readline (arrow keys, history). |
| `tools.py` | Tool implementations (`execute_bash`, `write_file`, `read_file`) + schema definitions (`AGENT_TOOLS`). |
| `system_prompt.txt` | Base system prompt text. The harness appends the cwd listing (and any `AGENTS.md` content) on top of this. |
| `tests/test_terminal_io.py` | Tests for the display/UI layer. |
| `tests/test_tools.py` | Tests for tool implementations. |

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

## Conventions to follow
1. **Prefer the existing box-print helpers** (`print_box`, role-specific wrappers) for any output that touches the terminal — they handle ANSI-aware wrapping, colour coding, and truncation. Don't raw `print` long text.
2. **Keep tool calls in `tools.py`** — new capabilities go there as both a schema entry (so Ollama knows about them) *and* an implementation function.
3. **Tests mirror source layout.** Add a test class alongside any new logic, and run with `pytest tests/`.
4. **Don't modify `system_prompt.txt` lightly** — the harness augments it automatically each session (cwd listing + AGENTS.md). Overcrowding it bloats every request.
