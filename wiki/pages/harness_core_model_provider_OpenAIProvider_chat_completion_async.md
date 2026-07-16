---
name: "harness_core.model.provider.chat_completion_async"
description: "Get chat completion from OpenAI via the Responses API (async)."
source: "harness_core/model/provider.py"
---

Get chat completion from OpenAI via the Responses API (async).

Mirrors :meth:`chat_completion` but awaits the SDK call.

## Signature
```python
chat_completion_async(self, messages: list[Dict], model: str, **kwargs) -> Dict
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- [Class: OpenAIProvider](harness_core_model_provider_OpenAIProvider) - Parent class
