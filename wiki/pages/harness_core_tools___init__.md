---
name: "harness_core.tools.__init__"
description: "Tools subpackage — self-discovering skills."
source: "harness_core/tools/__init__.py"
---

Tools subpackage — self-discovering skills.

A file is treated as a "skill" if it defines function_def at the top level.
This module scans the package directory for such files, builds the agent tool
schema from each one's function_def, and maintains a dispatcher registry
mapping tool names to their callables.

## References
- [_discover_skills](harness_core_tools___init____discover_skills) - Scan this package's directory for skills — i
- [_build](harness_core_tools___init____build) - Re-discover skills and populate AGENT_TOOLS / DISPATCH_REGISTRY / SUMMARY_REGISTRY
- [AGENT_TOOLS](harness_core_tools___init___AGENT_TOOLS) - Constant
- [DISPATCH_REGISTRY](harness_core_tools___init___DISPATCH_REGISTRY) - Constant
- [SUMMARY_REGISTRY](harness_core_tools___init___SUMMARY_REGISTRY) - Constant
- [Module Index](../index/harness_core_tools.md) - Parent module index
