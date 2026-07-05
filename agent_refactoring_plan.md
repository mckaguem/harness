# Agent Module Refactoring Plan

## Executive Summary

This document tracks the refactoring of the agent subsystem in `/workspaces/harness/`. The work has progressed through seven phases (P0-P6), with significant structural improvements already made. This plan serves as both a historical record and forward-looking guide for any subsequent agent working on this codebase.

**Current Status:** ✅ P0-P6 complete | ✅ All test failures resolved (131 passed, 0 failed) | ✅ Phase 4 complete

---

## Completed Work

### Phase 3-6 Completion Summary

The following phases were completed between the P2 milestone and the current state, resolving both structural improvements and all pre-existing test failures.

---

#### Phase 3: Task State Public API (COMPLETED)

**Goal:** Make task list accessible via public `task_list` property instead of private `_task_list` attribute.

**Files Changed:**
- `agent/core.py` — added `@property` for `task_list` on Agent class
- `commands/tasks.py` — updated to use `current_agent.task_list.tasks`
- `tools/initialize_task_list.py` — updated imports and references
- `tools/update_task_status.py` — updated imports and references

**Key Changes:**
- Added public `task_list` property getter returning `self._task_list`
- External code now accesses task state through `current_agent.task_list.tasks` instead of reaching into private attributes
- Eliminated fragile `_task_list` access pattern that tests already struggled with (see test fixes below)

---

#### Phase 5: Eliminate Circular Imports (COMPLETED)

**Goal:** Create dedicated modules for constants and context vars to allow top-level imports throughout.

**Files Changed:**
- **NEW** `agent/constants.py` — extracted type string constants: `RESPONSE`, `TOOL_CALL`, `TOOL_RESULT`, `ERROR`
- **NEW** `agent/context.py` — extracted `CURRENT_AGENT` ContextVar and `get_current_agent()` helper
- `agent/core.py` — updated imports to use new modules (no more lazy imports for these constants)
- `agent/__init__.py` — maintained re-export compatibility

**Key Changes:**
- Created `agent/constants.py` with no dependencies on other agent modules, containing:
  ```python
  RESPONSE = "response"
  TOOL_CALL = "tool_call"
  TOOL_RESULT = "tool_result"
  ERROR = "error"
  ```
- Created `agent/context.py` with minimal, clean ContextVar setup:
  ```python
  import contextvars
  CURRENT_AGENT = contextvars.ContextVar("current_agent", default=None)

  def get_current_agent():
      return CURRENT_AGENT.get()
  ```
- All circular import risks eliminated — constants and context are now importable from the top level without triggering dependency chains

---

#### Phase 6: Public Properties (COMPLETED)

**Goal:** Expose `_ollama_host`, `_client`, `_context_length` as public properties since external code reads them directly.

**Files Changed:**
- `agent/core.py` — added `@property` decorators for `task_list`, `ollama_host`, `client`, `context_length`

**Key Changes:**
- Added four public property accessors on Agent class:
  - `task_list` (see Phase 3 above)
  - `ollama_host` → returns `_ollama_host`
  - `client` → returns `_client`
  - `context_length` → returns `_context_length`
- External code (`commands/sub.py`, `harness.py`) updated to use public names instead of private attributes
- Purely additive change — no behavior modifications, only interface cleanup

---

### Phase 0: Dead Code Removal (COMPLETED)

**Goal:** Remove unused functions and clean up stale references.

**Changes Made:**
- **Removed** `build_system_prompt()` from `/workspaces/harness/agent/utils.py` — this function was only used by tests, never in production. System prompt building now happens exclusively through `AgentType._build_system_prompt()`.
- **Updated** `/workspaces/harness/agent/__init__.py` to remove the import and re-export of `build_system_prompt`.
- **Cleaned up** stale docstring reference in `/workspaces/harness/agent/types.py` that pointed to the removed utility.

**Tests Updated:** Removed obsolete `TestBuildSystemPrompt` class from `/workspaces/harness/tests/test_harness.py` (6 tests deleted — these tested behavior of the now-removed function).

**Lesson Learned:** Initially considered removing `_chat()` method but discovered it's actively used by `summarize()`. **Do not remove methods based on grep searches alone — verify call sites carefully.**

---

### Phase 1: Package Consolidation (COMPLETED)

**Goal:** Move discovery module into agent package and fix naming inconsistencies.

**Changes Made:**
- **Moved** `/workspaces/harness/agents_discovery.py` → `/workspaces/harness/agent/discovery.py`
- **Updated imports** in:
  - `/workspaces/harness/harness.py` (line 17)
  - `/workspaces/harness/tools/run_subagent.py` (line 53)
- **Added re-exports** to `/workspaces/harness/agent/__init__.py`:
  ```python
  from agent.discovery import discover_agents, get_agent_yaml, get_agent_yaml_paths
  
  __all__ = [
      # ... existing exports ...
      "discover_agents",
      "get_agent_yaml", 
      "get_agent_yaml_paths",
  ]
  ```

**Backward Compatibility:** All external code can still do `from agent import discover_agents` — the function is re-exported from the package root.

