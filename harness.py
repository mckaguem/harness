"""Entry point — wires up configuration and starts the agent loop."""

import sys
from pathlib import Path

from terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_error,
    display_agent_response,
)
from commands import COMMANDS
from agent import Agent, AgentType, user_loop
from tools import AGENT_TOOLS
from skills.discovery import discover_skills, format_skill_catalog
from config import resolve_config_path


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
    # Resolve the absolute path to agents/main.yaml (project dir preferred over global).
    # ------------------------------------------------------------------
    main_agent_path = resolve_config_path("agents/main.yaml")
    if main_agent_path is None:
        sys.stderr.write(
            "\n[harness] FATAL: Could not find 'agents/main.yaml' in project or global config dirs. Aborting startup.\n"
        )
        sys.exit(1)

    # Build the agent definition from YAML (this also resolves provider_config).
    agent_type = AgentType.from_file(str(main_agent_path))

    if not agent_type.provider_config:
        sys.stderr.write(
            "\n[harness] FATAL: No provider configuration found for agent 'main'. Aborting startup.\n"
        )
        sys.exit(1)

    # Create a Provider from the resolved ProviderConfig.
    from model.provider import Provider
    provider = Provider.from_config(agent_type.provider_config)

    # Phase 2: Discover skills and inject their catalog into the system prompt.
    discovered_skills = discover_skills()
    if discovered_skills:
        visible_skills = [
            (name, meta) for name, meta in discovered_skills
            if not meta.get("disable-model-invocation", False)
        ]
        if visible_skills:
            catalog = format_skill_catalog(visible_skills)
            agent_type.inject_extra_system_prompt(catalog)

    # ------------------------------------------------------------------
    # Build context_length from the provider (try to detect, fall back to default).
    # ------------------------------------------------------------------
    try:
        context_length = provider.get_context_length(agent_type.model_name) or 2**17
    except Exception:
        context_length = 2**17

    agent = Agent(
        agent_type=agent_type,
        provider=provider,
        context_length=context_length,
        tool_schemas=AGENT_TOOLS,  # pass all schemas so filter_tool_schemas can work
    )

    user_loop(agent)


if __name__ == "__main__":
    main()
