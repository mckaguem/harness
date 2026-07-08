# Comprehensive Refactor Plan for Harness Codebase

## Executive Summary
This document outlines a systematic refactoring strategy to improve code quality, reduce technical debt, and enhance maintainability. The plan addresses critical bugs, eliminates dead code, reduces coupling, and improves test coverage across the entire harness codebase (~3000 lines of Python).

## Analysis Overview
- **Total files analyzed**: 50+ Python source files
- **Key modules identified**: agent/, tools/, commands/, terminal_io/
- **Critical issues found**: 12 high-priority problems requiring immediate attention
- **Estimated effort**: 4 phases over multiple iterations

## Phase 1: Critical Fixes & Dead Code Removal (High Priority)

### 1.1 Fix `prompt_user()` Interface Mismatch [CRITICAL BUG]
**File**: `terminal_io/prompt.py` vs `commands/__init__.py`
**Issue**: Function defined without parameters but called with argument on line ~124
```python
# Current (broken):
def prompt_user() -> str:  # No parameters
    ...

# Called as:
choice = prompt_user(f"Enter session number...")  # TypeError!
```
**Fix**: Add optional `prompt` parameter to match call site expectations
**Risk**: Low - backward compatible change

### 1.2 Remove Dead Functions in display.py [DEAD CODE]
**File**: `terminal_io/display.py`
**Issue**: Four functions are defined but never called anywhere:
- `display_user_prompt()` 
- `display_tool_call_with_result()`
- `display_tool_success()`
- `_panel_title()` (helper, also duplicated inline)

**Fix**: Remove these 4 functions entirely to reduce maintenance burden
**Risk**: Zero - confirmed unused via codebase search

### 1.3 Eliminate Duplicate cmd_exit/cmd_quit [DUPLICATION]
**File**: `commands/__init__.py`
**Issue**: Two identical functions with different names, wasting ~20 lines
```python
def cmd_exit(rest, agent=None): ...  # Returns True
def cmd_quit(rest, agent=None): ...  # Identical body!
```
**Fix**: Create single `_cmd_exit()` function, reference it twice in COMMANDS dict:
```python
def _cmd_exit(_rest, agent=None):
    print_system("Goodbye!", "See you next time.")
    return True

COMMANDS = {
    'exit': _cmd_exit,
    'quit': _cmd_exit,  # Same function, different name in dict
    ...
}
```
**Risk**: Zero - behavior unchanged

### 1.4 Remove Unused console Singleton in speed.py [DEAD CODE]
**File**: `terminal_io/speed.py`
**Issue**: Creates Rich Console singleton that's never used (function returns string)
```python
console = Console()  # Created but no console.print() calls exist
```
**Fix**: Remove the unused import and instantiation entirely
**Risk**: Zero - confirmed no usage

### 1.5 Clean Up Dead Imports [DEAD CODE]
**Files**: 
- `terminal_io/prompt.py` - remove `import os` (line 2)
- `agent/core.py` - remove `from pprint import pprint` (line 7)

**Fix**: Remove unused imports to reduce confusion and potential side effects
**Risk**: Zero

## Phase 2: Architecture Improvements (Medium Priority)

### 2.1 Consolidate "Block Incomplete Tasks" Logic [DUPLICATION]
**Files**: `agent/core.py` vs `agent/executor.py`
**Issue**: Same business rule implemented twice with different code paths
- core.py lines 196-208: Inline string building + injection
- executor.py `make_submit_results_block()`: Different format, returns dict

**Fix**: 
1. Unify logic in `executor.make_submit_results_block()` to return proper ToolResult
2. Remove inline implementation from core.py and call the unified method
3. Ensure consistent error messaging and behavior

**Risk**: Medium - requires careful testing of both code paths
**Benefit**: Eliminates maintenance trap where changing one misses the other

### 2.2 Improve Agent Class Cohesion [ARCHITECTURE]
**File**: `agent/core.py`
**Issue**: God object pattern - Agent class handles too many responsibilities:
- Session management (delegated but also wraps)
- Task list integration 
- Tool execution coordination
- LLM API calls (_chat method)
- Sub-agent spawning logic

**Fix**: Extract into focused classes:
1. Create `AgentExecutor` to handle tool dispatch and result formatting
2. Move `_chat()` logic to a dedicated `LLMClient` class (or keep in executor if simple enough)
3. Reduce Agent class to pure orchestration - delegate more responsibilities

**Risk**: High - requires careful refactoring of dependencies
**Benefit**: Much easier to test, maintain, and extend individual components

