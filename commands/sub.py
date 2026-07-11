"""Handler for the /sub command — spawn an interactive sub-agent conversation."""

from terminal_io.display import print_system


def cmd_sub(rest: str, parent_agent) -> bool | None:
    """Spawn an interactive conversation with a sub-agent.

    Loads the named sub-agent via :meth:`Agent.spawn_subagent`, prints a status
    banner, then drives the interactive loop using :func:`user_loop`.  On exit
    the conversation is summarised and injected into the parent so it continues
    with that context.

    Args:
        rest: The sub-agent name (e.g. ``"analyst"`` from ``/sub analyst``).
        parent_agent: The calling agent whose message history receives the summary.

    Returns:
        False to continue the parent loop after returning from the sub-agent,
        or True if an error occurs and we want to break (currently never).
    """
    sub_name = rest.strip()
    if not sub_name:
        print_system("Error", "Usage: /sub <agent-name>  (e.g. /sub analyst)")
        return False

    # Lazy imports — ``agent.loop`` pulls from this module, so top-level imports
    # of any ``agent`` symbol would trigger a circular import at runtime.
    from agent import Agent, user_loop
    from tools import AGENT_TOOLS

    try:
        sub_agent = Agent.spawn_subagent(
            sub_name, parent_agent, tool_schemas=AGENT_TOOLS
        )
    except FileNotFoundError as exc:
        print_system("Error", str(exc))
        return False

    print_system(
        f"🤖 Sub-agent '{sub_name}' loaded — {sub_agent._agent_type.model_name}",
        "Type a message to begin. Type /exit or /quit to return."
    )

    def _on_exit(agent, messages):
        """Summarize the sub-agent conversation and inject it into the parent.

        The summary is injected via :meth:`inject_text` so it is queued and
        prepended to the next user prompt with a clear delimiter.
        """
        print_system(
            f"📝 Summarizing '{sub_name}' conversation...",
            "Ask the sub-agent to produce a final summary."
        )
        try:
            summary = agent._session.summarize()
            print_system("Summary", summary)
            if not summary:
                raise ValueError("summarize() returned empty content")
            parent_agent.inject_text(
                f"[Conversation with '{sub_name}' ended.\n"
                f"**Summary:**\n{summary}\n---]"
            )
        except Exception as exc:
            print_system("Error", f"Failed to summarize sub-agent conversation: {exc}")

    # Drive the interactive loop — reuses ``user_loop`` for display & prompt handling.
    user_loop(sub_agent, sub_agent.client, on_exit=_on_exit)

    return False
