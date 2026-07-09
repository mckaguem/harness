# Harness Project Refactoring Plan

## Current State Assessment

Based on analysis of `/workspaces/harness` project structure:

### Existing Modules
1. **agent** - Already exists (`/workspaces/harness/agent/`) with 12 files
2. **session** - Already exists (`/workspaces/harness/session/`) with 4 files
3. **tools** - Already exists (`/workspaces/harness/tools/`) with 17 files
4. **commands** - Already exists (`/workspaces/harness/commands/`) with 3 files
5. **skills** - Exists as skill definitions in `.harness_py/skills/` but not as Python module
6. **model** - Exists as `model_utils.py` but not as proper module
7. **provider** - Doesn't exist yet, needs to be created

### Key Issues Identified
1. **Duplicate sessions module**: `sessions/` directory duplicates `session/` module
2. **Deprecated files**: `agent/session.py` and `agent/session_utils.py` are deprecated duplicates
3. **Skills not modularized**: Skills exist as YAML/config files but not as Python module
4. **Model utilities**: `model_utils.py` is standalone, should be a module
5. **No provider abstraction**: No unified provider interface for OpenAI/Ollama/etc.
6. **High coupling**: `tools/tool_result.py` has 20 dependents
7. **Inconsistent naming**: Mixed use of singular vs plural (`session` vs `sessions`)

## Target Architecture

```
/workspaces/harness/
├── harness.py                    # Main entry point
├── config.py                     # Configuration
├── model/                        # NEW: Model abstractions
│   ├── __init__.py
│   ├── utils.py                  # model_utils.py moved here
│   ├── provider.py               # NEW: Provider abstraction
│   └── types.py                  # Model-related types
├── agent/                        # Agent framework (existing)
│   ├── core.py                   # Main Agent class
│   ├── discovery.py              # Agent YAML discovery
│   ├── executor.py               # Tool execution
│   ├── loop.py                   # Interactive REPL
│   ├── task_list.py              # Task management
│   ├── types.py                  # AgentType dataclass
│   └── utils.py                  # Agent utilities
├── session/                      # Session management (existing)
│   ├── session.py               # Session class
│   ├── session_utils.py         # Session utilities
│   └── context_compression.py    # Context compression
├── skills/                       # NEW: Skills module
│   ├── __init__.py
│   ├── discovery.py             # skills_discovery.py moved here
│   ├── interceptor.py           # skills_interceptor.py moved here
│   └── base.py                  # Base skill class/interface
├── tools/                       # Tools implementation (existing)
│   ├── __init__.py              # Dynamic tool discovery
│   ├── tool_result.py           # ToolResult dataclass
│   ├── utils.py                 # Tool utilities
│   ├── dispatcher.py            # Tool dispatcher
│   └── *.py                     # Individual tool implementations
├── commands/                     # Slash commands (existing)
│   ├── __init__.py              # Command registry
│   ├── sub.py                   # /sub command
│   └── tasks.py                 # /tasks command
├── terminal_io/                  # Terminal UI (existing)
│   ├── display.py
│   ├── prompt.py
│   └── speed.py
├── tests/                        # Test suite (existing)
└── .harness_py/                  # Configuration directory
    ├── agents/                   # Agent YAML definitions
    └── skills/                   # Skill definitions
```

## Phase 1: Clean Up Duplicates & Deprecated Code

### Task 1.1: Remove duplicate sessions directory
- Delete `/workspaces/harness/sessions/` directory entirely
- Verify no imports reference `sessions.*`

### Task 1.2: Remove deprecated agent session files
- Delete `agent/session.py` (duplicate of `session/session.py`)
- Delete `agent/session_utils.py` (duplicate of `session/session_utils.py`)
- Update any remaining imports

### Task 1.3: Fix multiple submit_results definitions
- Consolidate multiple `submit_results` function definitions in `tools/__init__.py`
- Ensure only one clean implementation remains

## Phase 2: Create Missing Modules

### Task 2.1: Create model module
- Create `model/` directory with `__init__.py`
- Move `model_utils.py` to `model/utils.py`
- Create `model/provider.py` with provider abstraction
- Create `model/types.py` for model-related types

### Task 2.2: Create skills module
- Create `skills/` directory with `__init__.py`
- Move `skills_discovery.py` to `skills/discovery.py`
- Move `skills_interceptor.py` to `skills/interceptor.py`
- Create `skills/base.py` for skill base class

### Task 2.3: Create provider abstraction in model module
- Design provider interface in `model/provider.py`
- Support OpenAI, Ollama, and extensible to other providers
- Move provider-specific logic from various files into this module

## Phase 3: Refactor Dependencies

### Task 3.1: Reduce coupling of tools/tool_result.py
- Consider moving `ToolResult` to shared location (maybe `agent/tool_result.py`)
- Or keep in tools but improve dependency management

