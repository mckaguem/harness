---
name: "harness_core.commands.compress.compress_handler"
description: "Handle the /compress command — trigger manual session compression."
source: "harness_core/commands/compress.py"
---

Handle the /compress command — trigger manual session compression.

Args:
    rest: Optional fraction parameter as string (e.g., "0.2")
    agent: The Agent instance containing a session
    
Returns:
    False to continue the loop

## Signature
```python
compress_handler(rest: str, agent)
```

## References
- [Module: harness_core.commands.compress](harness_core_commands_compress) - Parent module
