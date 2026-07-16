---
name: "harness_core.tools.list_dir._build_tree"
description: "Recursively render *directory* into ``tree``-style lines."
source: "harness_core/tools/list_dir.py"
---

Recursively render *directory* into ``tree``-style lines.

Parameters
----------
directory : Path
    The directory to render.
prefix : str
    The indentation/connector prefix inherited from ancestor levels.
depth : int
    How many levels deep we already are relative to the search root
    (the root itself is depth 0).
max_depth : int
    Maximum descent depth; directories at this depth are listed but not
    descended into.
include_hidden : bool
    Whether entries whose name starts with ``.`` should be included.

## Signature
```python
_build_tree(directory: Path, prefix: str, depth: int, max_depth: int, include_hidden: bool) -> list[str]
```

## References
- [Module: harness_core.tools.list_dir](harness_core_tools_list_dir) - Parent module
