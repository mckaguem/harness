---
name: "harness_core.agent.loop._emit_tool_call_event"
description: "Emit an 'agent.tool.call' event for in-progress tool calls."
source: "harness_core/agent/loop.py"
---

Emit an 'agent.tool.call' event for in-progress tool calls.

## Signature
```python
_emit_tool_call_event(agent, func_name: str, args_str: str, summary: str | None, pre_content: str, reasoning: str | None) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
