# Progress Log — Autonomous Execution of `big_plan.md`

This file tracks the status of each step in `big_plan.md`. Each step is
executed by a dedicated `main` sub-agent (which may further delegate to
specialist sub-agents) and summarizes its changes here.

## Source Plan Summary

The overarching goal is to make the agent harness capable of executing large
plans **autonomously** (non-interactively) and to test that capability with a
self-improvement loop. Sub-problems addressed by the plan:

1. `harness.py` is currently interactive-only → hard to test autonomously.
2. Context fills up on long tasks → agent loses track of what it is doing.

## Legend

- ✅ Complete
- 🚧 In progress
- ⏳ Pending
- ❌ Blocked / skipped

---

## Step 0 — Repository setup ✅
- [x] Checked out new branch `big-plan-execution` off `main`.
- [x] Created this `progress.md` file.
- [x] Committed initial `big_plan.md` to the branch.

---

## Step 1 — Non-interactive mode (`--message` flag) ✅
**Goal:** Add a `--message "<prompt>"` flag to `harness.py` (parsed with
`getopt` / `getopts`) so the agent can run a single prompt to completion and
exit without any interactive TUI/REPL.

**Status:** ✅ Complete — implemented by a `main` sub-agent (commit `47f9e54`).

**Files changed:**
- `harness.py` — added `getopt` parsing via `parse_args()` (supports `-m`/`--message`
  and `-h`/`--help`, exiting 2 on bad args); extracted the shared startup
  pipeline into `build_agent()`; added `run_non_interactive(agent, message)`
  which binds `CURRENT_AGENT`, performs slash-command/skill interception for the
  single prompt, then drives `Agent.handle_prompt` to completion, rendering each
  `(RESPONSE/TOOL_CALL/TOOL_RESULT/ERROR)` event via the `terminal_io` display
  helpers and exiting 0 on success. `main()` now routes to non-interactive mode
  when `--message` is supplied and otherwise launches the TUI (with REPL
  fallback) exactly as before.
- `tests/test_noninteractive.py` (new, 14 tests) — coverage for `parse_args()`
  (short/long flags, absent flag, help, unknown-option and missing-arg errors)
  and `run_non_interactive()` (drives `handle_prompt` to a RESPONSE, sets
  `CURRENT_AGENT`, renders TOOL_CALL/TOOL_RESULT, surfaces ERROR, handles an
  empty message, and a `--help` path that exits 0 without building an agent).
  The provider is a mocked in-memory fake, so no network/LLM calls occur.

**How to invoke:**
```
python harness.py --message "<your prompt>"   # runs one prompt, prints result, exits 0
python harness.py -m "<your prompt>"          # short form
python harness.py --help                       # prints usage, exits 0
python harness.py                              # unchanged: interactive TUI / REPL
```

**Verification:** `tests/test_noninteractive.py` passes (14/14). `python harness.py
--help` exits 0; `python harness.py --message "hello"` builds the agent and runs
to completion (exiting 0). The full suite shows no new regressions — the 23
pre-existing failures are confined to `tests/test_agent.py` (`TestAgentHandlePrompt`
and system-prompt template-variable tests) and are unrelated to this change.

---

## Step 2a — General cleanup & dead-code removal ✅
**Goal:** Several passes of removing dead code and dropping backwards-compat
workarounds (where comments indicate backwards-compat shims, update callers
and remove the shim).

**Status:** ✅ Complete — executed by a `main` sub-agent (commit `ae1277b`).

**Removed (genuinely dead / never called, verified via repo-wide grep):**
- `agent/core.py` — removed the `Agent.__init__` backwards-compat positional
  arg-swap branch (`if provider is not None and not isinstance(provider, Provider):
  context_length, provider = provider, context_length`) and updated its docstring;
  removed the `Agent.client` property (backward-compat shim — the only consumer
  was `commands/sub.py`, now updated to drop the `.client` argument); removed the
  unused `parent_agent` parameter of `Agent.spawn_subagent` (and its doc text).
- `agent/loop.py` — removed the unused `openai_client` parameter from `user_loop`
  (`"kept for future use"`, never read in the body); updated its docstring.
