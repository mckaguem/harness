# Progress Log — Plan Execution

This file tracks the work done across the phases described in `plan.md`.

## Branch
`feature/plan-execution`

## Legend
- ✅ completed
- 🔄 in progress
- ⬜ pending

## Phases

### Phase 1 — Fix existing tests
- ✅ Goal: Run the full test suite, identify failing tests, determine whether each failure is due to a stale test or a genuine bug, and fix accordingly. Re-run and commit.
- Status: ✅ completed

### Phase 2 — Improve test coverage
- ⬜ Goal: Add end-to-end non-interactive tests exercising all tools, the skill mechanisms, and subagents. Run, fix, commit.
- Status: ✅ completed

### Phase 2b — Parallel subagents
- ⬜ Goal: Make `run_subagent` return immediately with a subagent identifier and run in parallel (async/threads). Add an `await` tool that blocks until a subagent completes. Enforce a maximum concurrency limit with an error when exceeded. Add tests. Run, fix, commit.
- Status: ✅ completed

### Phase 3 — Speculative features
- ⬜ Goal: Use the `researcher` subagent to find 10 beneficial features online, document them, choose the best, and implement it with tests. Run, fix, commit.
- Status: ✅ completed

## Summary of commits / changes
(Will be filled in as work progresses.)

### Change 1 — config.py tolerance fix (Phase 1)
- `harness_core/config.py` previously raised `FileNotFoundError` when the harness
  config file was missing and lacked a default `context_length`. Added a
  `FileNotFoundError` fallback (use built-in defaults) and a default
  `context_length` so agents can be constructed in tests/CI without a full config
  present on disk.

### Change 2 — tests/test_agent.py TestAgentHandlePrompt rewrite (Phase 1)
- The old `TestAgentHandlePrompt` mocked a raw `MagicMock()` OpenAI client
  (`mock_client.chat.completions.create`), which fails the
  `isinstance(provider, Provider)` guard in `harness_core/agent/core.py` (line 38),
  leaving `provider=None` and raising `AttributeError` at `core.py:143`.
- Rewrote the entire class to mock the `Provider` interface via
  `MagicMock(spec=OpenAIProvider)` and return NORMALIZED chat-completion dicts
  (`{"choices":[{"message":{...}}], "usage":{...}}`) shaped like
  `OpenAIProvider._normalize_response`. Helper builders `_make_provider`,
  `_response`, and `_tool_call` now drive `provider.chat_completion(...)` exactly as
  production does. This fixed 22 failing tests in the suite. Production code in
  `harness_core/` was NOT modified.

### Change 3 — tests/test_e2e_coverage.py (Phase 2)
- `tests/test_e2e_coverage.py` (new, untracked) provides end-to-end non-interactive
  coverage for the harness. It drives the agent through the real dispatch path via
  `run_non_interactive` / `Agent.handle_prompt` with an in-memory fake provider so no
  network or live LLM is contacted.
- Covers: every tool exposed by the harness (driven through the real dispatch path),
  the skill mechanisms (discovery, interceptor routing, activate_skill), and subagents
  (`run_subagent` spawning + discovery).
- Network calls are patched offline: `_FakeDDGS` (monkeypatch `ddgs.DDGS`) for
  `web_search`, and `_fake_urlopen` / `_FakeResponse` (monkeypatch
  `harness_core.tools.web_fetch.urlopen`) for `web_fetch`. Production code was NOT
  modified — only the two failing tests were fixed (undefined `_fake_ddgs_class` and
  `fake_urlopen` references replaced with real module-scope fakes), leaving the other
  15 tests intact. Full suite: 393 passed, 0 failures.

### Change 4 — Parallel subagents (Phase 2b)
- Introduced `harness_core/tools/subagent_manager.py` with a `SubagentManager` class (module-level singleton `manager`) that tracks in-flight background sub-agent jobs, enforces a `MAX_CONCURRENT` limit (raises `RuntimeError` when exceeded, surfaced as an error `ToolResult`), and provides `launch(...)` (returns an incrementing `"subagent-<n>"` identifier) and `await_one(identifier)` (blocks until the job completes and returns its `ToolResult`).
- `run_subagent` gained a new `block` parameter (default `True`). When `block=True` it preserves the existing synchronous behaviour (returns the `ToolResult` directly). When `block=False` it delegates to `manager.launch(...)`, runs the sub-agent in the background via a worker thread, and immediately returns a short identifier-bearing `ToolResult`.
- Added `harness_core/tools/await_subagent.py`, a new tool that blocks until a background sub-agent job finishes and returns its result. It is auto-discovered into `DISPATCH_REGISTRY` (alongside `AGENT_TOOLS`), so `'await_subagent' in DISPATCH_REGISTRY` is `True`.
- The `tests/test_tools.py` count was updated to 14 (was 13): it now covers the new `await_subagent` auto-discovery/registration alongside the rest of the tool surface.
- Tests: `tests/test_parallel_subagent_manager.py` (13 tests) covers `SubagentManager` lifecycle, concurrency limit, the `run_subagent(block=...)` paths, and `await_subagent` round-trip. All 13 pass in < 1s after fixing two tests that patched the wrong module path (`harness_core.tools.run_subagent._run_one` → `harness_core.tools.subagent_manager._run_one`).

### Change 5 — Phase 3: persistent project memory (MEMORY.md)
- Phase 3 research enumerated 10 beneficial features for a local coding agent in
  `docs/speculative_features.md` (sources: Claude Code architecture write-ups,
  r/LocalLLaMA threads, agent-worktree/context-mode projects, etc.). The selected
  best feature was a **persistent project memory file** (`MEMORY.md`) — the agentic
  "external memory" pattern: a durable notes file that outlives any single
  conversation and is auto-injected into the system prompt, surviving context
  compression and session reloads.
- `harness_core/memory.py` (new) provides `get_memory_path()`, `read_memory()`
  (returns stripped content or `None`), and `memory_section(memory)` (builds the
  prompt block, returning "" when memory is empty/None so callers can append it
  unconditionally). It reuses `harness_core.utils.project_root` to locate the file.
- `harness_core/tools/update_memory.py` (new) is a self-discovered tool (exposes
  `function_def`) so it is auto-registered into `DISPATCH_REGISTRY`/`AGENT_TOOLS`.
  It supports `mode="replace"` (default) and `mode="append"`, returning a
  `ToolResult` (theme `"error"` for invalid modes). Lets an agent maintain
  `MEMORY.md` while working.
- System-prompt wiring: `AgentType._build_system_prompt` in
  `harness_core/agent/types.py` now imports `read_memory`/`memory_section` and
  appends the memory section at the end of the prompt (after the cwd footer), so
  every agent sees the project's persistent memory. Previously the wiring was
  missing and agents never saw the file.
- `tests/test_memory.py` (new, 9 fast offline tests) covers `read_memory`
  (missing/returns content), `memory_section` (empty/block), `update_memory`
  (replace/append/invalid mode), system-prompt injection, and auto-discovery.
- `tests/test_tools.py` count is 20 (Phase 2b additions remain green).
