"""Entry point — wires up configuration and starts the agent loop."""

import os
import sys
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
from skills_discovery import discover_skills, format_skill_catalog, check_command_skill_collision


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

    # ------------------------------------------------------------------
    # Pre-flight: check for command/skill name collisions.
    # If a built-in slash command and a skill share the same name, we can't
    # reliably route "/name" to either one — abort before anything else loads.
    # ------------------------------------------------------------------
    collisions = check_command_skill_collision()
    if collisions:
        sys.stderr.write(
            "\n[skills] FATAL: Command/skill collision detected. Aborting startup.\n"
        )
        for msg in collisions:
            sys.stderr.write(f"  - {msg}\n")
        sys.exit(1)

    # Build the agent definition from YAML.
    agent_type = AgentType.from_file("agents/main.yaml")
    
    # Phase 1: Discover skills and inject their catalog into the system prompt.
    discovered = discover_skills()
    if discovered:
        # Filter out skills marked disable-model-invocation: true
        visible_skills = [
            (name, meta) for name, meta in discovered
            if not meta.get("disable-model-invocation", False)
        ]
        if visible_skills:
            catalog = format_skill_catalog(visible_skills)
            agent_type.inject_extra_system_prompt(catalog)
    
    agent = Agent(
        agent_type=agent_type,
        ollama_client=ollama_client,
        context_length=context_length,
        tool_schemas=AGENT_TOOLS,  # pass all schemas so filter_tool_schemas can work
    )

    user_loop(agent, ollama_client)


if __name__ == "__main__":
    main()
