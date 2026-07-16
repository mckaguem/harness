---
name: "harness_core.agent.tool_context"
description: "ToolContext — the execution context handed to every tool call."
source: "harness_core/agent/tool_context.py"
---

ToolContext — the execution context handed to every tool call.

Previously, tool implementations reached for the ``CURRENT_AGENT`` contextvar
directly to find "the agent that called me". That created two problems:

1. **Hidden coupling.** A tool's behaviour silently depended on global process
   state (the contextvar), making it impossible to tell, by reading the tool's
   signature, that it depends on an agent at all.
2. **Headless ambiguity.** When a tool was dispatched outside a
   ``handle_prompt`` loop (e.g. by an external harness), ``CURRENT_AGENT`` was
   ``None`` and the tool had to either crash with an opaque message or silently
   bootstrap a shared fallback agent — neither of which is correct for a
   per-agent concern like a task list.

The fix is to make the dependency explicit: every tool that needs the calling
agent receives a :class:`ToolContext` object as its ``ctx`` argument. The
dispatcher builds this context from whatever agent is currently active
(``CURRENT_AGENT``), so:

* inside a ``handle_prompt`` loop, ``ctx.agent`` is the agent running that loop;
* inside a sub-agent's loop, ``ctx.agent`` is that sub-agent (it has its own
  task list, by construction);
* outside any loop, ``ctx.agent`` is ``None`` and the tool fails *loudly* with a
  clear error instead of quietly sharing a hidden agent's state.

Keeping the context as an object (rather than passing the bare agent) leaves
room to add things like the active session, request id, or cancellation token
later without changing every tool signature. For now it just carries the agent
(YAGNI — only what's needed today).

## References
- [ToolContext](harness_core_agent_tool_context_ToolContext) - Execution context for a single tool invocation
  - [__init__](harness_core_agent_tool_context_ToolContext___init__) - Method
  - [__repr__](harness_core_agent_tool_context_ToolContext___repr__) - Method
- [current_tool_context](harness_core_agent_tool_context_current_tool_context) - Build a :class:`ToolContext` for the agent currently bound to CURRENT_AGENT
- [Module Index](../index/harness_core_agent.md) - Parent module index
