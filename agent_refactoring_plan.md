# Agent Module Refactoring Plan

## Executive Summary

The agent subsystem spans 10 files totaling ~1,400 lines across the `agent/` package (835 LOC), `agents_discovery.py` (126 LOC), and three callers (`harness.py`, `commands/sub.py`, `commands/tasks.py`). The code has grown organically and exhibits several structural issues: a **God Agent** class, duplicated system-prompt logic, inconsistent naming/organization, tight coupling between agent lifecycle management and tool dispatch, and scattered concerns that blur package boundaries.

This plan proposes consolidating the subsystem into a cleaner architecture without changing any external behavior — all existing imports must remain resolvable.

---

## Part 1: Current Architecture Analysis

### 1.1 File Inventory & Responsibilities

| File | Lines | Responsibility |
|------|-------|---------------|
| `agent/__init__.py` | 27 | Barrel export, re-exports everything from submodules |
| `agent/core.py` | 414 | **God class** — Agent lifecycle, conversation loop, tool dispatch, task list injection, sub-agent spawning, summarization |
| `agent/loop.py` | 76 | Interactive REPL: prompt → command detection → display routing |
| `agent/types.py` | 106 | YAML loading for agent definitions (AgentType dataclass) |
| `agent/utils.py` | 77 | Tool schema filtering + legacy system-prompt builder |
| `agent/task_list.py` | 135 | Task state machine (TaskList, Task dataclasses) |
| `agents_discovery.py` | 126 | YAML file discovery across project/global paths (at package root, not in `agent/`) |
| `tools/run_subagent.py` | 199 | Sub-agent execution harness (calls Agent.spawn_subagent) |
| `harness.py` | 122 | Entry point — wires up agent + skills → starts loop |
| `commands/sub.py` | 70 | `/sub` command handler |
| `commands/tasks.py` | 48 | `/tasks` command handler |

### 1.2 Dependency Graph (Simplified)

```
harness.py ──────────► agent.Agent + AgentType, user_loop
     │                      ▲                    │
     ├──── discover_agents()│                     ├── handle_prompt()
     │                      │                    │
     ▼                      │                    ▼
 agents_discovery.py    tools/run_subagent  commands/sub.py, commands/tasks.py
                          (sub-agent runner)        │
                                                    │
                              agent.core.CURRENT_AGENT ───► commands/tasks.py
                              tools/init_task_list, update_task_status
```

### 1.3 Key Coupling Patterns Identified

| Coupling | Where | Issue |
|----------|-------|-------|
| `Agent` ↔ `tools.dispatcher` | `handle_prompt()` calls `dispatch(func_name, args)` | Agent knows about the dispatcher — it should not need to know how tools are implemented |
| `Agent` ↔ `agent.task_list` | `_inject_task_state()`, `_task_list` field | Task state is tightly bound into the Agent conversation loop |
| `Agent` ↔ `tools.tool_result.ToolResult` | Error paths in `handle_prompt()` create ToolResult objects directly | Domain concern (agent) depends on tool infrastructure detail |
| `harness.py` ↔ `skills_discovery` + `agents_discovery` + `agent` | Entry point imports and wires everything | Bootstrap file is a "god orchestrator" itself |
| `tools/run_subagent` ↔ `agent.core.CURRENT_AGENT` | Uses contextvar to find parent agent | Indirect coupling via module-level state |

---

## Part 2: Identified Issues in Detail

### Issue #1 — The God Agent Class (`agent/core.py`, 414 lines)

**Current state:** One class, `Agent`, handles:
- Conversation message history management
- LLM API calls (duplicated between `_chat()` and `handle_prompt()`)
- Tool schema resolution at init time
- Ollama client host normalization
- Injected text queueing for skill interception
- Task list injection into messages (cache-friendly wrapping)
- Tool dispatch via the global dispatcher
- Termination circuit breaker logic (submit_results blocking)
- Sub-agent factory method (`spawn_subagent`)
- Conversation summarization

