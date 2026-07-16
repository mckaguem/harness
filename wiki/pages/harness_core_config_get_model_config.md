---
name: "harness_core.config.get_model_config"
description: "Retrieve a ModelConfig by its name."
source: "harness_core/config.py"
---

Retrieve a ModelConfig by its name.

Looks up the model in the models dictionary using the exact ``name`` field.
Returns ``None`` if no explicit entry exists for that model. The caller can
then fall back to the global ``context_length`` from load_harness_config().

## Signature
```python
get_model_config(model_name: str) -> ModelConfig | None
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
