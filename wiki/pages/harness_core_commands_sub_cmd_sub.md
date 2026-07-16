---
name: "harness_core.commands.sub.cmd_sub"
description: "Spawn an interactive conversation with a sub-agent."
source: "harness_core/commands/sub.py"
---

Spawn an interactive conversation with a sub-agent.

Loads the named sub-agent via :meth:`Agent.spawn_subagent`, prints a status
banner, then drives the interactive loop using :func:`user_loop`.  On exit
the conversation is summarised and injected into the parent so it continues
with that context.

Args:
    rest: The sub-agent name (e.g. ``"analyst"`` from ``/sub analyst``).
    parent_agent: The calling agent whose message history receives the summary.

Returns:
    False to continue the parent loop after returning from the sub-agent,
    or True if an error occurs and we want to break (currently never).

## Signature
```python
cmd_sub(rest: str, parent_agent) -> bool | None
```

## References
- [Module: harness_core.commands.sub](harness_core_commands_sub) - Parent module
