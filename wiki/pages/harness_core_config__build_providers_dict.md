---
name: "harness_core.config._build_providers_dict"
description: "Build a providers dict from a raw YAML provider list."
source: "harness_core/config.py"
---

Build a providers dict from a raw YAML provider list.

Returns a dictionary keyed by provider ``name`` with :class:`ProviderConfig`
instances as values. Only entries that are dicts containing a ``name`` key
are included.

## Signature
```python
_build_providers_dict(raw_provs: list[dict]) -> dict[str, ProviderConfig]
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
