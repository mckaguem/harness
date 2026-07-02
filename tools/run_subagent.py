"""run_subagent — spawn a sub-agent, run a task, return the result.

Creates a fresh :class:`Agent` from ``agents/<sub_agent>.yaml``, runs
``handle_prompt(task)`` synchronously on it, and returns structured findings
back to the calling (parent) agent.

Each call spawns an isolated sub-agent — no shared history with prior calls or
the parent's conversation.  The sub-agent has access to all tools unless its
YAML constrains ``agent_tools``, plus a runtime-injected ``submit_results`` tool
that it must invoke exactly once when done.

## Flow

1. Embed the termination prompt as a module-level constant (no external file dependency).
2. Spawn the sub-agent, inject the termination text into its system_prompt via
   :meth:`AgentType.inject_extra_system_prompt`, and pass ``submit_results`` as
   an extra tool schema via :meth:`Agent.spawn_subagent`.
3. Drive the sub-agent with ``task + termination_prompt``.  When the sub-agent
   calls ``submit_results``, dispatch that call directly, capture its return
   string (the parsed JSON payload), and return it immediately to the parent —
   bypassing any further RESPONSE yields.

If the sub-agent never calls ``submit_results`` (i.e. it falls back to a plain
text response), we fall through and return that response text as before.
"""

TERMINATION_PROMPT = """\
You are a specialized sub-agent execution thread. Your purpose is to execute the user's task with absolute technical precision using your permitted tools.

## Termination Protocol (CRITICAL)
When you have completed your assigned task, you must NOT write a final conversational response. You must explicitly invoke the `submit_results` tool to return your findings. 

* Ensure that all data requested by the `submit_results` schema (such as file paths, line numbers, and verbatim snippets) is exhaustively populated.
* Do not wrap the tool arguments in markdown backticks (like ```json) or add conversational text outside of the tool call."""


def run_subagent(sub_agent: str, task: str) -> tuple:
    """Spawn a named sub-agent and execute *task* on it.

    Args:
        sub_agent: Name of the agent definition in ``agents/<sub_agent>.yaml``
                   (e.g. ``"analyst"``, ``"coder"``, ``"sysadmin"``).
        task: The task description to run — treated as a user prompt for the
              sub-agent's :meth:`Agent.handle_prompt` loop.

    Returns:
        On success, one of:
        * If the sub-agent invokes :func:`submit_results <tools.submit_results>`,
          the parsed-and-echoed JSON payload (the structured findings) is
          returned to the parent agent — this is the normal/expected path.
        * Otherwise, the final ``RESPONSE`` text produced by the sub-agent.
        An error message if spawning or running failed.
    """
    import json as _json

    try:
        from agent import Agent, RESPONSE, TOOL_CALL  # noqa: F401 (explicit guards)

        termination_prompt = TERMINATION_PROMPT

        # No explicit parent needed — spawn_subagent falls back to the current
        # contextvar bound by handle_prompt().
        sub = Agent.spawn_subagent(
            sub_agent,
            extra_tools=[_get_submit_results_def()],  # inject submit_results at runtime
        )

        # Append termination protocol to sub-agent's existing system prompt.
        sub._agent_type.inject_extra_system_prompt(termination_prompt)


        result_text = ""
        for kind, *args in sub.handle_prompt(task):
            if kind == TOOL_CALL and args[0] == "submit_results":
                # Dispatch the submit_results call directly and capture its return value.
                func_name = args[0]
                try:
                    args_data = _json.loads(args[1])
                except Exception as exc:
                    description = (
                        f"Error parsing submit_results arguments ({exc}). "
                        "The sub-agent produced malformed JSON."
                    )
                    # Append this error to the sub's message log so it can self-correct,
                    # then break — we've already yielded an ERROR, which is enough signal.
                    return ("_error_", description)

                from tools.dispatcher import dispatch

                result = dispatch(func_name, args_data)
                if isinstance(result, tuple):
                    type_, content = result
                    return ("json", content)  # Always JSON for submit_results results
                return ("json", str(result))

            elif kind == RESPONSE:
                result_text = args[0]

        return (
            "text",
            result_text if result_text.strip() else "(sub-agent produced no output)",
        )

    except FileNotFoundError as exc:
        return ("_error_", f"Error: {exc}")
    except Exception as exc:
        return ("_error_", f"Error running sub-agent '{sub_agent}': {exc}")


def _get_submit_results_def():
    """Lazily import and return the ``submit_results`` function_def dict."""
    from tools.submit_results import function_def
    
    # Return a copy to avoid mutating the original module-level definition
    return dict(function_def)


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
