---
name: "harness_core.tools.read_file.read_file"
description: "Read a file and return its contents with auto-detected format. Supports offset and limit parameters to read specific line ranges."
source: "harness_core/tools/read_file.py"
---

Read a file and return its contents with auto-detected format. Supports offset and limit parameters to read specific line ranges.

Returns:
    A ``ToolResult`` containing the formatted content (type + content joined
    by " | "), or an error result for failures.

## Signature
```python
read_file(filename: str, offset: int, limit: int) -> ToolResult
```

## References
- [Module: harness_core.tools.read_file](harness_core_tools_read_file) - Parent module
