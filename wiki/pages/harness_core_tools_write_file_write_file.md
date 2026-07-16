---
name: "harness_core.tools.write_file.write_file"
description: "Write to a file if it is within the current working directory."
source: "harness_core/tools/write_file.py"
---

Write to a file if it is within the current working directory.

Returns:
    A ``ToolResult`` containing JSON-encoded status data and filename/bytes info,
    or an error result for failures.

## Signature
```python
write_file(filename: str, content: str) -> ToolResult
```

## References
- [Module: harness_core.tools.write_file](harness_core_tools_write_file) - Parent module
