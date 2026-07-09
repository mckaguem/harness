# Project Structure Analysis - Harness

## Project Overview
**Path:** `/workspaces/harness`
**Description:** A Python-based agent framework with tool discovery, sub-agent spawning, and session management.

## 1. Directory Structure & Module Organization

### Core Modules
```
/workspaces/harness/
├── agent/                    # Core agent implementation (12 files)
│   ├── __init__.py          # Package exports
│   ├── constants.py         # Constants
│   ├── context.py           # Context variable management
│   ├── core.py              # Main Agent class
│   ├── discovery.py         # Agent YAML discovery
│   ├── executor.py         # Tool execution
│   ├── loop.py              # Interactive user loop
│   ├── session.py           # Agent session (deprecated?)
│   ├── session_utils.py     # Session utilities (deprecated?)
│   ├── task_list.py         # Task management
│   ├── types.py             # AgentType dataclass
│   └── utils.py             # Utility functions
├── tools/                   # Tool implementations (17 files)
│   ├── __init__.py          # Auto-discovers skills via function_def
│   ├── activate_skill.py
│   ├── dispatcher.py
│   ├── edit_file.py
│   ├── execute_bash.py
│   ├── grep.py
│   ├── initialize_task_list.py
│   ├── read_file.py
│   ├── run_subagent.py
│   ├── submit_results.py    # Critical tool for sub-agents
│   ├── tool_result.py       # ToolResult dataclass (highly depended on)
│   ├── update_task_status.py
│   ├── utils.py
│   ├── web_fetch.py
│   ├── web_search.py
│   └── write_file.py
├── commands/                # Slash command handlers (3 files)
│   ├── __init__.py          # Main command registry
│   ├── sub.py               # /sub command
│   └── tasks.py             # /tasks command
├── session/                 # Active session module (4 files)
│   ├── __init__.py
│   ├── context_compression.py
│   ├── session.py           # Session class
│   └── session_utils.py
├── terminal_io/             # Terminal UI components (4 files)
│   ├── __init__.py
│   ├── display.py
│   ├── prompt.py
│   └── speed.py
└── tests/                  # Test suite (16 files)
    ├── test_agent.py
    ├── test_commands.py
    ├── test_context_compression.py
    ├── test_discovery.py
    ├── test_dispatcher.py
    ├── test_edit_file.py
    ├── test_executor.py
    ├── test_grep.py
    ├── test_harness.py
    ├── test_run_subagent.py
    ├── test_skills.py
    ├── test_task_context_bug.py
    ├── test_task_list.py
    ├── test_tasks_command.py
    ├── test_terminal_display.py
    ├── test_terminal_io.py
    └── test_tools.py
```

### Supporting Modules
```
├── skills_discovery.py      # Skill discovery from .harness_py/skills/
├── skills_interceptor.py    # Skill message interception
├── config.py                # Configuration paths
├── model_utils.py          # Model utilities
├── original_source.py       # Original source code utilities
├── harness.py              # MAIN ENTRY POINT
└── TODO.md                  # TODO list
```

### Duplicate/Deprecated Directories (Issues)
```
├── sessions/                # DUPLICATE: Old sessions dir (2 files)
│   ├── __init__.py
│   └── context_compression.py  # Duplicate of session/context_compression.py
└── .sessions/               # Session storage directory
```

### Configuration Directories
```
├── .harness_py/
│   ├── agents/             # Agent YAML definitions
│   └── skills/            # Skill definitions
├── sample_config/
│   └── skills/
│       └── sample-skill/
│           └── scripts/
│               └── test.py
└── harness.egg-info/       # Package metadata
```

## 2. Key Dependencies & Import Patterns

### Critical Dependencies (Most Depended-On Modules)
1. **tools/tool_result.py** (20 dependents) - `ToolResult` dataclass used throughout tools
2. **tools/utils.py** (13 dependents) - Utility functions for tool implementations
3. **agent/discovery.py** (6 dependents) - Agent YAML discovery
4. **config.py** (4 dependents) - Configuration path resolution
5. **agent/core.py** (4 dependents) - Main Agent class

### External Dependencies (36 total)
- **OpenAI/LLM**: `openai`, `ollama`
- **Web/tools**: `ddgs` (search), `urllib`, `json`
- **UI**: `rich`, `prompt_toolkit`
- **Data**: `yaml`, `dataclasses`
- **Testing**: `pytest`, `unittest.mock`
- **System**: `os`, `pathlib`, `subprocess`, `sys`

### No Circular Dependencies Found ✓

## 3. Entry Points & Execution Flow

### Primary Entry Points
1. **`harness.py`** - Main entry point
   - Configuration setup (OpenAI client, context length)
   - Command/skill collision checking
   - Agent discovery and initialization
   - Skill injection
   - Calls `user_loop()`

2. **`agent/loop.py`** - Interactive REPL loop
   - `user_loop()` function
   - Handles user input, slash commands
   - Displays agent responses, tool calls, errors
   - Integrates with `commands.COMMANDS`

