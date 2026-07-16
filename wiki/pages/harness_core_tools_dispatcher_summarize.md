---
name: "harness_core.tools.dispatcher.summarize"
description: "Return a summary string for the tool *func_name* with keyword *args*."
source: "harness_core/tools/dispatcher.py"
---

Return a summary string for the tool *func_name* with keyword *args*.

Looks up the tool's summary function in SUMMARY_REGISTRY and calls it
with **args. If the summary function isn't registered or raises an
exception, falls back to "{func_name}: (summary unavailable)".

## Signature
```python
summarize(func_name: str, args: dict) -> str
```

## References
- [Module: harness_core.tools.dispatcher](harness_core_tools_dispatcher) - Parent module
