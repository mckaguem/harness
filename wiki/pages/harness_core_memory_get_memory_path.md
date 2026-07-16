---
name: "harness_core.memory.get_memory_path"
description: "Return the path to ``MEMORY.md`` in the project root, or ``None`` if absent."
source: "harness_core/memory.py"
---

Return the path to ``MEMORY.md`` in the project root, or ``None`` if absent.

Uses :func:`harness_core.utils.project_root` to locate the project root; falls
back to the current working directory if no project markers are found (so the
memory file still resolves inside test environments).

## Signature
```python
get_memory_path() -> Path | None
```

## References
- [Module: harness_core.memory](harness_core_memory) - Parent module