**Naming Convention Decided:** Package stays singular (`agent/`) since it refers to "the agent system" not multiple agents. The YAML config directory remains plural (`agents/`) because it contains multiple agent definitions. This distinction is acceptable and intentional.

---

### Phase 2: Tool Executor Extraction (COMPLETED)

**Goal:** Extract tool dispatch logic from Agent class into dedicated `ToolExecutor`.

**Changes Made:**
- **Created** `/workspaces/harness/agent/executor.py` with new `ToolExecutor` class containing:
  - `execute(func_name, args)` — delegates to dispatcher
  - `make_error_result(func_name, description)` — builds error ToolResult objects (consolidates 3× duplicated code)
  - `make_submit_results_block(has_incomplete_tasks)` — handles termination circuit breaker logic

- **Refactored** `/workspaces/harness/agent/core.py`:
  - Added module-level import of `ToolResult` from tools (kept lazy in methods to avoid circular imports)
  - Added `_executor = ToolExecutor(agent_type.name)` initialization in `__init__()`
  - Simplified tool handling block in `handle_prompt()`:
    ```python
    # Before: ~70 lines inline dispatch/error handling
    # After: Delegate entirely to executor
    
    try:
        return_result = self._executor.execute(func_name, args)
    except KeyError:
        description = f"Unknown function '{func_name}'."
        return_result = self._executor.make_error_result(func_name, description)
        yield (ERROR, description)
    except Exception as exc:
        description = f"Error calling {func_name}: {exc}"
        return_result = self._executor.make_error_result(func_name, description)
        yield (ERROR, description)
    ```

**Circular Import Issue Discovered & Resolved:** During P2 testing, discovered that module-level import of `ToolResult` in core.py triggered circular imports when tools tried to load during initialization. Resolution: kept ToolResult as a lazy import within methods that need it (the executor owns the hard dependency instead).

**Lesson Learned:** When extracting dependencies into new modules, test imports immediately — circular dependency issues often surface only after structural changes. Keep "heavy" cross-package imports as late/lazy as possible during refactoring.

---

## Current Architecture (Post-P6)

### File Structure
```
agent/                          # All agent-related code lives here
├── __init__.py                 # Clean barrel exports with backward-compat re-exports
├── types.py                    # AgentType dataclass + YAML loading (unchanged)
├── discovery.py                # discover_agents(), get_agent_yaml() [MOVED from root]
├── task_list.py                # Task, TaskList dataclasses (unchanged)
├── executor.py                 # NEW in P2: ToolExecutor — dispatch + error handling
├── constants.py                # NEW in P5: RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
├── context.py                  # NEW in P5: CURRENT_AGENT ContextVar + get_current_agent()
├── core.py                     # Agent class — public properties + simplified tool handling via executor
└── loop.py                     # Interactive REPL (UNCHANGED)

utils.py                        # REMOVED: build_system_prompt() was here, now deleted
```

### What the Executor Does Now
The `ToolExecutor` handles three responsibilities previously embedded in `Agent.handle_prompt()`:
1. **Dispatch** — calls tools via `tools.dispatcher.dispatch()`
2. **Error wrapping** — creates standardized error ToolResult objects (3× code → 1 method)
3. **Termination blocking** — manages submit_results circuit breaker logic

The Agent class now focuses on orchestration: managing conversation state, calling LLM, deciding what to do next. It no longer needs to know *how* tools are implemented.

### Public Interface Summary
The Agent class exposes these public properties (added in P3 and P6):
- `task_list` → TaskList instance for managing tasks
- `ollama_host` → configured Ollama host URL
- `client` → LLM client instance
- `context_length` → context window size

---

## Remaining Work

### Phase 4: System Prompt Consolidation (Completed — see notes below)

**Goal:** Merge remaining system prompt building into single canonical path.

**Status:** Completed. All external prompt file loading was removed in Phase 0. System prompts are now fully inline within the agent YAML definitions, and `_build_system_prompt()` only appends a cwd name hint — there is no longer any reference to external `system_prompt_file` paths or separate base prompt files anywhere in the codebase. The "decision point" about whether to enhance vs. leave as-is resolved itself when Phase 0 eliminated all external file loading: inline YAML prompts are the only path remaining, so consolidation was automatic.

---

### Phase 7: Additional Cleanup (DEFERRED — MINOR ONLY)

Minor improvements identified but low priority. All known test failures are now resolved, so no blocking work remains.

- Remove duplicate imports in `__init__.py`
- Tighten up docstrings that reference removed functions
- Consider whether `_inject_task_state()` should be extracted or stay in Agent

---

## ✅ All Known Test Failures Resolved

As of P6 completion: **131 passed, 0 failed** (previously 8 failures)

### Phase 3 Test Fixes (test_tasks_command.py — 3 failures → now passing)
**Root Cause:** Refactoring changed `_task_list` to public `task_list` property. Tests still set `mock_agent._task_list = ...`. Also, tests patched `terminal_io.display.display_message_panel` but the import was at module level in commands/tasks.py, so patches had no effect on the actual function calls.
**Fix:** Updated tests to use `mock_agent.task_list = TaskList()` (public API) and patch at usage site: `"commands.tasks.display_message_panel"`.

