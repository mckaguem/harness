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

## Step 3 — Standard Python project layout (+ `uv` CLI) ⏳
**Goal:** Rearrange the directory structure to conform to standard Python
project conventions so the program can be installed/run as a CLI tool with
`uv`. Update code, imports, tests, and packaging accordingly.

**Status:** Pending — to be executed by a `main` sub-agent.

---

## Step 4 — OpenAI `responses` interface & drop Ollama ⏳
**Goal:** Adapt `OpenAIProvider` to use the OpenAI **Responses** API instead of
the legacy Completions/Chat Completions interface. Remove Ollama support
(low priority).

**Status:** Pending — to be executed by a `main` sub-agent.

---

## Step 5 — Parallel sub-agents (async) ⏳
**Goal:** Make provider calls async and make `run_subagent` non-blocking so
the parent agent and sub-agents run concurrently; when a sub-agent returns,
insert its response into the calling agent's next round of messages.

**Status:** Pending — to be executed by a `main` sub-agent.

---

## Cross-cutting notes
- Each step's sub-agent is instructed to run `harness.py` in **non-interactive
  mode** (from Step 1) as part of its testing where applicable.
- Each step commits its own changes and summarizes them inline below.
