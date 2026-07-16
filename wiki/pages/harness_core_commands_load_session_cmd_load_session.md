---
name: "harness_core.commands.load_session.cmd_load_session"
description: "Load a session from a YAML file in .sessions/."
source: "harness_core/commands/load_session.py"
---

Load a session from a YAML file in .sessions/.

Usage:
    /load <filename>         - load a specific session file (with or without .yaml)
    /load                    - list available sessions and prompt for selection

Args:
    rest: Optional filename to load directly.
    agent: The current Agent instance (will be replaced with loaded one).

Returns:
    False to continue the loop (session is loaded into current agent).

## Signature
```python
cmd_load_session(rest: str, agent) -> bool | None
```

## References
- [Module: harness_core.commands.load_session](harness_core_commands_load_session) - Parent module
