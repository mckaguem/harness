"""Textual Harness App definition — event-driven TUI entry point."""
from __future__ import annotations
import logging

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static, TextArea

from textual.events import Message

from harness_core.event_types import TaskListPayload
from harness_core.terminal_io.widgets import (
    StatusSpinner,
    TaskListSidebar,
)


class ShowQuitDialog(Message):
    """Custom message dispatched when a quit request needs the dialog shown.

    Post this via app.post_message() from anywhere — it gets processed inside
    Textual's _process_messages loop where active_app ContextVar is set, so
    push_screen() can render without LookupError.
    """
    pass


class QuitConfirmDialog(ModalScreen[bool]):
    """Confirmation dialog shown when user presses Ctrl+Q."""

    CSS = """
    QuitConfirmDialog {
        align: center middle;
        background: $surface 80%;
        width: 50;
        height: 9;
        
        Vertical {
            width: 100%;
            height: 100%;
            align: center middle;
        }
    }

    #quit-message {
        margin-bottom: 1;
    }

    #quit-buttons {
        dock: bottom;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss(False)", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("[b]Are you sure you want to quit?[/b]", id="quit-message"),
            Horizontal(
                Button("Yes", variant="primary", id="quit-yes"),
                Button("No", variant="default", id="quit-no"),
            ),
            id="quit-buttons",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the dialog."""
        import logging
        logger = logging.getLogger(__name__)

        if event.button.id == "quit-yes":
            # Publish quit confirm via app then close with True
            logger.debug("QuitConfirmDialog: publishing quit_confirm...")
            try:
                self.app.publish_quit_confirm()
                logger.debug("QuitConfirmDialog: publish succeeded, dismissing...")
                self.dismiss(True)
            except Exception as e:
                logger.error(f"QuitConfirmDialog: PUBLISH FAILED: {type(e).__name__}: {e}")
        else:
            self.dismiss(False)


class TextualHarnessApp(App):
    """A minimal, idiomatic textual harness shell.

    Layout (top → bottom)::

        Header
        VerticalScroll  (output; a scrollable column of Static/Collapsible)
        TextArea (multi-line input)
        Footer
    """

    TITLE = "harness.py"

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
        ("ctrl+q", "confirm_quit", "Quit"),
        ("ctrl+g", "submit_input", "Submit")
    ]

    def __init__(self, agent_id: str | None = None, on_exit=None) -> None:
        super().__init__()
        self._agent_id = agent_id  # Store only the agent id string — no Agent object reference
        self._on_exit = on_exit
        self._output: VerticalScroll | None = None

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

        #def _do() -> None:
        try:
            sidebar = self.query_one("#task-sidebar", TaskListSidebar)
        except Exception:
            return
        sidebar.refresh_tasks_from_payload(payload)

        # try:
        #     self.call_from_thread(_do)
        # except Exception:
        #     pass

    def update_sidebar_model_name(self, model_name: str | None) -> None:
        """Push the most recent model name to the right sidebar (thread-safe).

        Marshals a single call onto the app thread that sets the stored model
        text and re-renders the sidebar above the task list.
        """
        if not self.is_running:
            return

        try:
            sidebar = self.query_one("#task-sidebar", TaskListSidebar)
            sidebar.set_model_name(model_name)
        except Exception:
            return

    async def on_mount(self) -> None:
        from .harness_tui import get_tui as _get_tui

        controller = _get_tui()
        controller.bind(
            self,
            self.query_one("#output", VerticalScroll),
            self.query_one("#input", TextArea),
            self.query_one("#spinner", StatusSpinner),
        )
        # Wire up the right-hand task-list sidebar.
        sidebar = self.query_one("#task-sidebar", TaskListSidebar)

        # Initial paint + heartbeat so the sidebar is always correct.
        sidebar.refresh_tasks()

        # Cache the output pane reference for error display.
        try:
            self._output = self.query_one("#output", VerticalScroll)
        except Exception:
            self._output = None

        # Focus the text input on startup so the user can type immediately.
        try:
            self.query_one("#input", TextArea).focus()
        except Exception:
            pass

        # Start the TUI's event-bus listener ONCE, on the app thread while the
        # app is running, so events mutate widgets only from the live app loop.
        # (Moved out of __main__ to avoid a "App is not running" race where the
        # listener fired before the Textual loop initialized.)
        if self._agent_id is not None:
            from .event_listener import subscribe_event_listener
            from harness_core.eventbus import event_bus
            self._event_listener = subscribe_event_listener(self._agent_id, event_bus)

    async def on_ShowQuitDialog(self, event) -> None:
        """Handle a quit-request dialog push.

        Dispatched by Textual's message pump inside its active_app ContextVar,
        so push_screen() can render without LookupError.
        """
        from harness_core.runtime.manager import Manager

        # Get the manager from where it was stored
        manager = getattr(self, "_manager", None)
        if manager is not None:
            listener = getattr(manager, "_listener", None)
            if listener is not None and hasattr(listener, "handle_show_quit_dialog"):
                await listener.handle_show_quit_dialog(event)

    def action_confirm_quit(self) -> None:
        """Show confirmation dialog before quitting."""
        self.push_screen(QuitConfirmDialog())

    def publish_quit_confirm(self) -> None:
        """Publish the PROCESS_CONTROL_QUIT_CONFIRM event via the event bus."""
        from .event_publisher import get_tui_publisher
        publisher = get_tui_publisher()
        if publisher is not None:
            from harness_core.event_types import AppControlPayload, PROCESS_CONTROL_QUIT_CONFIRM
            publisher.publish(
                PROCESS_CONTROL_QUIT_CONFIRM,
                AppControlPayload(action="quit_confirm"),
            )

    def request_exit(self) -> None:
        """Signal that the app should close (called by Manager on shutdown)."""
        if self.is_running:
            try:
                self.exit()
            except Exception:
                pass

    def action_submit_input(self) -> None:
        """Handle user input submission. Reads the current text from the
        TextArea widget and publishes it as an event for the agent to consume.
        """
        try:
            input_widget = self.query_one("#input", TextArea)
            message = input_widget.text
        except Exception:
            return

        # Clear + refocus immediately so the user sees feedback right away
        try:
            input_widget = self.query_one("#input", TextArea)
            input_widget.text = ""
            input_widget.focus()
        except Exception:
            pass

        from .harness_tui import get_tui as _get_tui
        tui = _get_tui()
        if tui is not None and message.strip():

            # Display the user's message in the output pane
            try:
                from harness_core.terminal_io.display import display_user_message
                display_user_message(message)

            except Exception:
                pass
            # Publish as event for the agent to consume
            tui.publish_user_input(message)

    async def start(self):
        await self.run_async()

async def launch(agent_id: str | None = None, on_exit=None) -> None:
    """Launch the Textual TUI.

    The agent loop is started independently by ``__main__.py`` — this function
    only launches the TUI app and does NOT take ownership of the agent's
    lifecycle or threading.

    Args:
        agent_id: The agent identifier string (e.g., "Agent.main") used to
            filter events for display in the sidebar. No Agent object is needed.
        on_exit: Optional callback invoked when the TUI exits.
    """
    logging.debug('Starting TUI')
    app = TextualHarnessApp(agent_id=agent_id, on_exit=on_exit)
    await app.start()