### Task 3.2: Update imports across codebase
- Update all imports to use new module structure
- Fix relative imports and module paths

### Task 3.3: Standardize naming conventions
- Ensure consistent use of singular/plural (session not sessions)
- Consistent naming patterns across modules

## Phase 4: Update Tests

### Task 4.1: Update test imports
- Update all test files to import from new module locations
- Fix broken imports in test suite

### Task 4.2: Add missing tests
- Add tests for new modules (model, skills)
- Ensure provider abstraction is properly tested

### Task 4.3: Verify test suite passes
- Run full test suite after refactoring
- Fix any test failures

## Phase 5: Implementation Details

### Model Module Design
```python
# model/provider.py
class Provider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict], model: str) -> Dict:
        pass
    
    @abstractmethod
    def get_context_length(self, model: str) -> int:
        pass
    
    @abstractmethod
    def tokenize(self, text: str, model: str) -> List[int]:
        pass

class OpenAIProvider(Provider):
    """OpenAI provider implementation."""

class OllamaProvider(Provider):
    """Ollama provider implementation."""

# model/utils.py - Keep existing utilities
# model/types.py - ModelConfig, ProviderConfig, etc.
```

### Skills Module Design
```python
# skills/base.py
class Skill:
    """Base class for skills."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def activate(self) -> Dict:
        """Activate skill and return instructions."""
        pass

# skills/discovery.py - Formerly skills_discovery.py
# skills/interceptor.py - Formerly skills_interceptor.py
```

### Import Updates Example
```python
# BEFORE:
from skills_discovery import discover_skills
from model_utils import get_context_length

# AFTER:
from skills.discovery import discover_skills
from model.utils import get_context_length
from model.provider import OpenAIProvider
```

## Phase 6: Migration Strategy

### Step 1: Backup current state
- Create backup of current project structure
- Document current working state

### Step 2: Implement incrementally
- Start with Phase 1 (cleanup) - lowest risk
- Then Phase 2 (new modules) - medium risk
- Finally Phase 3 (dependency updates) - highest risk

### Step 3: Test after each phase
- Run tests after each major change
- Verify basic functionality works

### Step 4: Update documentation
- Update AGENTS.md, skills_spec.md, TODO.md
- Update docstrings and inline documentation

## Phase 7: Validation Checklist

### Functional Requirements
- [ ] Main entry point (`harness.py`) works
- [ ] Interactive REPL (`agent/loop.py`) works
- [ ] Slash commands work
- [ ] Tool execution works
- [ ] Sub-agent spawning works
- [ ] Session save/load works
- [ ] Context compression works
- [ ] Skill activation works

### Code Quality Requirements
- [ ] No duplicate code exists
- [ ] All imports use new module structure
- [ ] No circular dependencies
- [ ] Tests pass (100% of existing tests)
- [ ] Type hints maintained/improved
- [ ] Docstrings updated

### Architectural Requirements
- [ ] Model module exists with provider abstraction
- [ ] Skills module exists as proper Python module
- [ ] Provider interface supports multiple backends
- [ ] Clear separation of concerns
- [ ] Consistent naming conventions

## Risk Mitigation

### High Risk Areas
1. **Dependency updates**: Many files import from moved modules
   - Mitigation: Update imports systematically, test incrementally
2. **Provider abstraction**: Changes to how models are called
   - Mitigation: Implement backwards-compatible interface initially
3. **Tool discovery**: Dynamic tool registration may break
   - Mitigation: Keep `tools/__init__.py` discovery mechanism unchanged

### Fallback Plan
- If refactoring causes critical issues, revert to backup
- Phase implementation allows for rollback at each stage
- Critical paths (tool execution, agent loop) tested first

## Timeline Estimate

1. **Phase 1 (Cleanup)**: 1-2 hours
2. **Phase 2 (New modules)**: 2-3 hours  
3. **Phase 3 (Dependencies)**: 3-4 hours
4. **Phase 4 (Tests)**: 1-2 hours
5. **Phase 5-7 (Validation)**: 1-2 hours

**Total Estimated Time**: 8-13 hours

## Success Criteria

The refactoring will be considered successful when:
1. All tests pass with the new module structure
2. All existing functionality works without regression
3. Code is organized into the 7 target modules (agent, session, skills, tools, commands, model, provider)
4. Duplicate code is eliminated
5. Provider abstraction supports at least OpenAI and Ollama
6. Documentation reflects new structure

## Notes & Considerations

1. **Backwards compatibility**: Some changes may break existing configurations
   - Solution: Update configuration loading to handle new paths
2. **External dependencies**: Tools like `run_subagent` inject `submit_results`
   - Solution: Ensure tool injection still works with new structure
3. **Dynamic nature**: Some modules use runtime discovery (`tools/__init__.py`)
   - Solution: Keep dynamic discovery pattern but update import paths