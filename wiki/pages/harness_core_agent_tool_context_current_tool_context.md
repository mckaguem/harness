---
name: "harness_core.agent.tool_context.current_tool_context"
description: "Build a :class:`ToolContext` for the agent currently bound to CURRENT_AGENT."
source: "harness_core/agent/tool_context.py"
---

Build a :class:`ToolContext` for the agent currently bound to CURRENT_AGENT.

Returns a context whose ``agent`` is ``None`` when no agent is active, so
callers can detect and reject headless usage explicitly rather than sharing
a hidden fallback agent.

## Signature
```python
current_tool_context() -> 'ToolContext'
```

## References
- [Module: harness_core.agent.tool_context](harness_core_agent_tool_context) - Parent module