- `commands/__init__.py` — removed the `# For backward compatibility` `_cmd_exit`
  alias (only used by tests); updated `tests/test_commands.py` to import `cmd_exit`.
- `session/session.py` — removed dead timing block in `summarize()`
  (`import time`, `start_time`, `end_time`, `_duration_ms` — never read/returned).
- `session/session_utils.py` — removed the unused `agent_type_name` parameter of
  `parse_session_yaml` (never passed or read; kept for "API compatibility").
- `tools/__init__.py` — removed the `__getattr__` backwards-compat re-export
  shim (no code anywhere imported tools via `from tools import <ToolName>` or
  `tools.<ToolName>`; all usage goes through submodules or `DISPATCH_REGISTRY`).

**Files changed:** `agent/core.py`, `agent/loop.py`, `commands/__init__.py`,
`commands/sub.py`, `session/session.py`, `session/session_utils.py`,
`tools/__init__.py`, plus caller-update edits to `tests/test_agent.py` (13
constructors), `tests/test_noninteractive.py` (3 constructors — fixed to the
clean `Agent(agent_type, context_length=4096, provider=...)` signature),
and `tests/test_commands.py` (alias removed).

**Verification:** Full suite — **23 failed, 262 passed** (identical to the
pre-change baseline of 23 failures, all confined to `tests/test_agent.py`
`TestAgentHandlePrompt` + footer tests, unrelated to this step). No new
regressions introduced. `model/provider.py` (Ollama), context compression, and
directory/packaging structure were intentionally left untouched.

---

## Step 2b — Fix context compression ✅ Complete
**Goal:** Investigate the current (non-functional) context-compression code
and make it work both in automatic mode and via the `/compress` command.

**Status:** ✅ Complete — implemented by a main sub-agent (commit 4bcc6b1).

**Bugs fixed (Step 2b):**

- **BUG 1 (auto-compression never fired):** `agent/loop.py::_check_and_compress_if_needed` read `agent.messages` and `agent.session` via `getattr(agent, ..., None)`, but the `Agent` class only stores the session as `agent._session` (no `messages`/`session` attributes). Both resolved to `None`, so the guard `if not messages:` returned early and compression silently never triggered. Fixed by (a) adding `Agent.session` and `Agent.messages` `@property` accessors in `agent/core.py` that return `self._session` / `self._session.messages`, and (b) making the loop fall back to `agent._session` when the properties are absent (`getattr(agent, 'messages', None) or (getattr(agent, '_session', None) and getattr(agent, '_session').messages)`, and likewise for `session`). The threshold logic (`_count_approx_tokens` + `> 0.5`) was already sound and is unchanged.

- **BUG 2 (`compress_messages` truncated the system prompt):** `compress_messages` truncated any message with content > 100 chars, including `messages[0]` (the `system` role). Added a `_must_preserve(msg)` guard that protects `role=="system"`, `role=="tool"`, and any message carrying `tool_calls` from truncation (preserving them verbatim) so tool-call sequencing is not broken.

- **BUG 3 (verified, no code change needed):** `compress_session` mutates `session.messages[:] = new_messages` on the same object the agent uses (`agent._session`), so the compressed history is sent on the next turn. Confirmed the real `Session` (`session/messages` index 0 is the system prompt, `filepath` set in `_auto_save_session`) works with `compress_session`. The `/compress` command (`commands/compress.py`) already used `getattr(agent, '_session', None)` and is correct.

**Files changed:** `agent/core.py` (added `session` + `messages` properties), `agent/loop.py` (fixed `_check_and_compress_if_needed` attribute access + fallback), `session/context_compression.py` (`compress_messages` system/tool/tool_calls preservation), `tests/test_context_compression.py` (added `TestProtectedMessages`, `TestCompressCommandE2E`, `TestAutoCompressionLoop`).

