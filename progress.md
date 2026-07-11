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

## Step 2a — General cleanup & dead-code removal ⏳
**Goal:** Several passes of removing dead code and dropping backwards-compat
workarounds (where comments indicate backwards-compat shims, update callers
and remove the shim).

**Status:** Pending — to be executed by a `main` sub-agent.

---

## Step 2b — Fix context compression ⏳
**Goal:** Investigate the current (non-functional) context-compression code
and make it work both in automatic mode and via the `/compress` command.

**Status:** Pending — to be executed by a `main` sub-agent.

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
