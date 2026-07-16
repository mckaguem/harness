---
name: "harness_core.terminal_io.tui.HarnessTUI"
description: "Controller singleton bridging the classic I/O helpers and the TUI."
source: "harness_core/terminal_io/tui.py"
---

Controller singleton bridging the classic I/O helpers and the TUI.

The app runs on the main thread while :func:`agent.loop.user_loop` runs on
a worker thread.  Widget mutation must therefore only happen on the app
thread; every operation here funnels through ``app.call_from_thread`` so it
is safe to call from the loop thread.

## Methods
- **__init__(self) -> None** - No description
- **bind(self, app: 'TextualHarnessApp', output: VerticalScroll, input: TextArea, spinner: 'StatusSpinner') -> None** - Attach a running app and its widgets (called from ``on_mount``)
- **is_active(self) -> bool** - Return ``True`` when the TUI app is mounted and accepting I/O
- **write(self, renderable) -> None** - Render ``renderable`` into the output pane (thread-safe)
- **begin_tool_panel(self, title: str, call_renderable) -> None** - Create a collapsed-by-default ``Collapsible`` for a tool call
- **complete_tool_panel(self, result_renderable) -> None** - Append a tool result into the most recent tool-call collapsible
- **write_count(self) -> int** - Number of times :meth:`write` committed to the output pane
- **update_sidebar_usage(self, text: str | None) -> None** - Push the most recent usage summary to the right sidebar
- **update_sidebar_tasks_from_payload(self, payload: TaskListPayload) -> None** - Push a TaskListPayload snapshot to the right sidebar (thread-safe)
- **show_spinner(self) -> None** - Reveal the spinner so the user knows the agent is working
- **hide_spinner(self) -> None** - Hide the spinner once the agent has produced its response
- **prompt(self, prompt_str: str) -> str** - Block the calling (loop) thread until the user submits input
- **_arm_input(self) -> None** - Focus + clear the input box
- **submit(self) -> None** - Resolve a pending :meth:`prompt` with the current input text
- **reset(self) -> None** - Detach the app (called on shutdown)

## Class Variables
None

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
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
