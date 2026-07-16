---
name: "harness_core.model.provider.create_provider"
description: "Create a provider instance."
source: "harness_core/model/provider.py"
---

Create a provider instance.

Ollama support was removed; the provider is always an OpenAIProvider,
which uses the OpenAI Responses API.

## Signature
```python
create_provider(client) -> Provider
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
