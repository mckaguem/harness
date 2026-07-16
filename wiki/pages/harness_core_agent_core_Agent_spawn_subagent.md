---
name: "harness_core.agent.core.spawn_subagent"
description: "Build and return a configured ``Agent`` for the named sub-agent."
source: "harness_core/agent/core.py"
---

Build and return a configured ``Agent`` for the named sub-agent.

Pure factory — does **not** start any conversation or display anything.
The returned agent can be driven however the caller wants (interactive
loop, single prompt via :meth:`handle_prompt`, tool-based invocation, etc.).

The sub-agent is looked up via :func:`agent.discovery.get_agent_yaml`, which
searches project and global config paths (``cwd/.harness_py/agents/`` then
``~/.harness_py/agents/``, with project taking precedence). It gets an
augmented system prompt (cwd listing + AGENTS.md) from
:meth:`AgentType._build_system_prompt` and has its tool schemas filtered by
its own ``agent_tools``. The context length is resolved by :meth:`from_file`
from the sub-agent's own model/provider configuration — it is no longer
copied from the parent agent.

Args:
    sub_name: The YAML file stem (e.g. ``"analyst"`` from ``/sub analyst``).
    tool_schemas: All available tool schemas passed through to :meth:`filter_tool_schemas`.
                  If ``None``, defaults to all tools (equivalent to ``["*"]``).
    extra_tools: Additional function_def dicts added after filtering. Useful for
                 runtime-injected tools like ``submit_results`` without modifying
                 agent YAML files.

Returns:
    A fully-constructed :class:`Agent` instance ready for prompting.

Raises:
    FileNotFoundError: If no matching agent YAML is found in any configured discovery path.

## Signature
```python
spawn_subagent(cls, sub_name: str, tool_schemas: list[Dict] | None, extra_tools: list[Dict] | None)
```

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [Class: Agent](harness_core_agent_core_Agent) - Parent class
