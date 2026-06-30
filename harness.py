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
from agent import Agent, AgentType, user_loop
from tools import AGENT_TOOLS


def main():
    ollama_host = os.environ.get(
        "OLLAMA_HOST",
        os.environ.get("OPENAI_BASE_URL", "http://localhost:11435"),
    )
    # strip trailing /v1 if the user passed an OpenAI-format URL — Ollama client needs bare base
    if ollama_host.rstrip("/").endswith("/v1"):
        ollama_host = ollama_host[: -len("/v1")]

    ollama_client = ollama.Client(host=ollama_host)
    context_length = 2**17

    # Build the agent definition from YAML.
    agent_type = AgentType.from_file("agents/main.yaml")
    
    agent = Agent(
        agent_type=agent_type,
        ollama_client=ollama_client,
        context_length=context_length,
        tool_schemas=AGENT_TOOLS,  # pass all schemas so filter_tool_schemas can work
    )

    user_loop(agent, ollama_client)


if __name__ == "__main__":
    main()
