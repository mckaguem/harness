---
name: "harness_core.tools.edit_file.edit_file"
description: "Apply a single search-and-replace edit to *filename*."
source: "harness_core/tools/edit_file.py"
---

Apply a single search-and-replace edit to *filename*.

``old_text`` must be an exact, unique snippet that appears in the file;
only its first occurrence is replaced with ``new_text``. If ``old_text``
is not found, an error result is returned and the file remains unchanged
(atomic per call).

## Signature
```python
edit_file(filename: str, old_text: str, new_text: str) -> ToolResult
```

## References
- [Module: harness_core.tools.edit_file](harness_core_tools_edit_file) - Parent module