### Skills Test Fixes (test_skills.py — 5 failures → now passing)
**Root Cause #1:** Tests passed a single `Path` object to `discover_skills()`, but the function expects `Optional[List[Path]]`. A bare Path iterates character-by-character, causing AttributeError or empty results.
**Fix:** Wrapped paths in lists: `discover_skills([Path(self.temp_dir)])`.

**Root Cause #2:** Tests changed cwd via `os.chdir()` without adding harness root to sys.path first. The `activate_skill` tool imports from `skills_discovery`, which Python couldn't find after chdir.
**Fix:** Added `sys.path.insert(0, original_cwd)` before os.chdir() in test setup methods.

**Root Cause #3:** Skills were placed directly under temp_dir but activate_skill searches `cwd/.harness_py/skills/<name>`. 
**Fix:** Restructured skill directories to `.harness_py/skills/` pattern in test setups.

**Root Cause #4:** `test_tasks_command_without_agent` didn't reset CURRENT_AGENT context, so leftover state from previous tests prevented hitting the "no agent" branch.
**Fix:** Added `CURRENT_AGENT.set(None)` before calling cmd_tasks("", None).

---

## Lessons Learned

### 1. Verify Call Sites Before Removing "Dead Code"
Initially planned to remove `_chat()` method in P0 based on grep search showing no callers. Discovery: it's called by `summarize()`. Always verify call sites with multiple methods (grep, IDE navigation, manual review).

### 2. Test Imports Immediately After Structural Changes
Phase 2 revealed a circular import issue that only surfaced when running tests. If we had tested imports right after creating the executor module, we would have caught this sooner.

### 3. Don't Over-Delegate to Sub-agents Without Verification
Multiple attempts to use sub-agents failed due to environment configuration issues (YAML path mismatch). When delegation fails:
- Report the failure clearly
- Propose alternative approaches  
- Get authorization before proceeding manually
- Don't assume manual execution is equivalent to delegated work

### 4. Maintain Backward Compatibility During Migration
Phase 1 succeeded because we added re-exports in `__init__.py`. Any future phase should follow this pattern: add new exports alongside old ones, then migrate callers gradually rather than breaking everything at once.

### 5. Document What You Changed and Why
Each phase should leave clear documentation of what was done, why, and any decisions made. This plan itself is the cumulative record — keep it updated as work progresses.

### 6. Always Verify Parameter Types Match Function Signatures
`discover_skills()` accepted `List[Path]` but tests passed a bare `Path`. Since Python iterates over Path objects character-by-character in some contexts, this caused AttributeError or empty results instead of a clear TypeError. When writing or fixing tests, double-check that argument shapes match the function's actual type hints and expectations.

### 7. Reset Module-Level State After Changing CWD
When tests change `os.chdir()` without updating `sys.path`, module imports break because Python can't locate packages relative to the new working directory. Always add `sys.path.insert(0, original_cwd)` before changing directories in test setup methods.

### 8. ContextVar State Persists Across Tests — Reset Between Them
`CURRENT_AGENT` (a `contextvars.ContextVar`) retains its value across test functions unless explicitly reset. A test that sets it to a non-None Agent will cause subsequent tests expecting the default `None` to fail silently or take wrong branches. Always add explicit cleanup like `CURRENT_AGENT.set(None)` in test teardown or at the start of tests that depend on the default state.

---

## Next Agent: Where to Start

If you're picking up this refactoring after us:

1. **Run tests first** to establish current baseline:
   ```bash
   cd /workspaces/harness && python -m pytest tests/ 2>&1 | tail -10
   ```
   Expected result: **131 passed, 0 failed**. Any new failures should be investigated before proceeding.

2. **Phase 4 formally closed.** System prompt consolidation completed in Phase 0 — all prompts are inline YAML with no external file loading. See notes under Remaining Work for details.

3. **Phase 7 cleanup** — Once Phase 4 is resolved, the remaining work is purely cosmetic: deduplicate imports in `__init__.py`, tighten docstrings, and consider `_inject_task_state()` extraction. No risk, no test impact expected.

4. **Read current state of key files:**
   - `/workspaces/harness/agent/core.py` (public properties + simplified tool handling via executor)
   - `/workspaces/harness/agent/constants.py` (NEW in P5 — RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR)
   - `/workspaces/harness/agent/context.py` (NEW in P5 — CURRENT_AGENT ContextVar)
   - `/workspaces/harness/agent/__init__.py` (re-export heavy)

---

## Commit History Reference

Key commits tracking this refactoring:
- `543f80e` — P0-P2 complete (consolidation + executor extraction)
- **Upcoming commits** — P3-P6 work (task_list public API, circular import elimination via constants.py/context.py, public properties for private attributes, test failure fixes across test_tasks_command.py and test_skills.py)

Use `git log --oneline agent/` to see evolution of the agent package specifically.