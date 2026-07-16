---
name: "harness_core.config.load_harness_config"
description: "Load and merge configuration from global and project ``config.yaml`` files."
source: "harness_core/config.py"
---

Load and merge configuration from global and project ``config.yaml`` files.

Returns a dictionary with keys:
- "providers": dict[str, ProviderConfig] keyed by provider name
- "models": dict[str, ModelConfig] keyed by model name (with context_length)
- "default_model": str | None
- "context_length": int (global default context length fallback)

## Signature
```python
load_harness_config() -> dict
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