### 2.3 Standardize Error Handling Patterns [CONSISTENCY]
**Files**: All tool implementations in `tools/` directory
**Issue**: Inconsistent error handling:
- Some tools return `(success=False, result="error message")` tuples
- Others use `ToolResult(theme="error", ...)` 
- Mix of exception types and formats

**Fix**: Establish single pattern using ToolResult consistently:
```python
def my_tool(...):
    try:
        # implementation
        return ToolResult(llm_text=..., display_text=..., theme="success")
    except Exception as e:
        return make_error_result(str(e), title="Tool Error")  # From utils.py
```

**Risk**: Medium - requires updating all tool implementations
**Benefit**: Consistent behavior, easier to test, better developer experience

### 2.4 Extract Display Logic from Business Logic [SEPARATION]
**File**: `terminal_io/display.py`
**Issue**: Rich rendering mixed with business logic (e.g., token speed formatting inline)

**Fix**: 
1. Keep display functions pure - accept structured data, return formatted strings/panels
2. Move formatting logic to dedicated helper functions in `terminal_io/speed.py`
3. Ensure no tool-specific knowledge leaks into generic display functions

**Risk**: Low - mostly reorganization
**Benefit**: Cleaner separation, easier to swap rendering libraries later

### 2.5 Improve Constants Usage [MAINTAINABILITY]
**Files**: Multiple files using magic strings/constants
**Issue**: 
- Inconsistent use of constants vs string literals
- Some constants defined but unused (e.g., in agent/types.py)

**Fix**: 
1. Audit all magic strings and create named constants where appropriate
2. Remove unused constant definitions
3. Ensure constants are consistently referenced throughout codebase

**Risk**: Low - straightforward cleanup
**Benefit**: Easier to maintain, better documentation of intent

## Phase 3: Test Coverage Enhancement (Medium Priority)

### 3.1 Identify and Fix Missing Tests [TEST COVERAGE]
**Current gaps identified**:
- `agent/discovery.py` - No tests for YAML discovery logic
- `commands/__init__.py` - Command handlers not tested
- `terminal_io/` modules - Display functions have no unit tests
- Integration scenarios (sub-agent spawning, session loading)

### 3.2 Add Unit Tests for Critical Path [QUALITY]
**Priority test targets**:
1. Tool execution flow (execute_bash, edit_file, write_file)
2. Session serialization/deserialization
3. Task list state machine transitions
4. Command handler routing and validation

### 3.3 Fix Existing Test Failures [BUG FIXES]
**Known issues to investigate**:
- Check if any existing tests fail due to the bugs identified in Phase 1
- Ensure all test mocks align with actual implementation signatures

## Phase 4: Code Quality Polish (Low Priority)

### 4.1 Improve Type Hints and Documentation [QUALITY]
- Add missing type annotations where helpful
- Improve docstrings for public APIs
- Remove outdated comments referencing old behavior

### 4.2 Optimize Performance Hotspots [PERFORMANCE]
- Profile if any functions are called frequently (e.g., display functions in tight loops)
- Consider caching for expensive operations like YAML parsing

### 4.3 Security Review [SECURITY]
- Audit all file path handling for traversal vulnerabilities
- Verify subprocess execution has proper sanitization
- Check for hardcoded credentials or sensitive data

## Implementation Strategy

### Execution Order
1. **Phase 1 first** - Fixes bugs and removes dead code that could break tests
2. **Phase 3 second** - Ensure tests pass before major refactoring 
3. **Phase 2 third** - Major architectural changes with safety net of passing tests
4. **Phase 4 last** - Polish work once everything is stable

### Risk Mitigation
- Each phase should be independently testable
- Use git branches for each phase to allow easy rollback
- Run full test suite after each phase completion
- Consider feature flags for risky changes if needed

### Success Criteria
- All existing tests pass
- No new warnings or errors introduced
- Code coverage maintained or improved
- Static analysis (pylint, mypy) shows improvement
- Performance benchmarks unchanged or better

## Estimated Timeline
- Phase 1: 2-3 hours (mostly straightforward fixes)
- Phase 2: 4-6 hours (requires careful refactoring and testing)
- Phase 3: 3-4 hours (writing comprehensive tests)
- Phase 4: 2-3 hours (polish work)

**Total estimated effort**: 11-16 hours

## Conclusion
This systematic approach addresses critical bugs first, then improves architecture with safety nets in place. The refactoring will make the codebase more maintainable, testable, and robust while preserving all existing functionality. The key insight is that Phase 2 changes (especially consolidating duplicate logic) are most valuable but also riskiest - hence they come after fixing bugs and adding tests as a safety net.
