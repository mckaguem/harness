---
name: "harness_core.terminal_io.event_listener"
description: "Event-driven wiring between the terminal_io EventBus and the TUI."
source: "harness_core/terminal_io/event_listener.py"
---

Event-driven wiring between the terminal_io EventBus and the TUI.

This module subscribes a single :class:`HarnessEventListener` to the relevant
``agent.*`` topics and dispatches each event to the appropriate handler.  A
sender-id regex filter (see :func:`harness_core.eventbus.filter_by_sender`)
restricts updates to a single agent (e.g. ``Agent.main``), so only events
published by that agent reach the TUI.

Handled topics:

* ``agent.tasklist.initialize`` / ``agent.tasklist.update`` / ``agent.tasklist.reset``
  -> refresh the right-hand TUI task sidebar from the payload.
* ``agent.session.autocompress`` / ``agent.status.ready``
  -> render a system banner via :func:`.display.print_system`.
* ``agent.tool.call`` / ``agent.tool.result`` / ``agent.tool.error``
  -> render tool call/result/error panels via :func:`.display.display_tool_call`,
     :func:`.display.display_tool_result`, and :func:`.display.display_error` (only for events
     whose sender matches the filtered agent id, e.g. ``Agent.main``).
* ``agent.session.error``
  -> render an error message via :func:`.display.display_error` (only for events
    whose sender matches the filtered agent id, e.g. ``Agent.main``).
* ``agent.turn.response``
  -> render the agent's response via :func:`.display.display_agent_response`.
* ``agent.turn.stats``
  -> push turn usage + elapsed time to the sidebar via :func:`.speed.display_turn_stats`.

## References
- [_make_refresh_handler](harness_core_terminal_io_event_listener__make_refresh_handler) - Build the shared async handler used by each task-list event handler
- [_make_system_message_handler](harness_core_terminal_io_event_listener__make_system_message_handler) - Build the shared async handler used by each system-message event handler
- [make_event_listener](harness_core_terminal_io_event_listener_make_event_listener) - Create a :class:`HarnessEventListener` filtered to ``agent_id``
- [subscribe_event_listener](harness_core_terminal_io_event_listener_subscribe_event_listener) - Create and subscribe a :class:`HarnessEventListener` for ``agent_id``
- [make_task_list_listener](harness_core_terminal_io_event_listener_make_task_list_listener) - Backward-compatible alias for :func:`make_event_listener`
- [subscribe_task_list_listener](harness_core_terminal_io_event_listener_subscribe_task_list_listener) - Backward-compatible alias for :func:`subscribe_event_listener`
- [Module Index](../index/harness_core_terminal_io.md) - Parent module index
