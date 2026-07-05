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
from skills_discovery import discover_skills, format_skill_catalog
from agent.discovery import discover_agents


def check_command_skill_collision() -> list[str]:
    """Check for name collisions between built-in commands and discovered skills.

    Returns:
        A list of human-readable collision messages (empty if there are none).
    """
    # Get all built-in command names
    command_names = set(COMMANDS.keys())
    
    # Discover all valid skills
    discovered_skills = discover_skills()
    skill_names = {name for name, _ in discovered_skills}
    
    # Find intersection - names that exist in both sets
    collisions = command_names & skill_names
    
    # Generate collision messages
    messages: list[str] = []
    for name in sorted(collisions):
        messages.append(
            f"Command '/{name}' and skill '{name}' both exist. "
            f"Cannot reliably route — aborting startup."
        )
    return messages


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

    # ------------------------------------------------------------------
    # Discover and load the main agent from config paths.
    # The "main" agent YAML is looked up in both project and global agents/
    # directories (project takes precedence).
    # ------------------------------------------------------------------
    discovered_agents = discover_agents()
    
    if not discovered_agents:
        sys.stderr.write("\n[agents] FATAL: No agents found in config paths. Aborting startup.\n")
        sys.exit(1)

    # Look for the "main" agent specifically
    main_agent_path = None
    for name, path in discovered_agents:
        if name == "main":
            main_agent_path = path
            break

    if main_agent_path is None:
        sys.stderr.write("\n[agents] FATAL: No 'main' agent found in config paths. Aborting startup.\n")
        available_names = ", ".join(name for name, _ in discovered_agents)
        sys.stderr.write(f"Available agents: {available_names}\n")
        sys.exit(1)

    # Build the agent definition from YAML.
    agent_type = AgentType.from_file(main_agent_path)
    
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
