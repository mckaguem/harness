---
name: "harness_core.config._build_models_dict"
description: "Build a models dict from a raw YAML model list."
source: "harness_core/config.py"
---

Build a models dict from a raw YAML model list.

Returns a dictionary keyed by model ``name`` with :class:`ModelConfig`
instances as values. Only entries that are dicts containing a ``name`` key
are included.

## Signature
```python
_build_models_dict(raw_models: list[dict]) -> dict[str, ModelConfig]
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
