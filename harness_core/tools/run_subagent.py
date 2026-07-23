"""run_subagent — spawn a sub-agent, run a task, return the result.

Creates a fresh :class:`Agent` from ``agents/<sub_agent>.yaml``, runs
``handle_prompt(task)`` asynchronously on it (via async generator), and returns
structured findings back to the calling (parent) agent.

Each call spawns an isolated sub-agent — no shared history with prior calls or
the parent's conversation.  The sub-agent has access to all tools unless its
YAML constrains ``agent_tools``, plus a runtime-injected ``submit_results`` tool
that it must invoke exactly once when done.
"""

import json


from harness_core.tools.tool_result import ToolResult
from harness_core.tools.utils import _strip_ansi, make_error_result


TERMINATION_PROMPT = """\
You are a specialized sub-agent execution thread. Your purpose is to execute the user's task with absolute technical precision using your permitted tools.

## Termination Protocol (CRITICAL)
When you have completed your assigned task, you must NOT write a final conversational response. You must explicitly invoke the `submit_results` tool to return your findings.

* Ensure that all data requested by the `submit_results` schema (such as file paths, line numbers, and verbatim snippets) is exhaustively populated.
* Do not wrap the tool arguments in markdown backticks (like ```json) or add conversational text outside of the tool call."""


function_def = {
    "type": "function",
    "function": {
        "name": "run_subagent",
        "description": (
            "Spawn a specialized sub-agent, run a task on it to completion, "
            "and return the result text. Each call creates an isolated agent with no shared history."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sub_agent": {
                    "type": "string",
                    "description": (
                        "Name of the sub-agent."
                    ),
                },
                "task": {
                    "type": "string",
                    "description": "The task description — what to have the sub-agent do.",
                },
            },
            "required": ["sub_agent", "task"],
        },
    },
}


async def run_subagent(sub_agent: str, task: str) -> ToolResult:
    """Spawn a named sub-agent and execute *task* on it.

    Args:
        sub_agent: Name of the sub-agent YAML (without extension).
        task: The task description to run.
    """
    from harness_core.agent import Agent, RESPONSE, TOOL_CALL  # noqa: F401 (explicit guards)
    from harness_core.tools.dispatcher import dispatch

    termination_prompt = TERMINATION_PROMPT

    sub = Agent.from_agent_name(
        sub_agent,
        extra_tools=[_get_submit_results_def()],
    )

    # Append termination protocol to sub-agent's existing system prompt.
    sub._agent_type.inject_extra_system_prompt(termination_prompt)

    try:
        result_text = ""
        async for kind, *args in sub.handle_prompt(task):
            if kind == TOOL_CALL and args[0] == "submit_results":
                func_name = args[0]
                try:
                    args_data = json.loads(args[1])
                except Exception as exc:
                    description = (
                        f"Error parsing submit_results arguments ({exc}). "
                        "The sub-agent produced malformed JSON."
                    )
                    return make_error_result(description)

                result = await dispatch(func_name, args_data, sub)
                return ToolResult(
                    llm_text=_strip_ansi(str(result)),
                    display_text=_strip_ansi(str(result)),
                    type_tag="json",
                    title="ℹ️ Run Sub-Agent",
                    theme="info",
                )

            elif kind == RESPONSE:
                result_text = args[0]

        return ToolResult(
            llm_text=_strip_ansi(result_text if result_text.strip() else "(sub-agent produced no output)"),
            display_text=_strip_ansi(result_text if result_text.strip() else "(sub-agent produced no output)"),
            type_tag="text",
            title="ℹ️ Run Sub-Agent",
            theme="info",
        )

    except FileNotFoundError as exc:
        return make_error_result(f"Error: {exc}")
    except Exception as exc:
        return make_error_result(f"Error running sub-agent '{sub_agent}': {exc}")

def summary(sub_agent: str, task: str) -> str:
    """Return a one-line summary of the run_subagent call."""
    return f"run_subagent: {sub_agent} ({task[:50]}...)" if len(task) > 50 else f"run_subagent: {sub_agent} ({task})"


def _get_submit_results_def() -> dict:
    """Lazily import and return the ``submit_results`` function_def dict."""
    from harness_core.tools.submit_results import function_def

    # Return a copy to avoid mutating the original module-level definition
    return dict(function_def)
