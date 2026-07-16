---
name: "harness_core.__main__.run_non_interactive"
description: "Run a single *message* to completion and exit cleanly."
source: "harness_core/__main__.py"
---

Run a single *message* to completion and exit cleanly.

This drives the same engine as the interactive loop
(:meth:`Agent.handle_prompt`) but without any TUI/REPL. It mirrors the
slash-command and skill-interception handling of ``user_loop`` for a single
prompt, then iterates the generator yielded by ``handle_prompt`` and renders
each event with the shared ``terminal_io`` display helpers.

Args:
    agent: A configured :class:`~agent.core.Agent`.
    message: The user prompt to run.

Returns:
    int: ``0`` on success (intended to be passed to ``sys.exit``).

## Signature
```python
run_non_interactive(agent, message)
```

## References
- [Module: harness_core.__main__](harness_core___main__) - Parent module
