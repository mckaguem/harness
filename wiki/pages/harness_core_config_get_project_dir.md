---
name: "harness_core.config.get_project_dir"
description: "Return the project config directory ``project_root/.harness_py/``."
source: "harness_core/config.py"
---

Return the project config directory ``project_root/.harness_py/``.

Falls back to ``Path.cwd()`` when no project marker is found, mirroring
the tolerance already present in ``AgentType._build_system_prompt``.

## Signature
```python
get_project_dir() -> Path
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
