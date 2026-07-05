# Agent Module Refactoring Plan

## Executive Summary

This document tracks the refactoring of the agent subsystem in `/workspaces/harness/`. The work has progressed through three phases (P0-P2), with significant structural improvements already made. This plan serves as both a historical record and forward-looking guide for any subsequent agent working on this codebase.

**Current Status:** ✅ P0-P2 complete | ⏳ P3-P7 remaining

---

## Completed Work

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

## Current Architecture (Post-P2)

### File Structure
```
agent/                          # All agent-related code lives here
├── __init__.py                 # Clean barrel exports with backward-compat re-exports
├── types.py                    # AgentType dataclass + YAML loading (unchanged)
├── discovery.py                # discover_agents(), get_agent_yaml() [MOVED from root]
├── task_list.py                # Task, TaskList dataclasses (unchanged)
├── executor.py                 # NEW: ToolExecutor — dispatch + error handling [NEW in P2]
├── core.py                     # Agent class — simplified tool handling via executor
└── loop.py                     # Interactive REPL (UNCHANGED)

utils.py                        # REMOVED: build_system_prompt() was here, now deleted
```

### What the Executor Does Now
The `ToolExecutor` handles three responsibilities previously embedded in `Agent.handle_prompt()`:
1. **Dispatch** — calls tools via `tools.dispatcher.dispatch()`
2. **Error wrapping** — creates standardized error ToolResult objects (3× code → 1 method)
3. **Termination blocking** — manages submit_results circuit breaker logic

The Agent class now focuses on orchestration: managing conversation state, calling LLM, deciding what to do next. It no longer needs to know *how* tools are implemented.

---

## Remaining Work

### Phase 3: Task State Public API (NEXT)

**Goal:** Make task list accessible via public API instead of private `_task_list` attribute.

**Why Now:** Currently external code accesses `CURRENT_AGENT.get()._task_list.tasks` — reaching into a private attribute of an unrelated class. This is fragile and tests already struggle with it (see known test failures below).

**Proposed Changes:**
1. Keep `TaskList` in its own file but add property accessors on Agent:
   ```python
   @property
   def task_list(self) -> TaskList:
       return self._task_list
   ```

2. Update `/workspaces/harness/commands/tasks.py`:
   ```python
   # Before: current_agent._task_list.tasks
   # After:  current_agent.task_list.tasks
   ```

3. Consider whether `_inject_task_state()` should delegate to a state-aware transformer or stay in Agent (it's closely tied to conversation management).

**Files Affected:** `agent/core.py`, `commands/tasks.py`, possibly new `agent/state.py` if we want deeper separation.

---

### Phase 4: System Prompt Consolidation (Deferred)

**Goal:** Merge remaining system prompt building into single canonical path.

**Status:** Partially done in P0. The old `build_system_prompt()` is gone, but `AgentType._build_system_prompt()` only appends cwd name — it doesn't do the full directory listing or AGENTS.md inclusion that the deleted function did.

**Decision Point:** Whether to:
- (A) Enhance `_build_system_prompt()` to include full functionality
- (B) Leave as-is since inline YAML prompts are now preferred

This depends on whether downstream consumers actually need the old behavior. Check `/workspaces/harness/sample_config/agents/*.yaml` and runtime usage before deciding.

---

### Phase 5: Eliminate Circular Imports (Deferred)

**Goal:** Create dedicated modules for constants and context vars to allow top-level imports throughout.

**Current State:** Several lazy imports remain due to circular dependency concerns:
- `agent/core.py`: imports `filter_tool_schemas`, `TaskList` lazily inside methods
- `tools/run_subagent.py`: imports from agent lazily
- `commands/sub.py`: same pattern

**Proposed Structure:**
```python
# agent/constants.py — no dependencies on other agent modules
RESPONSE = "response"
TOOL_CALL = "tool_call"  
TOOL_RESULT = "tool_result"
ERROR = "error"

# agent/context.py — minimal, no agent imports
import contextvars
CURRENT_AGENT = contextvars.ContextVar("current_agent", default=None)

def get_current_agent():
    return CURRENT_AGENT.get()
```

**Risk:** Medium. Changing import order can break things in subtle ways. Test thoroughly with full suite after any change.

---

### Phase 6: Public Properties for Private Attributes (Deferred)

**Goal:** Expose `_ollama_host`, `_client`, `_context_length` as public properties since external code reads them directly.

**Files Requiring Updates:**
- `agent/core.py` — add @property decorators
- `commands/sub.py` — change `sub_agent._client` → `sub_agent.client`
- `harness.py` — change `agent._context_length` → `agent.context_length`

**Low Risk** — purely additive, no behavior changes.

---

### Phase 7: Additional Cleanup (Deferred)

Minor improvements identified but low priority:
- Remove duplicate imports in `__init__.py`
- Tighten up docstrings that reference removed functions
- Consider whether `_inject_task_state()` should be extracted or stay in Agent

---

## Known Test Failures (Pre-existing, Not Caused by Refactoring)

As of P2 completion: **8 tests failing, 123 passing**

### Category A: test_tasks_command.py (3 failures)
```python
TypeError: 'unittest.mock.Mock' object does not support the context manager protocol
```
**Root Cause:** Python 3.14 compatibility issue — `Mock()` no longer supports `with` statements natively. Tests use invalid pattern: `with Mock() as mock_display:`

**Fix Required:** Replace with proper `patch()` usage or create Mock instances that explicitly support context manager protocol.

### Category B: test_skills.py (5 failures)
```python
AssertionError: Expected 1 skill, found 0
[skills] Warning: Skills directory not found: /tmp/.../.harness_py/skills
```
**Root Cause:** Test environment doesn't have skills directories set up. Tests assume skills are discoverable but the test fixtures don't create them properly.

**Fix Required:** Either mock skill discovery paths or ensure test fixtures create proper skill directory structures before running tests.

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

---

## Next Agent: Where to Start

If you're picking up this refactoring after us:

1. **Run tests first** to establish current baseline:
   ```bash
   cd /workspaces/harness && python -m pytest tests/ 2>&1 | tail -10
   ```

2. **Decide on Phase 3 vs Phase 5 order:** 
   - Phase 3 (task state API) has higher immediate impact on code clarity
   - Phase 5 (circular imports) is more foundational but riskier
   
3. **Check test failures** — the 8 known failures need fixing regardless of which phase you tackle next. They're mechanical issues, not design problems.

4. **Read current state of key files:**
   - `/workspaces/harness/agent/core.py` (heavily simplified from original)
   - `/workspaces/harness/agent/executor.py` (newly created)
   - `/workspaces/harness/agent/__init__.py` (re-export heavy)

5. **Commit after each phase** with descriptive messages following the pattern established in commit `543f80e`.

---

## Commit History Reference

Key commits tracking this refactoring:
- `543f80e` — P0-P2 complete (consolidation + executor extraction)
- Previous commits relate to earlier work on task lists, sub-agent infrastructure

Use `git log --oneline agent/` to see evolution of the agent package specifically.
