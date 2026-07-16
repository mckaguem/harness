---
name: "harness_core.terminal_io.tui.TextualHarnessApp"
description: "A minimal, idiomatic textual harness shell."
source: "harness_core/terminal_io/tui.py"
---

A minimal, idiomatic textual harness shell.

Layout (top → bottom)::

    Header
    VerticalScroll  (output; a scrollable column of Static/Collapsible)
    TextArea (multi-line input)
    Footer

## Methods
- **__init__(self, agent, on_exit) -> None** - No description
- **compose(self) -> 'ComposeResult'** - No description
- **update_sidebar_usage(self, text: str | None) -> None** - Push the most recent usage summary to the right sidebar (thread-safe)
- **update_sidebar_tasks_from_payload(self, payload: TaskListPayload) -> None** - Push a TaskListPayload snapshot to the right sidebar (thread-safe)
- **on_mount(self) -> None** - No description
- **_start_loop(self) -> None** - Begin the classic user loop on a worker thread (app is live now)
- **_show_loop_error(self, tb: str) -> None** - Render a worker-thread exception into the output pane
- **action_submit_input(self) -> None** - No description

## Class Variables
- `CSS`
- `BINDINGS`

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- Base class: `App`
- [__init__](harness_core_terminal_io_tui_TextualHarnessApp___init__) - Method
- [compose](harness_core_terminal_io_tui_TextualHarnessApp_compose) - Method
- [update_sidebar_usage](harness_core_terminal_io_tui_TextualHarnessApp_update_sidebar_usage) - Push the most recent usage summary to the right sidebar (thread-safe)
- [update_sidebar_tasks_from_payload](harness_core_terminal_io_tui_TextualHarnessApp_update_sidebar_tasks_from_payload) - Push a TaskListPayload snapshot to the right sidebar (thread-safe)
- [on_mount](harness_core_terminal_io_tui_TextualHarnessApp_on_mount) - Method
- [_start_loop](harness_core_terminal_io_tui_TextualHarnessApp__start_loop) - Begin the classic user loop on a worker thread (app is live now)
- [_show_loop_error](harness_core_terminal_io_tui_TextualHarnessApp__show_loop_error) - Render a worker-thread exception into the output pane
- [action_submit_input](harness_core_terminal_io_tui_TextualHarnessApp_action_submit_input) - Method
- `CSS`
- `BINDINGS`
