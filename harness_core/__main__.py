"""Entry point — wires up configuration and starts the agent loop.

The harness can run in two modes:

* **Interactive** (default) — launches the Textual TUI, falling back to the
  classic Rich/prompt_toolkit REPL. This is the historical behaviour.
* **Non-interactive** — when ``--message "<prompt>"`` (short ``-m``) is
  supplied, the harness loads configuration, discovers skills/agents, builds
  the main :class:`~agent.core.Agent`, runs that single prompt to completion
  via :meth:`Agent.handle_prompt`, prints the result, and exits cleanly. No
  TUI or REPL is launched.
"""

import getopt
import sys
import time

from harness_core.agent import Agent
from harness_core.tools import AGENT_TOOLS
from harness_core.skills.discovery import discover_skills
from harness_core.config import load_harness_config


USAGE = """\
Usage: harness.py [options]

Options:
  -m, --message <prompt>   Run a single prompt non-interactively and exit.
  -h, --help               Show this help message and exit.
"""


def parse_args(argv):
    """Parse CLI arguments with :mod:`getopt`.

    Args:
        argv: A list of argument strings (typically ``sys.argv[1:]``).

    Returns:
        dict: ``{"message": str | None, "help": bool}``. ``message`` is the
        value of ``--message``/``-m`` (or ``None`` when the flag is absent).

    Exits:
        Calls ``sys.exit(2)`` on an unknown option or a missing required
        argument, printing usage to stderr first.
    """
    try:
        opts, _args = getopt.getopt(argv, "hm:", ["help", "message="])
    except getopt.GetoptError as exc:
        sys.stderr.write(f"[harness] Error: {exc.msg}\n\n{USAGE}")
        sys.exit(2)

    message = None
    help_requested = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help_requested = True
        elif opt in ("-m", "--message"):
            message = arg
    return {"message": message, "help": help_requested}


def build_agent():
    """Load config, discover skills/agents, and build the main Agent.

    This is the shared "startup pipeline" used by both the interactive and
    non-interactive code paths (formerly the inline phases 1, 3, 4, 5 and 6 of
    ``main``). It returns a fully configured :class:`~agent.core.Agent`.

    Exits:
        Calls ``sys.exit(1)`` on a fatal configuration/startup error.
    """
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
    from harness_core.commands import COMMANDS
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
        from harness_core.agent.discovery import discover_agents as _discover_agents
        _discover_agents()
    except Exception as exc:
        sys.stderr.write(f"\n[harness] WARNING: Agent discovery failed: {exc}\n")

    # ------------------------------------------------------------------
    # Phase 5: Resolve the main agent YAML path.
    # ------------------------------------------------------------------
    from harness_core.config import resolve_config_path
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
    #   - Gets context_length from harness_core.model/provider config
    # ------------------------------------------------------------------
    try:
        # Start a fresh run folder so this app launch (and every subagent it
        # spawns) is organised under a single date-time directory in .sessions/.
        from harness_core.session.session_utils import create_run_folder
        create_run_folder()

        agent = Agent.from_file(str(main_agent_path), tool_schemas=AGENT_TOOLS)
        agent._id = "Agent.main"
    except Exception as exc:
        sys.stderr.write(f"\n[harness] FATAL: Failed to create main agent: {exc}\n")
        sys.exit(1)

    return agent


