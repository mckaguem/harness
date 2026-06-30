"""run_subagent — spawn a sub-agent, run a task, return the result.

Creates a fresh :class:`Agent` from ``agents/<sub_agent>.yaml``, runs
``handle_prompt(task)`` synchronously on it, captures the final response text,
and returns it as a string to the calling agent.

Each call spawns an isolated sub-agent — no shared history with prior calls or
the parent's conversation.  The sub-agent has access to all tools unless its
YAML constrains ``agent_tools``.
"""


def run_subagent(sub_agent: str, task: str) -> str:
    """Spawn a named sub-agent and execute *task* on it.

    Args:
        sub_agent: Name of the agent definition in ``agents/<sub_agent>.yaml``
                   (e.g. ``"analyst"``, ``"coder"``, ``"sysadmin"``).
        task: The task description to run — treated as a user prompt for the
              sub-agent's :meth:`Agent.handle_prompt` loop.

    Returns:
        The final response text produced by the sub-agent (the last
        ``RESPONSE`` yield from its ``handle_prompt`` generator), or an error
        message if spawning or running failed.
    """
    try:
        from agent import Agent, RESPONSE

        # No explicit parent needed — spawn_subagent falls back to the current
        # contextvar bound by handle_prompt().
        sub = Agent.spawn_subagent(sub_agent)  # type: ignore[call-arg]
        result_text = ""
        for kind, *args in sub.handle_prompt(task):
            if kind == RESPONSE:
                result_text = args[0]

        return result_text if result_text.strip() else "(sub-agent produced no output)"

    except FileNotFoundError as exc:
        return f"Error: {exc}"
    except Exception as exc:
        return f"Error running sub-agent '{sub_agent}': {exc}"


function_def = {
    "type": "function",
    "function": {
        "name": "run_subagent",
        "description": (
            "Spawn a specialized sub-agent, run a task on it to completion, "
            "and return the result text.  Sub-agents are defined in agents/*.yaml "
            "(e.g. analyst, coder, sysadmin, writer).  Each call creates an "
            "isolated agent with no shared history."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sub_agent": {
                    "type": "string",
                    "description": (
                        "Name of the sub-agent YAML in agents/ "
                        "(e.g. 'analyst', 'coder', 'sysadmin', 'writer')."
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
