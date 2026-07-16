---
name: "harness_core.commands.save_session.cmd_save_session"
description: "Save the current session to a YAML file in .sessions/."
source: "harness_core/commands/save_session.py"
---

Save the current session to a YAML file in .sessions/.

Usage:
    /save                    - auto-generated filename with timestamp + agent type
    /save my_custom_name     - uses 'my_custom_name.yaml' as filename

Args:
    rest: Optional custom filename (without extension).
    agent: The current Agent instance.

Returns:
    False to continue the loop after saving.

## Signature
```python
cmd_save_session(rest: str, agent) -> bool | None
```

## References
- [Module: harness_core.commands.save_session](harness_core_commands_save_session) - Parent module
