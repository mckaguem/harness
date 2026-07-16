---
name: "harness_core.tools.list_dir.list_dir"
description: "Explore directory contents and return an LLM-friendly tree view."
source: "harness_core/tools/list_dir.py"
---

Explore directory contents and return an LLM-friendly tree view.

Walks the directory tree starting at *path* (relative to the project root)
and renders it using Unicode box-drawing characters, similar to the bash
``tree`` command. Token-heavy build directories are always ignored, and the
descent depth is clamped to keep output bounded.

Parameters
----------
path : str, optional
    Directory (relative to the project root) to explore. Defaults to ``'.'``.
max_depth : int, optional
    Maximum descent depth from the root directory. Defaults to 2 and is
    clamped to the range [1, 4].
include_hidden : bool, optional
    Whether to include entries whose names start with ``.``. Defaults to
    False.

Returns
-------
ToolResult
    A ``ToolResult`` whose ``llm_text`` / ``display_text`` contain the tree,
    or an error result for invalid or unsafe paths.

## Signature
```python
list_dir(path: str, max_depth: int, include_hidden: bool) -> ToolResult
```

## References
- [Module: harness_core.tools.list_dir](harness_core_tools_list_dir) - Parent module
