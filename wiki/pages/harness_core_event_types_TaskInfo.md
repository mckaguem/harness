---
name: "harness_core.event_types.TaskInfo"
description: "Represents a single task with its status information."
source: "harness_core/event_types.py"
---

Represents a single task with its status information.

This is a lightweight, serializable representation of a task that can
be included in event payloads without carrying the full Task object.

## Methods
- **to_dict(self) -> dict[str, Any]** - Convert to a JSON-compatible dictionary

## Class Variables
- `id`: int
- `description`: str
- `status`: str

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- [to_dict](harness_core_event_types_TaskInfo_to_dict) - Convert to a JSON-compatible dictionary
- `id`: int
- `description`: str
- `status`: str
