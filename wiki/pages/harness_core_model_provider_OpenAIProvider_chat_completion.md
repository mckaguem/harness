---
name: "harness_core.model.provider.chat_completion"
description: "Get chat completion from OpenAI via the Responses API."
source: "harness_core/model/provider.py"
---

Get chat completion from OpenAI via the Responses API.

Args:
    messages: List of message dictionaries with 'role' and 'content'
    model: Model name to use
    **kwargs: Additional provider-specific parameters (currently only
        ``tools`` is ever passed, and may be None).

Returns:
    Normalized completion response with ``choices`` and ``usage``.

## Signature
```python
chat_completion(self, messages: list[Dict], model: str, **kwargs) -> Dict
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- [Class: OpenAIProvider](harness_core_model_provider_OpenAIProvider) - Parent class
