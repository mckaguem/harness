"""Entry point — owns config/agent/skill discovery and delegates to Manager.

This module is responsible for the shared "startup pipeline" that precedes any
run: loading harness configuration and discovering skills and agents. It then
delegates agent creation and execution to :class:`~harness_core.runtime.manager.Manager`,
which owns the agent loop and the Textual TUI.

The harness runs interactively by default: ``blarg`` sets up config/discovery,
asks the Manager to launch the main agent (which starts the run folder), and
runs the agent loop + TUI concurrently.
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


def setup():
    """Load config, discover skills, and discover agents (startup pipeline).

    This is the shared "startup pipeline" __main__ owns: it loads harness
    configuration and discovers skills/agents (validating they're loadable).
    It does NOT create a run folder or build an Agent — that is delegated to
    :meth:`Manager.launch_agent`.

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


async def blarg(argv=None):
    # __main__ owns the config/agent/skill discovery startup pipeline.
    setup()

    from harness_core.runtime.manager import Manager
    manager = Manager()
    # Manager.launch_agent starts the run folder and builds the main Agent.
    manager.launch_agent("main", tool_schemas=AGENT_TOOLS)
    await manager.run()

def main(argv=None):
    asyncio.run(blarg())



if __name__ == "__main__":
    main()

