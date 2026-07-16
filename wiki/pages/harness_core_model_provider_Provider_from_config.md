---
name: "harness_core.model.provider.from_config"
description: "Create a Provider instance from a configuration object."
source: "harness_core/model/provider.py"
---

Create a Provider instance from a configuration object.

Args:
    config: A ProviderConfig with provider_type, base_url,
            and optional api_key fields.

Returns:
    An OpenAIProvider instance (Ollama support was removed).

Raises:
    ValueError: If required fields are missing from the configuration.

## Signature
```python
from_config(cls, config: 'ProviderConfig') -> 'Provider'
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- [Class: Provider](harness_core_model_provider_Provider) - Parent class
