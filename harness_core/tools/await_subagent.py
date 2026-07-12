"""await_subagent — block until a background sub-agent job completes.

The ``run_subagent(block=False)`` tool launches a sub-agent in the background
(via the shared :class:`~harness_core.tools.subagent_manager.SubagentManager`)
and returns a short identifier like ``"subagent-1"``. This tool waits for that
job to finish and returns its :class:`~harness_core.tools.tool_result.ToolResult`.

If ``identifier`` is omitted, it blocks until the *first* currently-running
background sub-agent completes and returns that result.
"""

from typing import Optional

from harness_core.tools.subagent_manager import manager
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.utils import make_error_result


function_def = {
    "type": "function",
    "function": {
        "name": "await_subagent",
        "description": (
            "Wait for a background sub-agent job (launched via "
            "run_subagent with block=false) to finish and return its result. "
            "Provide the identifier returned by run_subagent (e.g. 'subagent-1'). "
            "If no identifier is given, wait for the first currently-running "
            "background sub-agent to complete and return its result."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": (
                        "Optional identifier of the background sub-agent to await "
                        "(e.g. 'subagent-1'). If omitted, awaits the first "
                        "completed running sub-agent."
                    ),
                },
            },
            "required": [],
        },
    },
}


def await_subagent(identifier: Optional[str] = None) -> ToolResult:
    """Block until a background sub-agent completes and return its result."""
    try:
        return manager.await_one(identifier)
    except RuntimeError as exc:
        return make_error_result(str(exc), title="Await Subagent")