def run_non_interactive(agent, message):
    """Run a single *message* to completion and exit cleanly.

    This drives the same engine as the interactive loop
    (:meth:`Agent.handle_prompt`) but without any TUI/REPL. It mirrors the
    slash-command and skill-interception handling of ``user_loop`` for a single
    prompt, then iterates the generator yielded by ``handle_prompt`` and renders
    each event with the shared ``terminal_io`` display helpers.

    Args:
        agent: A configured :class:`~agent.core.Agent`.
        message: The user prompt to run.

    Returns:
        int: ``0`` on success (intended to be passed to ``sys.exit``).
    """
    # Bind this agent as the current agent for the duration of the run.  Tools
    # such as the task list and run_subagent are agent-aware via the
    # CURRENT_AGENT ContextVar; without this binding they would see None and
    # fail.  (See agent/loop.py for the full rationale.)
    from harness_core.agent.context import CURRENT_AGENT
    CURRENT_AGENT.set(agent)

    from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
    from harness_core.commands import COMMANDS
    from harness_core.skills.interceptor import intercept_message, InterceptorKind
    from harness_core.terminal_io import (
        display_tool_call,
        display_tool_result,
        display_error,
        display_agent_response,
        display_user_message,
        display_turn_stats,
    )
    from rich.console import Console

    _console = Console()

    # --- Slash-command / skill interception (single prompt) ----------------
    effective_input = message
    if message.startswith('/'):
        parts = message[1:].split(' ', 1)
        command_name = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ''

        handler = COMMANDS.get(command_name)
        if handler:
            result = handler(rest, agent=agent)
            # /exit or /quit request termination; other built-in commands are
            # handled directly and need no LLM call.
            return 0 if result is True else 0

        # No built-in handler — run the skill-activation interceptor.
        outcome = intercept_message(message)
        if outcome.kind == InterceptorKind.ACTIVATED:
            agent.inject_text(outcome.payload)
            effective_input = outcome.stripped_message if outcome.stripped_message else message
        elif outcome.kind == InterceptorKind.RESTRICTED:
            display_error(outcome.payload)
            effective_input = outcome.stripped_message if outcome.stripped_message else message
        else:
            effective_input = message

    # Echo the prompt for visibility (no TUI to render the typed text).
    if effective_input.strip():
        display_user_message(effective_input)

    # --- Drive the agent engine to completion ------------------------------
    turn_start = time.time()
    for output in agent.handle_prompt(effective_input):
        kind = output[0]
        if kind == RESPONSE:
            _, content, ollama_response, _ = output
            elapsed = time.time() - turn_start
            reasoning = (
                (ollama_response or {}).get("reasoning")
                if isinstance(ollama_response, dict) else None
            )
            display_agent_response(content, ollama_response, agent._context_length, reasoning=reasoning)
            display_turn_stats(ollama_response, agent._context_length, elapsed_seconds=elapsed)
        elif kind == TOOL_CALL:
            _, func_name, args_str, response_data = output
            pre_content = (response_data or {}).get("pre_tool_content", "") or ""
            reasoning = (response_data or {}).get("reasoning", "") or ""
            display_tool_call(func_name, args_str, pre_content=pre_content, reasoning=reasoning)
        elif kind == TOOL_RESULT:
            _, func_name, result, response_data = output
            display_tool_result(func_name, result)
        elif kind == ERROR:
            _, description, _, _ = output
            display_error(description)

    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    if args["help"]:
        sys.stdout.write(USAGE)
        sys.exit(0)

    message = args["message"]

    # ------------------------------------------------------------------
    # Phase 2 (shared): Build the configured Agent.  Both code paths below
    # use this same pipeline.
    # ------------------------------------------------------------------
    agent = build_agent()

    # ------------------------------------------------------------------
    # Non-interactive mode: run the single prompt and exit.
    # ------------------------------------------------------------------
    if message is not None:
        sys.exit(run_non_interactive(agent, message))

    # ------------------------------------------------------------------
    # Phase 7: Interactive mode (historical default).
    # The textual TUI owns the screen and drives the classic user_loop on a
    # worker thread; if the TUI cannot run for any reason it falls back to the
    # classic Rich/prompt_toolkit REPL.
    # ------------------------------------------------------------------
    from harness_core.terminal_io.tui import launch
    try:
        launch(agent)
    except Exception as exc:  # pragma: no cover - defensive fallback path
        sys.stderr.write(
            f"\n[harness] WARNING: TUI failed to start ({exc}); using classic REPL.\n"
        )
        from harness_core.agent.loop import user_loop
        user_loop(agent)


if __name__ == "__main__":
    main()
