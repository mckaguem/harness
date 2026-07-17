"""Textual Harness App definition for the harness TUI."""
from __future__ import annotations

import asyncio
import traceback

from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Static, TextArea

from harness_core.event_types import TaskListPayload
from harness_core.terminal_io.widgets import (
    StatusSpinner,
    TaskListSidebar,
)


class TextualHarnessApp(App):
    """A minimal, idiomatic textual harness shell.

    Layout (top → bottom)::

        Header
        VerticalScroll  (output; a scrollable column of Static/Collapsible)
        TextArea (multi-line input)
        Footer
    """

    CSS = """
    TextArea {
        height: 10;
        border: round $accent;
        background: $surface;
    }
    VerticalScroll {
        height: 1fr;
        border: round $primary;
        overflow-y: auto;
        overflow-x: hidden;
    }
    .--sidebar {
        width: 44;
        height: 1fr;
        border: round $secondary;
        background: $panel;
        padding: 0 1;
    }
    .--sidebar Static {
        height: auto;
    }
    Static {
        height: auto;
    }
    Collapsible {
    }
    StatusSpinner {
        height: 1;
        dock: bottom;
        background: $panel;
        color: $accent;
        content-align: left middle;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+g", "submit_input", "Submit")
    ]

    def __init__(self, agent=None, on_exit=None) -> None:
        super().__init__()
        self._agent = agent
        self._on_exit = on_exit
        self._output: VerticalScroll | None = None
        self._event_listener = None  # Keep a reference so it's not garbage collected

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                VerticalScroll(id="output"),
                TextArea(id="input", language=None, soft_wrap=True),
                StatusSpinner(id="spinner", classes="--busy"),
            ),
            TaskListSidebar(id="task-sidebar", classes="--sidebar"),
        )
        yield Footer()

    def update_sidebar_usage(self, text: str | None) -> None:
        """Push the most recent usage summary to the right sidebar (thread-safe).

        Marshals a single call onto the app thread that sets the stored usage
        text and re-renders the sidebar above the task list.  This is only ever
        invoked from the HarnessTUI controller after the app is bound and
        running; it guards on the App's own ``is_running`` flag and wraps the
        marshalled work in try/except so a stray call never raises (Textual's
        ``App`` does not expose an ``is_active`` property, which was the
        original source of the reported crash).
        """
        if not self.is_running:
            return

        try:
            sidebar = self.query_one("#task-sidebar", TaskListSidebar)
        except Exception:
            return

        sidebar.set_usage(text)
        sidebar.refresh_tasks()

    def update_sidebar_tasks_from_payload(self, payload: TaskListPayload) -> None:
        """Push a TaskListPayload snapshot to the right sidebar (thread-safe).

        Marshals a single call onto the app thread that re-renders the sidebar
        from the event payload.  Guards on the App's own ``is_running`` flag and
        wraps the marshalled work in try/except so a stray call never raises.
        """
        if not self.is_running:
            return

        def _do() -> None:
            try:
                sidebar = self.query_one("#task-sidebar", TaskListSidebar)
            except Exception:
                return
            sidebar.refresh_tasks_from_payload(payload)

        try:
            self.call_from_thread(_do)
        except Exception:
            pass

    async def on_mount(self) -> None:
        from .harness_tui import get_tui as _get_tui

        controller = _get_tui()
        controller.bind(
            self,
            self.query_one("#output", VerticalScroll),
            self.query_one("#input", TextArea),
            self.query_one("#spinner", StatusSpinner),
        )
        # Register this app's running loop so that events published from the
        # worker thread (the agent loop) are marshalled back onto the app
        # thread where the widgets live.
        from harness_core.eventbus import set_event_loop

        set_event_loop(asyncio.get_running_loop())

        # Wire up the right-hand task-list sidebar.
        sidebar = self.query_one("#task-sidebar", TaskListSidebar)
        if self._agent is not None:
            sidebar.set_agent(self._agent)
        # Initial paint + heartbeat so the sidebar is always correct.
        sidebar.refresh_tasks()
        self.set_interval(1.0, sidebar.refresh_tasks)

        # Subscribe the consolidated EventListener that drives the sidebar from
        # the TaskList event bus and renders system banners (e.g. auto-compress
        # / agent-ready) via the terminal_io display layer.  The listener filters
        # by this agent's sender id so only the main agent's events are shown.
        # We await the subscription here (on_mount runs on the app loop's thread)
        # so the listener is fully subscribed to the bus BEFORE the worker-thread
        # user_loop emits its one-shot ``agent.status.ready`` banner — otherwise
        # the late subscriber would miss that event and the banner would never
        # appear.
        try:
            from .event_listener import subscribe_event_listener

            if self._agent is not None:
                listener = subscribe_event_listener(self._agent.id)
                self._event_listener = listener  # Keep a reference so it's not garbage collected
        except Exception as e:
            pass

        # Cache the output pane reference for _show_loop_error (worker-thread path).
        try:
            self._output = self.query_one("#output", VerticalScroll)
        except Exception:
            self._output = None

        self.call_after_refresh(self._start_loop)

    def _start_loop(self) -> None:
        """Begin the user loop on a worker thread (app is live now)."""
        if self._agent is None:
            return

        def _loop() -> None:
            try:
                self._agent.user_loop(on_exit=self._on_exit)
            except Exception:
                # Surface the error in the UI instead of dying silently.
                self.call_from_thread(
                    self._show_loop_error, traceback.format_exc()
                )
            finally:
                # The loop exited (e.g. /exit or an error); close the app from
                # the app thread.
                self.call_from_thread(self.exit)

        self.run_worker(
            _loop,
            thread=True,
            group="loop",
            description="harness user loop",
            exit_on_error=False,  # we handle errors ourselves
        )

    def _show_loop_error(self, tb: str) -> None:
        """Render a worker-thread exception into the output pane."""
        output = self._output
        if output is not None:
            output.mount(
                Static(
                    Panel(
                        Text.from_markup(f"[red bold]Loop error:[/]\n{tb}"),
                        title="Error",
                        border_style="red",
                    )
                )
            )

    def action_submit_input(self) -> None:
        from .harness_tui import get_tui as _get_tui

        _get_tui().submit()


def launch(agent, on_exit=None) -> None:
    """Launch the Textual TUI and drive ``user_loop`` on a worker thread.

    Args:
        agent: An initialized :class:`~agent.core.Agent` instance.
        on_exit: Optional callback invoked when the loop ends (see
            :func:`agent.loop.user_loop`).
    """
    app = TextualHarnessApp(agent=agent, on_exit=on_exit)
    app.run()
