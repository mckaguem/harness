---
name: "harness_core.tools.dispatcher.dispatch"
description: "Call the tool implementation matching *func_name* with keyword *args*."
source: "harness_core/tools/dispatcher.py"
---

Call the tool implementation matching *func_name* with keyword *args*.

Tools that need access to the calling agent declare an ``agent`` parameter;
the dispatcher detects this automatically via signature introspection and
passes the :class:`~agent.core.Agent` instance as a keyword argument. Tools
that don't need it (e.g. ``submit_results``) keep their original signatures
untouched — no special case required.

Returns whatever the underlying tool function returns — typically a
:class:`ToolResult`. Raises ``KeyError`` if *func_name* isn't registered;
callers should treat that as "unknown tool".

## Signature
```python
dispatch(func_name: str, args: dict) -> ToolResult | tuple
```

## References
- [Module: harness_core.tools.dispatcher](harness_core_tools_dispatcher) - Parent module
