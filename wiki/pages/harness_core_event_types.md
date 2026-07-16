---
name: "harness_core.event_types"
description: "Event payload types for the Harness event system."
source: "harness_core/event_types.py"
---

Event payload types for the Harness event system.

This module defines base classes and concrete payload types used for
structured event data passed through the event bus. Using typed payloads
enables better IDE support, runtime validation, and clearer APIs.

## References
- [EventPayload](harness_core_event_types_EventPayload) - Base class for all event payloads
  - [to_dict](harness_core_event_types_EventPayload_to_dict) - Convert the payload to a dictionary for serialization
- [TaskInfo](harness_core_event_types_TaskInfo) - Represents a single task with its status information
  - [to_dict](harness_core_event_types_TaskInfo_to_dict) - Convert to a JSON-compatible dictionary
- [TaskListPayload](harness_core_event_types_TaskListPayload) - Event payload containing a complete task list snapshot
  - [from_task_list](harness_core_event_types_TaskListPayload_from_task_list) - Create a TaskListPayload from a TaskList instance
  - [to_dict](harness_core_event_types_TaskListPayload_to_dict) - Convert the payload to a dictionary for serialization
- [SystemMessagePayload](harness_core_event_types_SystemMessagePayload) - Event payload for a system-level status/notification message
- [SessionErrorPayload](harness_core_event_types_SessionErrorPayload) - Event payload for an error reported at session level (e
- [AgentResponsePayload](harness_core_event_types_AgentResponsePayload) - Event payload for an agent turn response (the LLM's text reply)
- [TurnStatsPayload](harness_core_event_types_TurnStatsPayload) - Event payload for post-turn usage + elapsed-time stats pushed to the sidebar
- [ToolCallPayload](harness_core_event_types_ToolCallPayload) - Event payload for an in-progress tool call
- [ToolResultPayload](harness_core_event_types_ToolResultPayload) - Event payload for a tool result
- [ToolErrorPayload](harness_core_event_types_ToolErrorPayload) - Event payload for a tool-call error
- [Module Index](../index/harness_core.md) - Parent module index
