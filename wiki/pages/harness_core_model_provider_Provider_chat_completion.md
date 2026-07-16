---
name: "harness_core.model.provider.chat_completion"
description: "Get chat completion from the provider."
source: "harness_core/model/provider.py"
---

Get chat completion from the provider.

Args:
    messages: List of message dictionaries with 'role' and 'content'
    model: Model name to use
    **kwargs: Additional provider-specific parameters

Returns:
    Dictionary with completion response

## Signature
```python
chat_completion(self, messages: list[Dict], model: str, **kwargs) -> Dict
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- [Class: Provider](harness_core_model_provider_Provider) - Parent class
