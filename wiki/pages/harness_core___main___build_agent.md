---
name: "harness_core.__main__.build_agent"
description: "Load config, discover skills/agents, and build the main Agent."
source: "harness_core/__main__.py"
---

Load config, discover skills/agents, and build the main Agent.

This is the shared "startup pipeline" used by both the interactive and
non-interactive code paths (formerly the inline phases 1, 3, 4, 5 and 6 of
``main``). It returns a fully configured :class:`~agent.core.Agent`.

Exits:
    Calls ``sys.exit(1)`` on a fatal configuration/startup error.

## Signature
```python
build_agent()
```

## References
- [Module: harness_core.__main__](harness_core___main__) - Parent module
