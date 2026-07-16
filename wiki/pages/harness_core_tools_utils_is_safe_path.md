---
name: "harness_core.tools.utils.is_safe_path"
description: "Ensure the target path is within an allowed directory."
source: "harness_core/tools/utils.py"
---

Ensure the target path is within an allowed directory.

Allowed locations are ``/tmp`` (resolving anywhere under it) and the
project root (found via project markers like ``.git`` or ``.harness_py``;
falls back to the current working directory if no root is found).

Paths that resolve outside both ``/tmp`` and the project root are rejected,
and any unexpected error fails closed (returns ``False``).

## Signature
```python
is_safe_path(filename: str) -> bool
```

## References
- [Module: harness_core.tools.utils](harness_core_tools_utils) - Parent module
