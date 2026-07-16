---
name: "harness_core.tools.submit_results.summary"
description: "Return a one-line summary of the submit_results call."
source: "harness_core/tools/submit_results.py"
---

Return a one-line summary of the submit_results call.

Args:
    json_payload: Same JSON payload string passed to submit_results().

Returns:
    One-line summary: "submit_results: <summary_of_actions>" or
    "submit_results: <invalid json>" if parsing fails.

## Signature
```python
summary(json_payload: str) -> str
```

## References
- [Module: harness_core.tools.submit_results](harness_core_tools_submit_results) - Parent module
