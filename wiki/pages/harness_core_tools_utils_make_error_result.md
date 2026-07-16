---
name: "harness_core.tools.utils.make_error_result"
description: "Create a standardized error ToolResult."
source: "harness_core/tools/utils.py"
---

Create a standardized error ToolResult.

This helper centralizes the common pattern of returning error results across
all tool implementations, ensuring consistent formatting and reducing boilerplate.

Args:
    message: The error message to display (will be ANSI-stripped).
    title: Optional custom title. Defaults to "Error".

Returns:
    A ToolResult with theme="error", type_tag="text", and the formatted message.

## Signature
```python
make_error_result(message: str, title: str) -> ToolResult
```

## References
- [Module: harness_core.tools.utils](harness_core_tools_utils) - Parent module
