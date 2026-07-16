---
name: "harness_core.agent.tool_context.ToolContext"
description: "Execution context for a single tool invocation."
source: "harness_core/agent/tool_context.py"
---

Execution context for a single tool invocation.

Attributes:
    agent: The agent that issued the tool call. ``None`` when the tool is
        invoked outside of any active agent loop.

## Methods
- **__init__(self, agent: object | None) -> None** - No description
- **__repr__(self) -> str** - No description

## Class Variables
None

## References
- [Module: harness_core.agent.tool_context](harness_core_agent_tool_context) - Parent module
- [__init__](harness_core_agent_tool_context_ToolContext___init__) - Method
- [__repr__](harness_core_agent_tool_context_ToolContext___repr__) - Method
