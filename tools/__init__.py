"""Tools subpackage — one module per tool, plus a dispatcher and shared utils."""

from tools.dispatcher import dispatch
from tools.utils import is_safe_path


def _build_agent_tools() -> list:
    """Assemble the AGENT_TOOLS schema from each submodule's function_def."""
    from tools import execute_bash as _eb
    from tools import write_file as _wf
    from tools import read_file as _rf
    from tools import edit_file as _ef
    from tools import grep as _g
    return [
        _eb.function_def,
        _wf.function_def,
        _rf.function_def,
        _ef.function_def,
        _g.function_def,
    ]


AGENT_TOOLS = _build_agent_tools()


# Re-export individual tool functions for direct use (tests, etc.) and backward compat.
from tools.execute_bash import execute_bash as execute_bash_fn
from tools.write_file import write_file as write_file_fn
from tools.read_file import read_file as read_file_fn
from tools.edit_file import edit_file as edit_file_fn
from tools.grep import grep as grep_fn

# Also expose them without the `_fn` suffix so callers can do `tools.execute_bash(...)`.
execute_bash = execute_bash_fn
write_file = write_file_fn
read_file = read_file_fn
edit_file = edit_file_fn
grep = grep_fn
