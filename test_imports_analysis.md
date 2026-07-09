# Test Files Import Analysis

## Summary
Analysis of all Python test files in `/workspaces/harness/tests/` directory to identify imports that may need updating due to refactoring.

## Files Analyzed
Total: 18 test files

## Import Issues Found

### 1. **HIGH PRIORITY - Needs Immediate Update**
- **File**: `tests/test_terminal_io.py`
- **Line**: 10
- **Current Import**: `from model.utils import get_context_length`
- **Issue**: This import currently references the new module structure. Wait, let me check if this is actually correct or not. Looking at the grep results earlier, there was a reference to `model_utils` import that needs updating.
  
Let me re-examine: In the grep results, I saw `from model_utils import get_context_length` in the refactoring report, but in the actual file it shows `from model.utils import get_context_length`. This suggests the import may have already been updated.

### 2. **POTENTIAL ISSUES - Verify Correctness**

#### Agent-related imports
Files using `from agent import ...`:
- `test_agent.py` (multiple instances)
- These appear to be correct since `agent/__init__.py` re-exports the necessary symbols.

#### Tools-related imports
Files using tool imports:
- `test_tools.py`: `from tools import AGENT_TOOLS`
- `test_tools.py`: `from tools.execute_bash import execute_bash`, `from tools.write_file import write_file`, `from tools.read_file import read_file`
- `test_edit_file.py`: `from tools.edit_file import edit_file`
- `test_grep.py`: `from tools.grep import grep`
- `test_dispatcher.py`: `from tools.dispatcher import dispatch`
- `test_tools.py`: `from tools.utils import is_safe_path`
- `test_tools.py`: `from tools.tool_result import ToolResult`

**Analysis**: These appear correct based on the current module structure.

#### Skills-related imports
Files using skills imports:
- `test_skills.py`: `from skills.discovery import discover_skills`, `from skills.discovery import format_skill_catalog`, `from skills.discovery import parse_skill_metadata`
- `test_skills.py`: `from tools.activate_skill import activate_skill`

**Analysis**: These appear correct.

#### Other module imports
- `test_discovery.py`: `from agent.discovery import ...` ✓
- `test_commands.py`: `from commands import ...` ✓
- `test_context_compression.py`: `from session.context_compression import ...` ✓
- `test_terminal_display.py`: `from terminal_io.display import ...` ✓
- `test_terminal_io.py`: `from terminal_io import format_speed` ✓
- `test_executor.py`: `from agent.executor import ToolExecutor` ✓
- `test_run_subagent.py`: `from tools.run_subagent import ...` ✓
- `test_task_context_bug.py`: `from tools.update_task_status import update_task_status` ✓
- `test_task_context_bug.py`: `from agent.task_list import TaskList, NextTaskInfo` ✓
- `test_task_list.py`: `from agent.task_list import Task, VALID_STATUSES, TaskList` ✓
- `test_harness.py`: `from agent.loop import user_loop` ✓
- `test_harness.py`: `from tools.tool_result import ToolResult` ✓
- `test_tasks_command.py`: `from commands.tasks import cmd_tasks` ✓
- `test_tasks_command.py`: `from agent.task_list import TaskList` ✓

## Search for Old Module Names

### Searched for:
1. `model_utils` - Found in documentation/files but **not** in actual test imports
2. `skills_discovery` - Found as `from skills.discovery` which is correct
3. `tools` - Used correctly as `from tools import` or `from tools.module import`
4. `agent` - Used correctly as `from agent import`

### Key Finding:
The main issue appears to be in `test_terminal_io.py` line 10. Let me verify if this is actually a problem by checking if `model/utils.py` exists:

<｜DSML｜function_calls>
<｜DSML｜invoke name="execute_bash">
<｜DSML｜parameter name="command" string="true">ls -la /workspaces/harness/model/