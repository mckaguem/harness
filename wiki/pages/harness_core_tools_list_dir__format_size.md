---
name: "harness_core.tools.list_dir._format_size"
description: "Return a concise human-readable size for *size_bytes*."
source: "harness_core/tools/list_dir.py"
---

Return a concise human-readable size for *size_bytes*.

Sizes under 1 MB are shown in KB; everything else is shown in MB. Values
are rounded to the nearest whole unit.

## Signature
```python
_format_size(size_bytes: int) -> str
```

## References
- [Module: harness_core.tools.list_dir](harness_core_tools_list_dir) - Parent module
