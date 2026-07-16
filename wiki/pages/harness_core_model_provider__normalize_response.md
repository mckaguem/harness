---
name: "harness_core.model.provider._normalize_response"
description: "Convert an OpenAI Responses API response into the normalized"
source: "harness_core/model/provider.py"
---

Convert an OpenAI Responses API response into the normalized
chat-completion dict shape (``choices`` + ``usage``) shared by both the
sync and async chat paths.

## Signature
```python
_normalize_response(response) -> dict
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
