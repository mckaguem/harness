# Project: Harness — Local Ollama Agent CLI

## 1. Project Overview & Mission

- **Core Objective:** A terminal-based, self-contained agent runtime that connects to a local LLM (via Ollama) and equips it with sandboxed tools — bash execution, file I/O, recursive grep, and sub-agent delegation — for autonomous coding, analysis, and sysadmin work with zero cloud dependencies.
- **Operating Boundary:** Everything runs inside the current working directory. Path traversal outside CWD is blocked by design.

## 2. Technical Stack & Architecture (brief)

| Layer | Technology |
|-------|-----------|
| **Language & Runtime** | Python 3.10+ (uses `str | None` hints, walrus operators) |
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
- **Edits:** Use targeted `edit_file` (supports multiple ordered replacements atomically) over full rewrites.
- **Breaking changes:** Alert the user if a change breaks type definitions, tool schemas, or architectural boundaries. Never remove a `tools/` file that has tests, and never modify an agent YAML's tool list without confirming intent.
- **Adding tools:** drop a `.py` in `harness_core/tools/` with a module-level `function_def` + matching callable — auto-discovered. Add a mirror test.
- **Adding agents:** add YAML under `.harness_py/agents/` (required: `name`, `model_name`); missing `model_name` fails at load time.
- **Display:** Always render terminal output through `terminal_io` helpers (`print_box`, role-specific display functions, `display_agent_response()` for Markdown). Never raw-print long text.

## 6. Non-Obvious Security Rules

- **Fail closed on security / never leak paths.** Catch specific exceptions (FileNotFoundError, PermissionError, TimeoutExpired) and wrap with descriptive but non-path-disclosing context.
- Treat `docs/original_source.py` as archive-only; it is the pre-refactor monolith and must not be edited.
