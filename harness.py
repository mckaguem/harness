"""Entry point — wires up configuration and starts the agent loop."""

import sys
from agent import Agent, user_loop
from tools import AGENT_TOOLS
from skills.discovery import discover_skills
from config import load_harness_config


def main():
    # ------------------------------------------------------------------
    # Phase 1: Load configuration (caches it globally for downstream modules).
    # ------------------------------------------------------------------
    try:
        load_harness_config()
    except RuntimeError as exc:
        sys.stderr.write(f"\n[harness] FATAL: {exc}\n")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Phase 3: Discover skills (validates they're loadable and checks for
    # command/skill collisions — if any skill name matches a command name,
    # we can't reliably route "/name" to either one, so abort).
    # ------------------------------------------------------------------
    from commands import COMMANDS
    try:
        discover_skills(command_names=set(COMMANDS.keys()))
    except RuntimeError as exc:
        sys.stderr.write(f"\n[skills] FATAL: {exc}\n")
        sys.exit(1)
    except Exception as exc:
        sys.stderr.write(f"\n[harness] WARNING: Skill discovery failed: {exc}\n")

    # ------------------------------------------------------------------
    # Phase 4: Discover agents (side-effect: validates agent YAML files).
    # ------------------------------------------------------------------
    try:
        from agent.discovery import discover_agents as _discover_agents
        _discover_agents()
    except Exception as exc:
        sys.stderr.write(f"\n[harness] WARNING: Agent discovery failed: {exc}\n")

    # ------------------------------------------------------------------
    # Phase 5: Resolve the main agent YAML path.
    # ------------------------------------------------------------------
    from config import resolve_config_path
    main_agent_path = resolve_config_path("agents/main.yaml")
    if main_agent_path is None:
        sys.stderr.write(
            "\n[harness] FATAL: Could not find 'agents/main.yaml' in project or global config dirs. Aborting startup.\n"
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # Phase 6: Create the main Agent from its YAML definition.
    # Agent.from_file handles all initialization internally:
    #   - Loads agent type (model, system_prompt, tools config)
    #   - Discovers skills & agents to inject into system prompt
    #   - Resolves provider configuration
    #   - Gets context_length from model/provider config
    # ------------------------------------------------------------------
    try:
        agent = Agent.from_file(str(main_agent_path), tool_schemas=AGENT_TOOLS)
    except Exception as exc:
        sys.stderr.write(f"\n[harness] FATAL: Failed to create main agent: {exc}\n")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Phase 7: Run the interactive user loop with the configured Agent.
    # The textual TUI owns the screen and drives the classic user_loop on a
    # worker thread; if the TUI cannot run for any reason it falls back to the
    # classic Rich/prompt_toolkit REPL.
    # ------------------------------------------------------------------
    from terminal_io.tui import launch
    try:
        launch(agent)
    except Exception as exc:  # pragma: no cover - defensive fallback path
        sys.stderr.write(
            f"\n[harness] WARNING: TUI failed to start ({exc}); using classic REPL.\n"
        )
        from agent.loop import user_loop
        user_loop(agent)


if __name__ == "__main__":
    main()