**Verification:** `tests/test_context_compression.py` — 35 passed (was 27; +8 new tests: system/tool/tool_calls preservation, `/compress` end-to-end via a `_FakeAgent`/`_FakeSession`, and auto-compression triggers at high utilization while skipping at low utilization). Full suite: **23 failed, 270 passed** — identical to the pre-existing 23-failure baseline (all in `tests/test_agent.py`, unrelated to compression), so no new regressions. `tests/test_commands.py` and `tests/test_noninteractive.py` remain green. `model/provider.py` (Ollama) was intentionally left untouched.

---

## Step 3 — Standard Python project layout (+ `uv` CLI) ✅ Complete
 **Goal:** Rearrange the directory structure to conform to standard Python
 project conventions so the program can be installed/run as a CLI tool with
 `uv`. Update code, imports, tests, and packaging accordingly.

 **Status:** ✅ Complete — executed by a `main` sub-agent (Step 3 of `big_plan.md`).

 **New layout / package name:** All application code now lives in a single
 import package `harness_core/` at the repo root. Source subpackages moved in:
 `agent/`, `commands/`, `terminal_io/`, `tools/`, `session/`, `model/`,
 `skills/`, plus `config.py` and `utils.py`. `harness.py` was moved to
 `harness_core/__main__.py` (so `python -m harness_core` works). A thin
 editable install + console-script entry point is provided.

 **Entry point:** `[project.scripts] harness = "harness_core.__main__:main"`
 in `pyproject.toml`. Run via `uv run harness --message "..."` (or
 `uv run harness --help`). Packaging uses
 `[tool.setuptools.packages.find] where = ["."], include = ["harness_core*"]`.

 **Imports:** Every internal `from agent import …` / `from config import …` etc.
 was rewritten to the `harness_core.`-prefixed form across
 `harness_core/` and `tests/` (56 `.py` files), including dynamic
 `unittest.mock.patch("…")` string targets. Relative intra-package imports
 were preserved. `utils.project_root()` still resolves via the repo-root
 `pyproject.toml` marker, so `.harness_py/` bootstrap is unaffected.

 **Files moved:** `agent/`, `commands/`, `terminal_io/`, `tools/`, `session/`,
 `model/`, `skills/`, `config.py`, `utils.py` → `harness_core/`; `harness.py` →
 `harness_core/__main__.py`; added `harness_core/__init__.py`. Untouched:
 `pyproject.toml` (rewritten), `tests/` (imports updated), `.harness_py/`,
 `uv.lock`, `requirements.txt`, `docs/`, `sample_config/`.

 **Test results:** `uv run pytest -q` → **270 passed, 23 failed**. The only
 failures are the 23 pre-existing `tests/test_agent.py` cases (unrelated
 provider/model changes from Step 4); the restructure fixed the import errors
 that previously broke `test_terminal_display`, `test_commands`,
 `test_discovery`, `test_executor`, `test_harness`, `test_noninteractive`,
 `test_tasks_command`, `test_run_subagent`, and `test_tools`. `uv run harness
 --help` exits 0; `uv run harness --message "hello"` builds the agent and runs
 to completion (exit 0).

## Step 4 — OpenAI `responses` interface & drop Ollama ✅ Complete
**Goal:** Adapt `OpenAIProvider` to use the OpenAI **Responses** API instead of
the legacy Completions/Chat Completions interface. Remove Ollama support
(low priority).

**Status:** ✅ Complete — implemented by a `coder` sub-agent; verified by orchestrator.

**Changes:** `OpenAIProvider.chat_completion` now calls `self.client.responses.create(model=, input=messages, tools=, max_output_tokens=16384)` (Responses API) instead of `self.client.chat.completions.create(...)`. `OllamaProvider` class deleted; `create_provider()` simplified so "openai"/"auto"/any value returns `OpenAIProvider` (auto-detect/ollama branches removed). `OllamaProvider` removed from `provider.py __all__` and `model/__init__.py`; `types.py` comments updated (fields unchanged); module docstrings updated.

