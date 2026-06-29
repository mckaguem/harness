"""Handler for the /sub command — spawn a sub-agent conversation."""

from pathlib import Path
import ollama

from terminal_io.display import print_system, display_error
from agent import Agent, AgentType
from tools import AGENT_TOOLS


def cmd_sub(rest: str, parent_agent) -> bool | None:
    """Spawn an interactive conversation with a sub-agent.

    Args:
        rest: The sub-agent name (e.g. ``"analyst"`` from ``/sub analyst``).
        parent_agent: The calling agent whose message history receives the summary.

    Returns:
        False to continue the parent loop after returning from the sub-agent.
    """
    sub_name = rest.strip()
    if not sub_name:
        print_system("Error", "Usage: /sub <agent-name>  (e.g. /sub analyst)")
        return False

    yaml_path = Path("agents") / f"{sub_name}.yaml"
    try:
        agent_type = AgentType.from_file(str(yaml_path))
    except FileNotFoundError as exc:
        print_system(
            "Error",
            f"No agent definition found at {yaml_path}\nRun 'ls agents/' to see available agents."
        )
        return False

    # Build the system prompt using harness's helper so sub-agents get the same
    # cwd listing and AGENTS.md injection as the main agent.
    from harness import build_system_prompt, run_loop
    system_prompt = build_system_prompt(agent_type.system_prompt_path)
    agent_type.system_prompt = system_prompt  # override with augmented prompt

    print_system(
        f"🤖 Sub-agent '{sub_name}' loaded — {agent_type.model_name}",
        "Type a message to begin. Type /exit or /quit to return."
    )

    # Create the sub-agent using Agent.handle_prompt() for proper tool dispatch.
    client = ollama.Client(host=parent_agent._ollama_host)
    context_length = parent_agent._context_length
    sub_agent = Agent(
        agent_type=agent_type,
        ollama_client=client,
        context_length=context_length,
        tool_schemas=AGENT_TOOLS,  # let filter_tool_schemas pick the right ones
    )

    def _on_exit(agent, messages):
        """Summarize the sub-agent conversation and inject it into the parent.

        Rather than mutating ``parent_agent.messages`` directly, we hand the
        summary off to ``parent_agent.inject_text()`` so that the injected text
        is queued and will be prepended to the next user prompt with a clear
        delimiter so the parent agent can tell it apart from genuine input.
        """
        print_system(
            f"📝 Summarizing '{sub_name}' conversation...",
            "Ask the sub-agent to produce a final summary."
        )
        try:
            summary = agent.summarize()
            print_system("Summary", summary)
            if not summary:
                raise ValueError("summarize() returned empty content")
            parent_agent.inject_text(
                f"[Conversation with '{sub_name}' ended.\n"
                f"**Summary:**\n{summary}\n---]"
            )
        except Exception as exc:
            print_system("Error", f"Failed to summarize sub-agent conversation: {exc}")

    # Run the interactive loop — reuses harness.run_loop for display & prompt handling.
    run_loop(sub_agent, client, on_exit=_on_exit)

    return False