3. **Slash Commands** (`commands/__init__.py`)
   - `/exit`, `/quit` - Exit program
   - `/sub <agent>` - Spawn sub-agent
   - `/tasks` - Task management
   - `/save` - Save session
   - `/load` - Load session  
   - `/new` - New session
   - `/compress` - Manual context compression

### Secondary Entry Points
- **Sub-agent spawning**: `Agent.spawn_subagent()` (via `/sub` command)
- **Tool execution**: Dynamic dispatch via `tools/dispatcher.py`

## 4. Architectural Patterns

### 1. Dynamic Tool Discovery
```
tools/__init__.py → _discover_skills()
  ↓
Scans tools/*.py for `function_def` dict
  ↓
Populates AGENT_TOOLS and DISPATCH_REGISTRY
  ↓
Tools auto-registered without manual imports
```

### 2. Agent Configuration via YAML
```
.harness_py/agents/main.yaml
  ↓
AgentType.from_file() loads YAML
  ↓
Defines: model_name, system_prompt, agent_tools
  ↓
Injected into Agent.__init__()
```

### 3. Session Management
```
Session class (session/session.py)
  ↓
Auto-saves to .sessions/ directory
  ↓
Context compression via session/context_compression.py
  ↓
Manual commands: /save, /load, /new, /compress
```

### 4. Sub-Agent System
```
Agent.spawn_subagent(sub_name, parent_agent)
  ↓
Discovers YAML from .harness_py/agents/<sub_name>.yaml
  ↓
Runtime injection of submit_results tool
  ↓
Parent agent receives structured results via submit_results
```

## 5. Issues for Refactoring

### High Priority Issues
1. **Duplicate Code**: `sessions/` vs `session/` directories
   - `sessions/context_compression.py` duplicates `session/context_compression.py`
   - `sessions/` appears unused/abandoned

2. **Multiple submit_results Definitions**
   - `tools/__init__.py` has 3 separate `submit_results` function definitions
   - Could cause runtime conflicts

3. **Deprecated Agent Session Files**
   - `agent/session.py` and `agent/session_utils.py` likely deprecated
   - Replaced by `session/session.py` and `session/session_utils.py`

### Medium Priority Issues
1. **Inconsistent Naming**
   - `agent.session` vs `agent.session_utils` (deprecated)
   - `session` package vs `sessions` directory

2. **Circular Import Risks**
   - `commands/__init__.py` imports from `session` package
   - `agent/loop.py` imports `session.context_compression`
   - Manage with late imports (`from commands.sub import cmd_sub`)

3. **Tool Dependencies**
   - `tools/tool_result.py` has 20 dependents - high coupling
   - Consider moving to more central location

### Low Priority Issues
1. **Test Coverage Gaps**
   - Missing tests for some tool implementations
   - Edge cases in context compression

2. **Configuration Path Resolution**
   - Could be simplified/reorganized
   - Environment variable handling

## 6. Refactoring Recommendations

### Phase 1: Consolidate Duplicates
1. Remove `sessions/` directory entirely
2. Update all imports from `sessions.` to `session.`
3. Consolidate multiple `submit_results` definitions

### Phase 2: Simplify Architecture
1. Move `tools/tool_result.py` to `agent/tool_result.py` (or shared location)
2. Create clear deprecation path for old agent session files  
3. Standardize naming conventions

### Phase 3: Enhance Maintainability
1. Add docstrings to all public APIs
2. Improve test coverage for edge cases
3. Add type hints to remaining untyped functions

### Phase 4: Performance/Optimization
1. Consider caching for tool discovery
2. Optimize context compression algorithm
3. Improve session serialization performance

## 7. Key Files for Understanding

1. **`harness.py`** - Main entry point, setup flow
2. **`agent/core.py`** - Core Agent class, logic flow
3. **`tools/__init__.py`** - Dynamic tool discovery mechanism
4. **`agent/loop.py`** - Interactive user loop
5. **`commands/__init__.py`** - Slash command implementations
6. **`session/session.py`** - Session management
7. **`tools/run_subagent.py`** - Sub-agent spawning pattern

## 8. Development Guidelines

### Adding New Tools
1. Create `.py` file in `tools/` with top-level `function_def` dict
2. Implement function matching `function_def["function"]["name"]`
3. Test appears automatically

### Adding New Slash Commands
1. Add handler function to `commands/__init__.py`
2. Register in `COMMANDS` dict
3. Ensure returns `True` (exit) or `False` (continue)

### Adding New Agent Types
1. Create YAML file in `.harness_py/agents/`
2. Define `model_name`, `system_prompt`, `agent_tools`
3. Can be referenced via `/sub <name>` or `Agent.spawn_subagent()`

### Adding Tests
1. Create `test_<module>.py` in `tests/`
2. Follow existing patterns using `pytest` and `unittest.mock`
3. Test both success and failure cases