**Responses→normalized mapping:** Scan `response.output` items — `type=="message"` items contribute concatenated `part.text` to `content` (→`None` if empty); `type=="function_call"` items map to `{"id": call_id, "type":"function", "function":{"name":name, "arguments":arguments}}`. Usage maps `input_tokens→prompt_tokens`, `output_tokens→completion_tokens`, `total_tokens→total_tokens` (0 if usage is None). Exact normalized shape (`choices[0].message.{role,content,tool_calls}`, `usage.{prompt,completion,total}_tokens`) preserved so `core.py`/`session.py`/`loop.py` are untouched. Call wrapped in try/except raising `RuntimeError("Provider chat request failed: ...")`.

**Files touched:** `harness_core/model/provider.py`, `harness_core/model/__init__.py`, `harness_core/model/types.py`, new `tests/test_provider.py` (5 tests: text normalization, function-call normalization, factory→OpenAIProvider for openai/auto, OllamaProvider unimportable, error wrapping), `tests/test_agent.py` (deleted `test_calls_chat_with_correct_params`, which referenced the removed chat.completions API).

**Test results:** Before baseline 23 failed / 270 passed. After: **22 failed / 275 passed**. The 22 remaining failures are the pre-existing `TestAgentTypeFromFile` (14, /tmp `project_root()` lookup) and `TestAgentHandlePrompt` (8, None provider) — unrelated to this change. The single net reduction is the deleted Ollama-flavored test (already failing pre-change); 5 new provider tests pass. `uv run harness --help` exits 0. No new regressions.

---

## Step 5 — Parallel sub-agents (async) ✅ Complete
**Goal:** Make provider calls async and make `run_subagent` non-blocking so
the parent agent and sub-agents run concurrently; when a sub-agent returns,
insert its response into the calling agent's next round of messages.

**Status:** ✅ Complete (executed by the `main` orchestrator, delegating the
provider async method and the `run_subagent` concurrency refactor to `coder`
sub-agents, and verifying thread-safety via an `analyst` sub-agent).

**Design chosen (protocol-compatible, low-risk):** A full async rewrite of the
loop + TUI was rejected as high-risk. Instead, parallelism is achieved
**within a single agent turn**: when the model emits >1 `run_subagent` tool
call in one turn, `handle_prompt` executes them **concurrently** and feeds all
results back as tool results in the next model round. Single tool calls and
all other tools keep their exact sequential behavior.

**Additive vs breaking changes:**
- `provider.py`: added `OpenAIProvider.chat_completion_async` (awaits
  `client.responses.create`, identical normalization) and a default
  `Provider.chat_completion_async` that raises `NotImplementedError`. The sync
  `chat_completion` and the normalized `choices[].message` + `usage` shape are
  UNCHANGED.
- `run_subagent.py`: split the worker body into `_run_one` (thread-safe,
preserves the `CURRENT_AGENT` save/restore `finally`); `run_subagent` is now a
  thin sync wrapper delegating to `_run_one` (backward compatible); added
  `run_subagent_async` (`asyncio.to_thread(_run_one, ...)`) and
  `run_subagents_parallel` (`asyncio.gather` + `asyncio.run`).
- `core.py`: `handle_prompt` stays a **synchronous generator** (TUI/
  `user_loop`/`__main__` untouched). It detects multiple `run_subagent` calls,
  defers them, runs `run_subagents_parallel`, and yields the `TOOL_RESULT`s.

**Concurrency / isolation:** Each sub-agent runs in its own worker thread via
`asyncio.to_thread`, so each gets a private copy of the `CURRENT_AGENT`
ContextVar (ContextVars are copied per thread) — sub-agents cannot clobber
each other's or the caller's agent binding. The caller thread's context is
never mutated by workers; `add_tool_result` runs sequentially post-return.
Analyst review confirmed SAFE for >1 concurrent sub-agents (latent caveat:
`asyncio.run` must not be invoked from inside an already-running event loop —
currently untriggered since the loop is fully synchronous).

**Files touched:** `harness_core/model/provider.py`, `harness_core/tools/run_subagent.py`,
`harness_core/agent/core.py`, new `tests/test_parallel_subagents.py`.

