---
name: "harness_core.model.provider.get_or_create"
description: "Get or create a singleton Provider for the given configuration."
source: "harness_core/model/provider.py"
---

Get or create a singleton Provider for the given configuration.

If a Provider with ``config.name`` already exists in the registry it is
returned unchanged; otherwise a new instance is created via
:meth:`from_config` and registered before being returned. This ensures
that all agents referencing the same provider name share exactly one
underlying client/connection pool.

Args:
    config: A ProviderConfig with a non-empty ``name`` field.

Returns:
    The singleton Provider instance for this configuration name.

Raises:
    ValueError: If *config* has no ``name`` attribute or it is empty.

## Signature
```python
get_or_create(cls, config: 'ProviderConfig') -> 'Provider'
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- [Class: Provider](harness_core_model_provider_Provider) - Parent class
