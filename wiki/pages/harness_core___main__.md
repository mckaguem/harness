---
name: "harness_core.__main__"
description: "Entry point — wires up configuration and starts the agent loop."
source: "harness_core/__main__.py"
---

Entry point — wires up configuration and starts the agent loop.

The harness can run in two modes:

* **Interactive** (default) — launches the Textual TUI, falling back to the
  classic Rich/prompt_toolkit REPL. This is the historical behaviour.
* **Non-interactive** — when ``--message "<prompt>"`` (short ``-m``) is
  supplied, the harness loads configuration, discovers skills/agents, builds
  the main :class:`~agent.core.Agent`, runs that single prompt to completion
  via :meth:`Agent.handle_prompt`, prints the result, and exits cleanly. No
  TUI or REPL is launched.

## References
- [parse_args](harness_core___main___parse_args) - Parse CLI arguments with :mod:`getopt`
- [build_agent](harness_core___main___build_agent) - Load config, discover skills/agents, and build the main Agent
- [run_non_interactive](harness_core___main___run_non_interactive) - Run a single *message* to completion and exit cleanly
- [main](harness_core___main___main) - Function
- [USAGE](harness_core___main___USAGE) - Constant
- [Module Index](../index/harness_core.md) - Parent module index
