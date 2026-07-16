---
name: "harness_core.tools.run_subagent"
description: "run_subagent — spawn a sub-agent, run a task, return the result."
source: "harness_core/tools/run_subagent.py"
---

run_subagent — spawn a sub-agent, run a task, return the result.

Creates a fresh :class:`Agent` from ``agents/<sub_agent>.yaml``, runs
``handle_prompt(task)`` synchronously on it, and returns structured findings
back to the calling (parent) agent.

Each call spawns an isolated sub-agent — no shared history with prior calls or
the parent's conversation.  The sub-agent has access to all tools unless its
YAML constrains ``agent_tools``, plus a runtime-injected ``submit_results`` tool
that it must invoke exactly once when done.

## Flow

1. Embed the termination prompt as a module-level constant (no external file dependency).
2. Spawn the sub-agent, inject the termination text into its system_prompt via
   :meth:`AgentType.inject_extra_system_prompt`, and pass ``submit_results`` as
   an extra tool schema via :meth:`Agent.spawn_subagent`.
3. Drive the sub-agent with ``task + termination_prompt``.  When the sub-agent
   calls ``submit_results``, dispatch that call directly, capture its return
   string (the parsed JSON payload), and return it immediately to the parent —
   bypassing any further RESPONSE yields.

## Configuration Paths

Sub-agents are discovered from two config paths (see :mod:`agents_discovery`):
- **Project**: ``cwd/.harness_py/agents/``
- **Global**: ``~/.harness_py/agents/`` (overridable via ``HARNESS_PY_HOME``)

When an agent name exists in both, the project version wins.

## References
- [_get_agents_dir_paths](harness_core_tools_run_subagent__get_agents_dir_paths) - Return absolute paths to all agents/ directories from harness_core
- [_build_function_def](harness_core_tools_run_subagent__build_function_def) - Build the function definition with injected agent directory paths
- [_run_one](harness_core_tools_run_subagent__run_one) - Spawn a single named sub-agent and execute *task* on it (worker body)
- [run_subagent](harness_core_tools_run_subagent_run_subagent) - Spawn a named sub-agent and execute *task* on it
- [run_subagent_async](harness_core_tools_run_subagent_run_subagent_async) - Run a single sub-agent off the event loop, returning a :class:`ToolResult`
- [run_subagents_parallel](harness_core_tools_run_subagent_run_subagents_parallel) - Run several ``(sub_agent, task)`` pairs concurrently and return results in order
- [summary](harness_core_tools_run_subagent_summary) - Return a one-line summary of the run_subagent call
- [_get_submit_results_def](harness_core_tools_run_subagent__get_submit_results_def) - Lazily import and return the ``submit_results`` function_def dict
- [TERMINATION_PROMPT](harness_core_tools_run_subagent_TERMINATION_PROMPT) - Constant
- [Module Index](../index/harness_core_tools.md) - Parent module index
