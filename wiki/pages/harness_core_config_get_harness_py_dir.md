---
name: "harness_core.config.get_harness_py_dir"
description: "Return both harness_py directories as a ``(project_dir, global_dir)`` tuple."
source: "harness_core/config.py"
---

Return both harness_py directories as a ``(project_dir, global_dir)`` tuple.

Both are :class:`Path` objects with ``agents/`` and ``skills/`` subdirectories
available inside them. Project dir takes precedence over global when
discovering skills and agents with the same name.

## Signature
```python
get_harness_py_dir() -> tuple[Path, Path]
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
