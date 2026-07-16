---
name: "harness_core.commands.new.cmd_new"
description: "Create a new session in the current agent."
source: "harness_core/commands/new.py"
---

Create a new session in the current agent.

Resets both the task list and conversation history, keeping only the system prompt.
A new session file is generated with a fresh timestamped filename.

Usage:
    /new                 - create a brand-new session (resets everything)

Args:
    rest: Unused (kept for consistency with other command handlers).
    agent: The current Agent instance.

Returns:
    False to continue the loop after resetting.

## Signature
```python
cmd_new(rest: str, agent) -> bool | None
```

## References
- [Module: harness_core.commands.new](harness_core_commands_new) - Parent module
