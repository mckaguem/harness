---
name: "harness_core.terminal_io.tui"
description: "Textual-based terminal UI for the harness."
source: "harness_core/terminal_io/tui.py"
---

Textual-based terminal UI for the harness.

This module provides an idiomatic :mod:`textual` application that replaces the
plain Rich/``prompt_toolkit`` REPL for interactive sessions.  The design keeps
the existing ``terminal_io`` public surface intact:

* :class:`TextualHarnessApp` is a small, composable app: a header, a
  :class:`~textual.containers.VerticalScroll` output pane (a scrollable column
  of :class:`~textual.widgets.Static` wrappers — and, for tool calls,
  :class:`~textual.widgets.Collapsible` widgets whose result is rendered inline
  inside them), a multi-line :class:`~textual.widgets.TextArea` input, and a
  footer.
* :class:`HarnessTUI` is a controller singleton that owns the running app
  instance and exposes thread-safe ``write``/``prompt`` operations used by the
  classic ``display_*`` / ``prompt_user`` helpers.  When the TUI is *not*
  active the controller is a no-op and those helpers fall back to their
  original Rich / ``prompt_toolkit`` behaviour.

The interactive loop itself still lives in :func:`agent.loop.user_loop`; the
TUI simply runs it on a worker thread and routes all I/O through the
controller, so the REPL logic and the existing tests are unchanged.

## References
- [StatusSpinner](harness_core_terminal_io_tui_StatusSpinner) - A non-blocking animated "thinking" indicator for the message panel
  - [__init__](harness_core_terminal_io_tui_StatusSpinner___init__) - Method
  - [render](harness_core_terminal_io_tui_StatusSpinner_render) - Method
- [TaskListSidebar](harness_core_terminal_io_tui_TaskListSidebar) - A right-hand panel that renders the main agent's task list
  - [__init__](harness_core_terminal_io_tui_TaskListSidebar___init__) - Method
  - [set_agent](harness_core_terminal_io_tui_TaskListSidebar_set_agent) - Provide the agent whose task list should be displayed
  - [set_usage](harness_core_terminal_io_tui_TaskListSidebar_set_usage) - Store the most recent LLM usage summary to render above the tasks
  - [refresh_tasks](harness_core_terminal_io_tui_TaskListSidebar_refresh_tasks) - Re-render the sidebar
  - [refresh_tasks_from_payload](harness_core_terminal_io_tui_TaskListSidebar_refresh_tasks_from_payload) - Re-render the task list from a TaskListPayload (event-driven)
- [HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Controller singleton bridging the classic I/O helpers and the TUI
  - [__init__](harness_core_terminal_io_tui_HarnessTUI___init__) - Method
  - [bind](harness_core_terminal_io_tui_HarnessTUI_bind) - Attach a running app and its widgets (called from ``on_mount``)
  - [is_active](harness_core_terminal_io_tui_HarnessTUI_is_active) - Return ``True`` when the TUI app is mounted and accepting I/O
  - [write](harness_core_terminal_io_tui_HarnessTUI_write) - Render ``renderable`` into the output pane (thread-safe)
  - [begin_tool_panel](harness_core_terminal_io_tui_HarnessTUI_begin_tool_panel) - Create a collapsed-by-default ``Collapsible`` for a tool call
  - [complete_tool_panel](harness_core_terminal_io_tui_HarnessTUI_complete_tool_panel) - Append a tool result into the most recent tool-call collapsible
  - [write_count](harness_core_terminal_io_tui_HarnessTUI_write_count) - Number of times :meth:`write` committed to the output pane
  - [update_sidebar_usage](harness_core_terminal_io_tui_HarnessTUI_update_sidebar_usage) - Push the most recent usage summary to the right sidebar
  - [update_sidebar_tasks_from_payload](harness_core_terminal_io_tui_HarnessTUI_update_sidebar_tasks_from_payload) - Push a TaskListPayload snapshot to the right sidebar (thread-safe)
  - [show_spinner](harness_core_terminal_io_tui_HarnessTUI_show_spinner) - Reveal the spinner so the user knows the agent is working
  - [hide_spinner](harness_core_terminal_io_tui_HarnessTUI_hide_spinner) - Hide the spinner once the agent has produced its response
  - [prompt](harness_core_terminal_io_tui_HarnessTUI_prompt) - Block the calling (loop) thread until the user submits input
  - [_arm_input](harness_core_terminal_io_tui_HarnessTUI__arm_input) - Focus + clear the input box
  - [submit](harness_core_terminal_io_tui_HarnessTUI_submit) - Resolve a pending :meth:`prompt` with the current input text
  - [reset](harness_core_terminal_io_tui_HarnessTUI_reset) - Detach the app (called on shutdown)
- [TextualHarnessApp](harness_core_terminal_io_tui_TextualHarnessApp) - A minimal, idiomatic textual harness shell
  - [__init__](harness_core_terminal_io_tui_TextualHarnessApp___init__) - Method
  - [compose](harness_core_terminal_io_tui_TextualHarnessApp_compose) - Method
  - [update_sidebar_usage](harness_core_terminal_io_tui_TextualHarnessApp_update_sidebar_usage) - Push the most recent usage summary to the right sidebar (thread-safe)
  - [update_sidebar_tasks_from_payload](harness_core_terminal_io_tui_TextualHarnessApp_update_sidebar_tasks_from_payload) - Push a TaskListPayload snapshot to the right sidebar (thread-safe)
  - [on_mount](harness_core_terminal_io_tui_TextualHarnessApp_on_mount) - Method
  - [_start_loop](harness_core_terminal_io_tui_TextualHarnessApp__start_loop) - Begin the classic user loop on a worker thread (app is live now)
  - [_show_loop_error](harness_core_terminal_io_tui_TextualHarnessApp__show_loop_error) - Render a worker-thread exception into the output pane
  - [action_submit_input](harness_core_terminal_io_tui_TextualHarnessApp_action_submit_input) - Method
- [get_tui](harness_core_terminal_io_tui_get_tui) - Return the process-wide :class:`HarnessTUI` controller
- [launch](harness_core_terminal_io_tui_launch) - Launch the textual TUI and drive ``user_loop`` on a worker thread
- [TOOL_SEPARATOR](harness_core_terminal_io_tui_TOOL_SEPARATOR) - Constant
- [Module Index](../index/harness_core_terminal_io.md) - Parent module index
