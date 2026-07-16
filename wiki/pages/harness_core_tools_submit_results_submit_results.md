---
name: "harness_core.tools.submit_results.submit_results"
description: "Signal task completion and return structured findings to the parent agent."
source: "harness_core/tools/submit_results.py"
---

Signal task completion and return structured findings to the parent agent.

Args:
    json_payload: A single, valid JSON object (stringified — as passed by
                  function-calling parser).  The object must
                  conform to the schema documented in this module docstring.

Returns:
    On success: a :class:`ToolResult` containing the parsed payload for display and
                downstream consumption.
    On failure: an error ToolResult describing why parsing failed.

## Signature
```python
submit_results(json_payload: str) -> ToolResult
```

## References
- [Module: harness_core.tools.submit_results](harness_core_tools_submit_results) - Parent module