**Problems:**
1. **Single Responsibility Violation**: The Agent class handles at least 6 distinct concerns that should be separate classes/services.
2. **Dead code**: `_chat()` is defined but never called — `handle_prompt` duplicates the Ollama chat call inline (lines ~158-170 vs lines ~94-103).
3. **Testability**: With all concerns fused, unit testing requires constructing full Agent instances even to test individual features like task injection or tool filtering.

### Issue #2 — Duplicated System-Prompt Logic

Two separate functions build system prompts with similar goals:

| Function | Location | What it does |
|----------|----------|-------------|
| `AgentType._build_system_prompt()` | `agent/types.py` lines 30-45 | Appends cwd **name** only to inline YAML prompt |
| `build_system_prompt()` | `agent/utils.py` lines 57-81 | Reads a file, appends cwd **contents listing**, optionally appends AGENTS.md |

Neither is consistently used. The old `build_system_prompt()` in utils.py appears unused by any production path (it's only called from tests). This indicates migration residue — the system prompt moved into YAML but the old builder was never deleted.

### Issue #3 — `agents_discovery.py` Lives at Package Root

The file `agents_discovery.py` (126 LOC) provides agent YAML discovery but lives at `/workspaces/harness/agents_discovery.py` rather than inside the `agent/` package. This breaks the mental model: everything agent-related should be under `agent/`. Additionally, it's named with a plural (`agents`) while the package is singular (`agent`).

### Issue #4 — Naming Inconsistency: `agent` vs `agents_discovery.py`

- Package name: `agent` (singular)
- Discovery module: `agents_discovery` (plural "s")
- Directory for YAML configs: `agents/` (plural, matches discovery)

This creates cognitive dissonance. The package should be consistently named either all-singular or all-plural.

### Issue #5 — Tool Dispatch Logic Embedded in Agent

In `Agent.handle_prompt()` (lines ~172-230), the code:
1. Imports `dispatch` from `tools.dispatcher` inline
2. Creates `ToolResult` objects directly for error handling
3. Manages tool call result formatting and message history appending

This is essentially a **tool execution pipeline** that should be extracted into its own class (e.g., `ToolExecutor`). The Agent should only know "I have tools" not "how each tool gets dispatched."

### Issue #6 — Task List Management Is an Agent Detail, Not a Public Concern

`TaskList` is instantiated privately inside `Agent.__init__()` and used exclusively by:
- `Agent._inject_task_state()` (prepends task state to LLM messages)
- `Agent.handle_prompt()` (blocks submit_results when tasks are incomplete)

External consumers (`commands/tasks.py`, `tools/initialize_task_list.py`, `tools/update_task_status.py`) interact with it only through the `CURRENT_AGENT` context variable, accessing private `_task_list`. This is fragile — tests and commands reach into a private attribute of an unrelated class.

### Issue #7 — Circular Import Fragility

Multiple files use lazy imports specifically to avoid circular imports:
- `agent/core.py`: imports `filter_tool_schemas`, `TaskList`, `AgentType` lazily inside methods
- `tools/run_subagent.py`: imports `from agent import Agent, RESPONSE, TOOL_CALL` inside function body
- `commands/sub.py`: same lazy import pattern

This makes the code harder to reason about and harder for IDE tooling/static analysis.

### Issue #8 — `filter_tool_schemas` Is in the Wrong Place

The function lives in `agent/utils.py` but is conceptually a **tool infrastructure** concern, not an agent-specific concern. It filters schemas by name list — this could be used by any component that needs to select tools from a registry (not just agents).

### Issue #9 — `Agent._ollama_host` Is a Private Attribute Used Externally

In multiple places, code reads `parent_agent._ollama_host` and `agent._client`:
- `Agent.spawn_subagent()` creates new Ollama clients using `_ollama_host`
- `commands/sub.py` passes `sub_agent._client` to `user_loop`
- `harness.py` uses `agent._context_length` in display calls

These should be public properties or the loop should accept an abstracted interface.

### Issue #10 — Error Handling Creates ToolResult Directly in Agent

In `handle_prompt()`, error paths (unknown function, unexpected exception) manually construct `ToolResult` objects with hardcoded formatting:
```python
return_result = ToolResult(
    llm_text=description,
    display_text=description,
    type_tag="text",
    title=f"Error: {func_name}",
    theme="error"
)
```

This is code duplication — the same pattern appears 3 times in `handle_prompt()`. It also forces a dependency on `tools.tool_result` from within the agent package.

---

## Part 3: Proposed Refactoring Plan

### Phase 1: Consolidate Discovery Into Agent Package

**Files affected:** `agents_discovery.py`, `agent/__init__.py`
**Risk:** Low — pure rename/move operation

#### Steps:

1. **Move** `agents_discovery.py` → `agent/discovery.py` (rename to singular)
2. **Update imports**: Change all references from `from agents_discovery import ...` to `from agent.discovery import ...`:
   - `harness.py` line 17
   - `tools/run_subagent.py` line 53
3. **Re-export** in `agent/__init__.py`: Add `from agent.discovery import discover_agents, get_agent_yaml, get_agent_yaml_paths` to maintain backward compatibility (so existing imports still work)
4. **Rename** module-level `_merge_agent_discoveries` to be private or keep as-is — no callers outside the package need it

#### Rationale:
- Keeps all agent-related code under one package boundary
- Eliminates the singular/plural naming inconsistency at the file level
- Discovery is inherently an "agent configuration" concern

---

### Phase 2: Extract Tool Execution Pipeline from Agent

**Files affected:** New `agent/executor.py`, modified `agent/core.py`
**Risk:** Medium — involves behavioral changes to message handling

#### Steps:

1. **Create** `agent/executor.py` containing a new `ToolExecutor` class:

```python
class ToolExecutor:
    """Handles tool dispatch, result formatting, and error wrapping."""
    
    def __init__(self, agent_name: str):
        self._agent_name = agent_name
    
    def execute(self, func_name: str, args: dict) -> "ToolResult":
        """Dispatch a tool call. Returns ToolResult (success or error)."""
        # ... dispatch logic extracted from Agent.handle_prompt
    
    def handle_submit_results_block(
        self, task_list: "TaskList"
    ) -> tuple[dict, "ToolResult"]:
        """Return (message, result) to block termination if tasks are incomplete."""
```

2. **Refactor** `Agent.__init__()` to accept an optional `ToolExecutor`:
   - Move `_ollama_host` normalization and tool schema filtering into a dedicated setup step
   - Keep the executor as `self._executor`

3. **Simplify** `Agent.handle_prompt()`:
   - Replace inline dispatch logic (lines ~158-230) with:
     ```python
     if func_name == "submit_results" and self._task_list.has_incomplete_tasks():
         # use executor to get blocked message + result
     return_result = self._executor.execute(func_name, args)
     ```

4. **Remove** direct `from tools.tool_result import ToolResult` from `core.py` — the executor owns that dependency.

#### Rationale:
- Agent now only concerns itself with "orchestration" (what to do next), not "execution" (how to call a tool)
- Tool executor can be unit-tested independently
- Error formatting is consolidated in one place instead of duplicated 3 times

---

### Phase 3: Extract Task State Management Into Its Own Service

**Files affected:** New `agent/state.py` or refactor `agent/task_list.py`, modified `agent/core.py`, modified `commands/tasks.py`
**Risk:** Medium — changes how task state is accessed globally

#### Steps:

1. **Create** a `TaskStateManager` class (or keep `TaskList` as-is but move it to the public API):
   - Keep `TaskList` and `Task` in their own file (`agent/task_list.py`)
   - Create an `AgentState` coordinator that owns both `TaskList` AND manages injected text queue

2. **Refactor** `Agent.__init__()` to use the state manager:
   ```python
   self._state = AgentState()  # wraps TaskList + injection queue
   ```

3. **Replace** `CURRENT_AGENT.get()._task_list` access in external modules with a proper public API:
   - Add `agent.get_current_agent_state()` function that returns the state manager (not the agent itself)
   - Or add property accessors on Agent: `agent.task_list`, `agent.injected_text`

4. **Update** `commands/tasks.py` to use the new public API instead of `_task_list`:
   ```python
   # Before: current_agent._task_list.tasks
   # After:  current_agent.state.get_tasks()
   ```

5. **Remove** `_inject_task_state()` from Agent and delegate it to a state-aware message transformer, or keep it as a thin delegator.

#### Rationale:
- Task management is a cross-cutting concern that shouldn't be buried inside the Agent class
- The `CURRENT_AGENT._task_list` pattern is fragile (private attribute access)
- An `AgentState` object provides a clean API surface for any component needing task data

---

### Phase 4: Consolidate System Prompt Logic

**Files affected:** `agent/types.py`, `agent/utils.py`
**Risk:** Low — the old `build_system_prompt()` is only used by tests

#### Steps:

1. **Remove** `build_system_prompt()` from `agent/utils.py`:
   - It's dead code (never called in production) and duplicates functionality already in `AgentType._build_system_prompt()`
   - Remove its re-export from `agent/__init__.py`

2. **Enhance** `AgentType._build_system_prompt()`:
   - Add an optional parameter to include the full directory listing (currently only includes cwd name)
   - Add AGENTS.md support if needed
   - This makes it a complete replacement for the old utility function

3. **Update** tests in `tests/test_harness.py` that import `build_system_prompt`:
   - Migrate them to use `AgentType._build_system_prompt()` directly, or remove those tests if they test obsolete behavior

#### Rationale:
- Eliminates duplicate functionality
- One canonical way to build system prompts → easier maintenance
- Removes confusing dead code from the public API

---

### Phase 5: Eliminate Circular Imports

**Files affected:** `agent/__init__.py`, `tools/run_subagent.py`, `commands/sub.py`
**Risk:** Low — refactoring imports only

#### Steps:

1. **Create** a dedicated `agent/constants.py` module for the type constants:
   ```python
   RESPONSE = "response"
   TOOL_CALL = "tool_call"
   TOOL_RESULT = "tool_result"
   ERROR = "error"
   ```

2. **Update** imports across the codebase:
   - `tools/run_subagent.py`: Change `from agent import Agent, RESPONSE, TOOL_CALL` → 
     `from agent.constants import RESPONSE, TOOL_CALL; from agent.core import Agent`
   - Same pattern in any other file importing these constants

3. **Move** `CURRENT_AGENT` to a dedicated module (`agent/context.py`) instead of keeping it in `core.py`:
   ```python
   # agent/context.py — no dependencies on core.py, loop.py, etc.
   import contextvars
   CURRENT_AGENT = contextvars.ContextVar("current_agent", default=None)
   
   def get_current_agent():
       return CURRENT_AGENT.get()
   ```

4. **Update** `agent/__init__.py` to re-export from the new modules cleanly:
   ```python
   from agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
   from agent.context import CURRENT_AGENT, get_current_agent
   # ... etc.
   ```

5. **Fix** lazy imports in `agent/core.py`: Since `types.py`, `task_list.py` have no back-references to `core.py`, they can be imported at module top-level:
   - `from agent.types import AgentType` — safe (no circular dep)
   - `from agent.task_list import TaskList` — safe (no circular dep)

#### Rationale:
- Separates the "what" (constants, context vars) from the "how" (Agent class with complex logic)
- Allows top-level imports instead of lazy ones → better static analysis, faster startup, clearer dependency graph

---

### Phase 6: Clean Up Naming & Package Structure

**Files affected:** All `agent/` files, `harness.py`, `commands/sub.py`
**Risk:** Low to Medium — cosmetic + structural improvements

#### Steps:

1. **Decide on naming convention**: Recommend keeping the package as `agent` (singular) since it refers to "the agent system" not "multiple agents." Update `agents_discovery.py` → `agent/discovery.py` (already planned in Phase 1). The directory `agents/` for YAML configs can stay plural since it contains multiple agent definitions.

2. **Make `_ollama_host`, `_client`, `_context_length` public properties**:
   ```python
   @property
   def ollama_host(self) -> str:
       return self._ollama_host
   
   @property  
   def client(self):
       return self._client
   
   @property
   def context_length(self) -> int:
       return self._context_length
   ```

3. **Update external consumers** (`commands/sub.py`, `harness.py`) to use public properties instead of `_ollama_host` and `_context_length`.

4. **Remove duplicate import in `agent/__init__.py`**: The file imports from each submodule AND re-exports — verify nothing is being imported twice unnecessarily. Currently it's fine but could be tightened.

---

### Phase 7: Address the Dead `_chat()` Method

**Files affected:** `agent/core.py`
**Risk:** Low — removing dead code

#### Steps:

1. **Delete** `_chat()` method from `Agent` class (lines ~94-103). It is defined but never called anywhere in the codebase. The actual LLM call happens inline in `handle_prompt()`.

2. If you want to *use* it, refactor `handle_prompt()` to call `self._chat(messages_to_send)` instead of duplicating the Ollama client chat call — this eliminates ~10 lines of duplicated request-building code. Recommendation: just delete it for now; if refactoring in Phase 2 is done first, you can have the executor own the LLM call.

---

## Part 4: Proposed Final File Structure

After all phases are complete:

```
agent/                          # All agent-related code lives here
├── __init__.py                 # Clean barrel exports (re-exports from submodules)
├── constants.py                # RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR strings
├── context.py                  # CURRENT_AGENT contextvar + accessor function
├── types.py                    # AgentType dataclass + YAML loading
├── discovery.py                # discover_agents(), get_agent_yaml(), etc. (moved from root)
├── task_list.py                # Task, TaskList dataclasses (unchanged)
├── state.py                    # NEW: AgentState coordinator (TaskList + injection queue)
├── executor.py                 # NEW: ToolExecutor — dispatch + error handling
├── core.py                     # Agent class (greatly simplified — ~250 LOC)
│                              #   Only: conversation management, orchestration, summarization
└── loop.py                     # Interactive REPL (unchanged structure)

tools/
├── run_subagent.py             # Uses new public API; fewer lazy imports needed
```

External callers (`harness.py`, `commands/sub.py`, `commands/tasks.py`) access the agent subsystem through a cleaner, more predictable import surface.

---

## Part 5: Migration Strategy & Risk Mitigation

### Order of Execution

| Phase | Priority | Estimated LOC Change | Risk | Depends On |
|-------|----------|---------------------|------|-----------|
| **P0**: Eliminate dead code (`_chat()`, `build_system_prompt()`) | Immediate | -30 lines | None | — |
| **P1**: Move discovery into package, fix naming | High | +5 (re-exports) | Very Low | P0 |
| **P2**: Extract ToolExecutor | Medium | +80 new / -60 existing | Low | P0 |
| **P3**: Task state public API | Medium | +40 new / -15 existing | Medium | P2 (for cleaner separation) |
| **P4**: Fix circular imports via constants/context modules | Medium | +25 new / -10 lazy | Low | P1, P2 |
| **P5**: Public properties for private attributes | Low | -10 access changes | Very Low | P3 |

### Backward Compatibility Guarantees

To ensure no existing import breaks during migration:

```python
# In agent/__init__.py — maintain all current re-exports PLUS new ones:
from agent.types import AgentType
from agent.core import Agent, CURRENT_AGENT, RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from agent.utils import filter_tool_schemas
from agent.loop import user_loop
from agent.discovery import discover_agents, get_agent_yaml  # NEW location, same names

# In harness.py — can still do:
# from agents_discovery import discover_agents   (if kept at root for compat)
# or migrate to: from agent.discovery import discover_agents
```

### Testing Strategy

1. **Run existing tests first** as a baseline to confirm nothing is broken before starting refactoring
2. After each phase, run the full test suite (`pytest tests/`) to catch regressions early
3. The `test_agent.py` file (660+ lines of tests) covers most agent functionality — if these pass after Phase 5, the public API is intact

### Rollback Plan

Since all changes maintain import compatibility (via re-exports in `__init__.py`), any phase can be rolled back independently without breaking dependent code. The worst case: revert one file change and tests will still pass because the old import paths are preserved.

---

## Part 6: Specific Code Change Details (By File)

### `agent/core.py` — After Refactoring (target structure)

```python
class Agent:
    """Owns the conversation state and handles a single user turn."""
    
    def __init__(self, agent_type, ollama_client, context_length, 
                 tool_schemas=None, extra_tools=None):
        # 1. Store core attributes as public properties
        self._agent_type = agent_type
        self._client = ollama_client
        self._context_length = context_length
        
        # 2. Normalize host (kept from current logic)
        raw_host = getattr(ollama_client, "host", None) or os.environ.get(...)
        self._ollama_host = ...
        
        # 3. Create executor and state manager (new!)
        self._executor = ToolExecutor(agent_type.name)
        self._state = AgentState()
        
        # 4. Resolve tools via executor (delegated)
        if tool_schemas:
            self._tools = filter_tool_schemas(agent_type, tool_schemas)
        else:
            self._tools = []
        if extra_tools:
            self._tools.extend(extra_tools)
        
        # 5. Initialize conversation messages
        self.messages: list[dict] = [{"role": "system", "content": agent_type.system_prompt}]
        self._injected_text: Optional[str] = None
        
        CURRENT_AGENT.set(self)
    
    @property
    def ollama_host(self): return self._ollama_host
    
    @property
    def context_length(self): return self._context_length
    
    # --- injection API (kept, minor changes) ---
    
    # --- Task state management (delegated to AgentState) ---
    
    # --- LLM call (executor owns this in Phase 2) ---
    
    def handle_prompt(self, user_input: str):
        """Simplified: orchestrates the loop, delegates execution."""
        # ... much shorter than current ~60-line tool handling block
    
    @classmethod
    def spawn_subagent(cls, sub_name, parent_agent=None, ...):
        """Factory — unchanged in behavior."""
    
    def summarize(self, summary_prompt=None) -> str:
        """Unchanged — this is agent-specific logic that belongs here."""
```

### `agents_discovery.py` → `agent/discovery.py` (no changes to content needed)

Just move the file. Update import references in:
- `harness.py`: line 17
- `tools/run_subagent.py`: line 53

Re-export from `agent/__init__.py` for backward compatibility.

### `commands/tasks.py` — After Refactoring

```python
from agent.context import get_current_agent
# No more direct access to CURRENT_AGENT._task_list

def cmd_tasks(rest: str, agent=None) -> bool | None:
    current = get_current_agent()
    if not current or not hasattr(current, 'state'):
        display_message_panel("No active task list.", ...)
        return False
    
    tasks = current.state.get_tasks()  # public API instead of _task_list.tasks
    ...
```

---

## Part 7: What NOT to Refactor (Out of Scope)

The following should be **left alone** because they are working well and changing them would add risk without proportional benefit:

1. **`agent/loop.py`** — The interactive REPL loop is clean, focused, and works correctly. Its only coupling (`from agent import Agent`) will resolve naturally after Phase 4.
2. **`tools/run_subagent.py`** — The termination protocol and sub-agent execution flow are well-designed. Only the imports need updating.
3. **`tools/tool_result.py`** — `ToolResult` is a good abstraction that decouples display from LLM text. Keep it as-is; have the new executor own its creation.
4. **`agent/task_list.py`** — The TaskList/Task implementation itself is solid and well-tested. The issue isn't with the code but with *where* it's accessed (via private attribute of Agent). Phase 3 addresses this without changing task_list.py itself.
5. **Tests** — Do not refactor tests. They serve as behavioral regression guards. Only update import paths if they reference removed symbols.

---

## Part 8: Summary of Benefits

| Before | After |
|--------|-------|
| `agent/core.py` is 414 LOC with 7+ responsibilities | ~250 LOC, focused on conversation orchestration only |
| System prompt logic duplicated between two functions | Single canonical `_build_system_prompt()` in AgentType |
| Discovery module at package root (`agents_discovery.py`) | Inside agent package (`agent/discovery.py`) |
| Tool dispatch embedded in handle_prompt() with 3× error formatting duplication | Dedicated `ToolExecutor` class, single responsibility |
| Task state accessed via `CURRENT_AGENT._task_list` (private attribute) | Public API: `agent.state.get_tasks()` or `agent.task_list` property |
| Circular imports force lazy imports throughout | Clean module dependency graph with constants/context separation |
| `_ollama_host`, `_context_length` are private, used externally | Public properties expose what callers need |
| Dead code (`_chat()`, `build_system_prompt()`) in the codebase | Eliminated — no confusion for future developers |
