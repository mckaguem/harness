---
name: "harness_core.session.context_compression._parse_tool_arguments"
description: "Return the arguments dict from ``function.arguments`` regardless of form."
source: "harness_core/session/context_compression.py"
---

Return the arguments dict from ``function.arguments`` regardless of form.

The LLM may pass arguments either as:
  - a parsed Python dict, or
  - a JSON-encoded string (which must be deserialized).

Returns None if *arguments* is not usable.

## Signature
```python
_parse_tool_arguments(arguments)
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
