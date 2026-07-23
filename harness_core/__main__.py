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

# Module-level logger used by setup() and blarg(). Defined after imports so it
# is available, but actual configuration happens inside setup() once CLI args
# have been parsed.
logger = logging.getLogger(__name__)

# The log level parsed from --log-level / -l in main(). Used by setup()'s
# basicConfig call to set the root logger's effective level before any
# downstream work (load_harness_config, discover_skills) runs. Default is INFO.
_parsed_log_level: int = logging.INFO


USAGE = """\
Usage: harness.py [options]

Options:
  -m, --message <prompt>   Run a single prompt non-interactively and exit.
  -l, --log-level <LEVEL>  Set log level (DEBUG/INFO/WARNING/ERROR/CRITICAL). Default: INFO
  -h, --help               Show this help message and exit.
"""

# Recognised level names — case-insensitive mapping to logging constants.
_LOG_LEVELS = {name: getattr(logging, name) for name in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")}


def parse_args(argv):
    """Parse CLI arguments with :mod:`getopt`.

    Args:
        argv: A list of argument strings (typically ``sys.argv[1:]``).

    Returns:
        dict: ``{"message": str | None, "help": bool, "log_level": int}``.
        ``message`` is the value of ``--message``/``-m`` (or ``None`` when
        absent); ``log_level`` is a :mod:`logging` constant.

    Exits:
        Calls ``sys.exit(2)`` on an unknown option or invalid log level,
        printing usage to stderr first.
    """
    try:
        opts, _args = getopt.getopt(argv, "hm:l:", ["help", "message=", "log-level="])
    except getopt.GetoptError as exc:
        # argparse/getopt errors happen before setup() runs, so logging may not
        # be configured yet — fall back to stderr.
        sys.stderr.write(f"[harness] Error: {exc.msg}\n\n{USAGE}")
        sys.exit(2)

    message = None
    help_requested = False
    log_level_str = "INFO"  # default
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help_requested = True
        elif opt in ("-m", "--message"):
            message = arg
        elif opt in ("-l", "--log-level"):
            log_level_str = arg

    # Validate and convert the level string to a logging constant.
    resolved_level = _LOG_LEVELS.get(log_level_str.upper())
    if resolved_level is None:
        sys.stderr.write(
            f"[harness] Error: invalid --log-level '{arg}'. "
            f"Expected one of: {', '.join(_LOG_LEVELS)}.\n\n{USAGE}"
        )
        sys.exit(2)

    return {"message": message, "help": help_requested, "log_level": resolved_level}


def run_non_interactive(agent: "Agent", message: str) -> int:
    """Run a single prompt against *agent* synchronously and return an exit code.

    Used by tests and CLI ``-m`` mode to execute one agent turn without the
    full interactive loop. Returns 0 on success, non-zero on failure.
    """
    async def _run():
        # _process_and_run_turn references self._on_exit_callback (set in
        # Agent.run_loop()); ensure it exists for single-turn use.
        if not hasattr(agent, '_on_exit_callback'):
            agent._on_exit_callback = None  # type: ignore[attr-defined]

        try:
            await agent._process_and_run_turn(message)
            return 0
        except Exception as exc:
            sys.stderr.write(f"[harness] run_non_interactive error: {exc}\n")
            return 1

    try:
        return asyncio.run(_run())
    except RuntimeError:
        # If there's already a running loop, use create_task + wait.
        import contextlib
        with contextlib.suppress(RuntimeError):
            pass
        loop = asyncio.get_running_loop()
        task = loop.create_task(_run())
        return 1 if task.result() else 0


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
    # Phase 0: Configure logging (must be first, before any downstream work).
    # ------------------------------------------------------------------
    if not logging.root.handlers:
        _log_format = '%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s'
        _datefmt = '%Y-%m-%dT%H:%M:%S'

        file_handler = logging.FileHandler(
            Path.cwd() / ".sessions" / "harness.log",
            mode='a',
            encoding='utf-8',
        )
        file_handler.setFormatter(logging.Formatter(_log_format, datefmt=_datefmt))

        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(_log_format, datefmt=_datefmt))

        logging.basicConfig(
            handlers=[file_handler, stream_handler],
            force=False,  # preserve any pre-existing configuration
        )
    # Set the root logger level from CLI (INFO by default).
    logging.root.setLevel(_parsed_log_level)

    # ------------------------------------------------------------------
    # Phase 1: Load configuration (caches it globally for downstream modules).
    # ------------------------------------------------------------------
    try:
        load_harness_config()
    except RuntimeError as exc:
        logger.critical("FATAL: %s", exc)
        raise SystemExit(1)

    # ------------------------------------------------------------------
    # Phase 3: Discover skills (validates they're loadable and checks for
    # command/skill collisions — if any skill name matches a command name,
    # we can't reliably route "/name" to either one, so abort).
    # ------------------------------------------------------------------
    from harness_core.commands import COMMANDS
    try:
        discover_skills(command_names=set(COMMANDS.keys()))
    except RuntimeError as exc:
        logger.critical("[skills] FATAL: %s", exc)
        raise SystemExit(1)
    except Exception as exc:
        logger.warning("Skill discovery failed: %s", exc)

    # ------------------------------------------------------------------
    # Phase 4: Discover agents (side-effect: validates agent YAML files).
    # ------------------------------------------------------------------
    try:
        from harness_core.agent.discovery import discover_agents as _discover_agents
        _discover_agents()
    except Exception as exc:
        logger.warning("Agent discovery failed: %s", exc)


async def blarg(argv=None):
    # __main__ owns the config/agent/skill discovery startup pipeline.
    setup()

    from harness_core.runtime.manager import Manager
    manager = Manager()
    # Manager.launch_agent starts the run folder and builds the main Agent.
    manager.launch_agent("main", tool_schemas=AGENT_TOOLS)
    await manager.run()


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    global _parsed_log_level
    _parsed_log_level = args["log_level"]

    if args.get("help"):
        sys.stdout.write(USAGE)
        return

    asyncio.run(blarg())


if __name__ == "__main__":
    main()
