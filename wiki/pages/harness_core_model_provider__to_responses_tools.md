---
name: "harness_core.model.provider._to_responses_tools"
description: "Convert Chat-Completions tool schemas to the Responses API `tools` shape."
source: "harness_core/model/provider.py"
---

Convert Chat-Completions tool schemas to the Responses API `tools` shape.

Chat Completions nests the callable under `function`:
    {"type": "function", "function": {"name": ..., "parameters": ...}}
The Responses API requires a FLATTENED shape (name/parameters at the
top level), matching ``openai.types.responses.FunctionToolParam``:
    {"type": "function", "name": ..., "parameters": ..., "strict": ...}
Sending the nested Chat shape yields ``400 invalid prompt`` (the
server reports `name`/``parameters` as `received undefined`).

## Signature
```python
_to_responses_tools(tools: list[Dict] | None) -> list[Dict] | None
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
