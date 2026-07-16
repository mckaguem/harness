---
name: "harness_core.config.get_provider_config"
description: "Retrieve a ProviderConfig by its identifier name."
source: "harness_core/config.py"
---

Retrieve a ProviderConfig by its identifier name.

Looks up the provider in the providers dictionary using the exact ``name``
field. Returns ``None`` if not found.

## Signature
```python
get_provider_config(name: str) -> ProviderConfig | None
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
