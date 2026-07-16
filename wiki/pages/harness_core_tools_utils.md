---
name: "harness_core.tools.utils"
description: "Shared utilities for tools — path safety checks, ANSI stripping, and error formatting."
source: "harness_core/tools/utils.py"
---

Shared utilities for tools — path safety checks, ANSI stripping, and error formatting.

## References
- [is_safe_path](harness_core_tools_utils_is_safe_path) - Ensure the target path is within an allowed directory
- [_strip_ansi](harness_core_tools_utils__strip_ansi) - Remove ANSI escape sequences and inline color tags from *text*
- [make_error_result](harness_core_tools_utils_make_error_result) - Create a standardized error ToolResult
- [Module Index](../index/harness_core_tools.md) - Parent module index
