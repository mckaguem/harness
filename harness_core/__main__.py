"""Entry point — wires up configuration and starts the agent loop.

The harness can run in two modes:

* **Interactive** (default) — launches the Textual TUI. The TUI is required;
  if it fails to start, the application exits with an error.
* **Non-interactive** — when ``--message "<prompt>"`` (short ``-m``) is
  supplied, the harness loads configuration, discovers skills/agents, builds
  the main :class:`~agent.core.Agent`, runs that single prompt to completion
  via :meth:`Agent.handle_prompt`, prints the result, and exits cleanly. No
  TUI is launched.
"""

import getopt
import sys
import logging
from pathlib import Path

# Configure the logging system — only if no handler is already set up, so that
# any caller-supplied logging configuration is preserved when embedded as a
# library. The log file lives in the current working directory (project ethos:
# everything runs inside CWD).
if not logging.root.handlers:
    logging.basicConfig(
        filename=Path.cwd() / ".sessions" / "harness.log",  # The file where logs will be saved
        filemode='a',            # 'a' to append to the file, 'w' to overwrite it each run
        format='%(asctime)s - %(levelname)s - %(message)s', # The format of the log message
        level=logging.DEBUG,        # The minimum severity level to capture
    )

from harness_core.agent import Agent
from harness_core.tools import AGENT_TOOLS
from harness_core.skills.discovery import discover_skills
from harness_core.config import load_harness_config

import asyncio



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
    # Phase 6: Create the main Agent by name.
    # Agent.from_agent_name resolves "main" via the discovery path and handles
    # all initialization internally:
    #   - Loads the agent type (model, system_prompt, tools config)
    #   - Discovers skills & agents to inject into the system prompt
    #   - Resolves provider configuration
    #   - Gets context_length from harness_core.model/provider config
    # It raises FileNotFoundError if the named agent cannot be found.
    # ------------------------------------------------------------------
    try:
        # Start a fresh run folder so this app launch (and every subagent it
        # spawns) is organised under a single date-time directory in .sessions/.
        from harness_core.session.session_utils import create_run_folder
        create_run_folder()

        agent = Agent.from_agent_name("main", tool_schemas=AGENT_TOOLS)
        agent._id = "Agent.main"
    except Exception as exc:
        logging.exception(exc)
        sys.stderr.write(f"\n[harness] FATAL: Failed to create main agent: {exc}\n")
        sys.exit(1)

    return agent

async def blarg(argv=None):
    agent = build_agent()

    from harness_core.runtime.manager import Manager
    manager = Manager(agent)
    await manager.run()

def main(argv=None):
    asyncio.run(blarg())



if __name__ == "__main__":
    main()

