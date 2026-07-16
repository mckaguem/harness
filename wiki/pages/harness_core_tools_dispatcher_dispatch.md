---
name: "harness_core.tools.dispatcher.dispatch"
description: "Call the tool implementation matching *func_name* with keyword *args*."
source: "harness_core/tools/dispatcher.py"
---

Call the tool implementation matching *func_name* with keyword *args*.

Tools that need the calling agent declare a ``ctx`` parameter; the dispatcher
builds a :class:`~agent.tool_context.ToolContext` from the currently active
agent (``CURRENT_AGENT``) and passes it automatically. Callers may also pass
their own ``ctx`` via *args* to override the active agent. Because the
context is injected based on the tool's own signature, tools that don't need
it (e.g. ``submit_results``) keep their original signatures untouched — no
special case required.

Returns whatever the underlying tool function returns — typically a
:class:`ToolResult`. Raises ``KeyError`` if *func_name* isn't registered;
callers should treat that as "unknown tool".

## Signature
```python
dispatch(func_name: str, args: dict) -> ToolResult | tuple
```

## References
- [Module: harness_core.tools.dispatcher](harness_core_tools_dispatcher) - Parent module