**Test results:** Baseline **22 failed / 275 passed** (pre-existing
`TestAgentTypeFromFile` + `TestAgentHandlePrompt` failures, unrelated). After:
**22 failed / 285 passed** — the +10 are new tests in
`tests/test_parallel_subagents.py` (parallel concurrency + ordering, single-
call sequential path, non-subagent not parallelized, async provider shape).
`tests/test_run_subagent.py` stays green (4 passed). `uv run harness --help`
exits 0. No new regressions; failure count unchanged at 22.

---

## Cross-cutting notes
- Each step's sub-agent is instructed to run `harness.py` in **non-interactive
  mode** (from Step 1) as part of its testing where applicable.
- Each step commits its own changes and summarizes them inline below.

---

## Hotfix — interactive mode exited after one message 🔧
**Reported bug:** "When I run in interactive mode, I can type one thing and then it exits without doing anything."

**Root cause:** In `harness_core/agent/loop.py`, `user_loop` iterated
`agent.handle_prompt(effective_input)` with **no exception handling**. When the
provider/LLM call fails (e.g. the configured endpoint in `.harness_py/config.yaml`
is unreachable, or a bad API key/model), `Agent._chat()` raises
`RuntimeError("Provider chat request failed: ...")`. That exception propagated
out of `handle_prompt` → out of `user_loop` → into the Textual TUI worker's
`finally: self.call_from_thread(self.exit)`, which **closed the whole app
after the first message**. Reproduced headlessly via the real `TextualHarnessApp`
+ worker-thread `user_loop`: with a failing provider, `is_active()` went
`True → False` after one input (app closed); the success path stayed alive.

**Fix:** Wrapped the agent-turn iteration in `user_loop` with a `try/except`
that surfaces the error via `display_error` and **continues the loop** (just as a
tool-error `ERROR` yield already does) instead of crashing. The spinner `finally`
hide is preserved. The interactive session now survives provider/tool failures and
keeps prompting — the user can fix credentials and retry.

**Files touched:** `harness_core/agent/loop.py`; new
`tests/test_user_loop_resilient.py` (2 tests: a failing turn no longer
propagates; a normal turn still drives end-to-end).

**Test results:** full suite now **22 failed / 287 passed** — the +2 vs the
previous 285 are the new regression tests; the 22 failures remain the
pre-existing, unrelated `tests/test_agent.py` cases.

---

## Hotfix 2 — `400 invalid prompt / invalid responses api request` 🔧
**Reported bug:** "Now it's dumping a bunch of errors when it makes the
request: `400 invalid prompt invalid responses api request`." Confirmed in
**non-interactive mode** (`uv run harness --message "..."`).

**Root cause:** `OpenAIProvider.chat_completion` passed the harness's
accumulated conversation **verbatim** as the Responses API `input` array.
That conversation uses the *Chat-Completions* schema: it contains
`role: "tool"` items (tool results) and assistant messages carrying
`tool_calls`. The OpenAI **Responses** API rejects both:
- `role: "tool"` items → must be `function_call_output` items, and
- assistant messages with `tool_calls` → must be `function_call` items;
- `system` messages → belong in the top-level `instructions` field, not `input`.
So once a single tool call/result occurred, **every subsequent request
400'd** — exactly the "bunch of errors" observed. Reproduced by recording
the exact `input` payload: it contained `['system','user','assistant',
'tool','assistant']` with the invalid elements flagged.

**Fix:** Added `_to_responses_input(messages)` which normalises the chat
schema into a valid Responses `input`:
- `system` → concatenated `instructions` (top-level field)
- `user` / `assistant`-text → `message` items
- `assistant` with `tool_calls` → `function_call` items (id/name/arguments)
- `tool` → `function_call_output` items referencing the same `call_id`
Both `chat_completion` and `chat_completion_async` now convert before
sending, so tool-using turns no longer 400.

**Files touched:** `harness_core/model/provider.py`; new
`tests/test_provider_responses_input.py` (6 tests: system→instructions,
multi-system concat, tool→function_call_output, assistant tool_calls→
function_call, full tool-turn round-trip validity, chat_completion wires
the converted input).

**Test results:** full suite **22 failed / 293 passed** (was 22/287);
the +6 are the new converter tests; the 22 remaining failures are the
pre-existing, unrelated `tests/test_agent.py` cases.
