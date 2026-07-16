---
name: "harness_core.agent.loop._emit_tool_error_event"
description: "Emit an 'agent.tool.error' event for tool-call errors."
source: "harness_core/agent/loop.py"
---

Emit an 'agent.tool.error' event for tool-call errors.

Handles both high-level agent turn failures and handle_prompt ERROR outputs.
The TUI listener handles display + panel reset on receipt.

## Signature
```python
_emit_tool_error_event(agent, description: str) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
