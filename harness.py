"""Entry point — wires up configuration and starts the agent loop."""

import os
from pathlib import Path
import ollama

from terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_error,
    display_agent_response,
)
from commands import COMMANDS
from agent import Agent, AgentType
from tools import AGENT_TOOLS


def build_system_prompt(base_prompt_path: str = "system_prompt.txt") -> str:
    """Read the base system prompt file and inject a listing of the current directory.

    Args:
        base_prompt_path: Path to the base system prompt text file. Defaults to 
                          ``system_prompt.txt`` in the project root so the default 
                          harness behavior is unchanged.

    If an ``AGENTS.md`` file exists in the working directory its contents are
    appended so the agent can follow any project-specific conventions.
    """
    prompt_path = Path(base_prompt_path)
    base = prompt_path.read_text(encoding="utf-8")

    # List files/dirs in the current working directory
    cwd_contents = "\n".join(
        entry.name for entry in sorted(Path.cwd().iterdir())
    )
    injection = (
        f"\n\nCurrent working directory contents:\n{cwd_contents}"
    )

    # Incorporate AGENTS.md if it exists.
    agents_md = Path.cwd() / "AGENTS.md"
    if agents_md.is_file():
        try:
            agents_content = agents_md.read_text(encoding="utf-8").strip()
            if agents_content:
                injection += (
                    f"\n\n--- AGENTS.md ---\n{agents_content}\n--- end AGENTS.md ---"
                )
        except Exception:
            pass

    return base + injection


def run_loop(agent: Agent, ollama_client: "ollama.Client", on_exit=None) -> None:
    """Run the interactive chat loop.

    Args:
        agent: An initialized :class:`Agent` instance with its configuration.
        ollama_client: The Ollama client (kept for future use).
        on_exit: Optional callback invoked just before the loop breaks due to 
                 ``/exit`` or ``/quit``. Receives ``(agent, messages)``. Return
                 value is ignored — the callback can mutate whatever it needs.
    """
    print_system(
        f"🚀 Agent Ready — {agent._agent_type.name} ({agent._agent_type.model_name})",
        "Type a message to begin. Type /exit or /quit to stop."
    )

    while True:
        user_input = prompt_user()

        # Check for slash commands first.
        if user_input.startswith('/'):
            parts = user_input[1:].split(' ', 1)
            command_name = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ''

            handler = COMMANDS.get(command_name)
            if handler:
                result = handler(rest, agent=agent)
                if result is True and on_exit is not None:
                    # Let caller do its own exit-time work (e.g. summarize)
                    on_exit(agent, agent.messages)
                    break
                elif result is True:
                    break
                continue

        for output in agent.handle_prompt(user_input):
            kind = output[0]
            if kind == "response":
                _, content, ollama_response = output
                display_agent_response(content, ollama_response, agent._context_length, None)
            elif kind == "tool_call":
                _, func_name, args_str = output
                display_tool_call(func_name, args_str)
            elif kind == "tool_result":
                _, func_name, result = output
                display_tool_result(func_name, result)
            else:  # ERROR
                _, description = output
                display_error(description)


def main():
    MODEL_NAME = 'hf.co/deepreinforce-ai/Ornith-1.0-35B-GGUF:Q6_K'

    ollama_host = os.environ.get(
        "OLLAMA_HOST",
        os.environ.get("OPENAI_BASE_URL", "http://localhost:11435"),
    )
    # strip trailing /v1 if the user passed an OpenAI-format URL — Ollama client needs bare base
    if ollama_host.rstrip("/").endswith("/v1"):
        ollama_host = ollama_host[: -len("/v1")]

    ollama_client = ollama.Client(host=ollama_host)
    context_length = 2**17

    # Build the agent definition. We construct it programmatically here; an 
    # alternative would be to load from YAML via AgentType.from_file().
    system_prompt = build_system_prompt()
    
    agent_type = AgentType(
        name="main",
        model_name=MODEL_NAME,
        system_prompt_path="system_prompt.txt",
        system_prompt=system_prompt,
        agent_tools=["*"],  # use all available tools
    )
    
    agent = Agent(
        agent_type=agent_type,
        ollama_client=ollama_client,
        context_length=context_length,
        tool_schemas=AGENT_TOOLS,  # pass all schemas so filter_tool_schemas can work
    )

    run_loop(agent, ollama_client)


if __name__ == "__main__":
    main()
