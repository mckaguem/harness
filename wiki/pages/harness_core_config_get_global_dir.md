---
name: "harness_core.config.get_global_dir"
description: "Return the global config directory, defaulting to ``~/.harness_py/``."
source: "harness_core/config.py"
---

Return the global config directory, defaulting to ``~/.harness_py/``.

Override with the ``HARNESS_PY_HOME`` environment variable. Falls back to
``Path.cwd()`` when no project marker is found (so config loading can
tolerate marker-less environments such as test sandboxes).

## Signature
```python
get_global_dir() -> Path
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
