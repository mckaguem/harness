"""Event-driven controller for the harness TUI."""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from textual.containers import VerticalScroll
from textual.widgets import Static, TextArea
from rich.text import Text

from harness_core.event_types import TaskListPayload
from harness_core.terminal_io.widgets import (
    MessageCard,
    StatusSpinner,
)


if TYPE_CHECKING:
    from .tui_app import TextualHarnessApp


class HarnessTUI:
    """Event-driven controller for the Textual TUI.

    The app runs on the main thread while the agent loop runs in a worker
    thread.  Widget mutation must therefore only happen on the app thread;
    every operation here funnels through ``app.call_from_thread`` so it is
    safe to call from the loop thread.  Input handling is now event-driven:
    user input is published via :meth:`publish_user_input` instead of blocking
    with a prompt/submit cycle.
    """

    def __init__(self) -> None:
        self._app: TextualHarnessApp | None = None  # type: ignore[assignment]
        self._input: TextArea | None = None  # type: ignore[assignment]
        self._output: VerticalScroll | None = None  # type: ignore[assignment]
        self._spinner: StatusSpinner | None = None
        self._write_count = 0
        self._lock = threading.Lock()
        # True once bind() has been called in on_mount.  We treat the TUI as
        # active as soon as it is bound (even before ``app.is_running`` flips)
        # so the very first loop output routes into the output pane.
        self._bound = False
        # Renderables queued before bind() attached the output pane.
        self._write_buffer: list = []
        # Persisted model name so it survives before the app is mounted
        # (the agent.status.ready handler can fire before on_mount completes).
        self._model_name: str | None = None

    # ── lifecycle ───────────────────────────────────────────────────────

    def bind(
        self,
        app: "TextualHarnessApp",
        output: "VerticalScroll",
        input: TextArea,
        spinner: StatusSpinner,
    ) -> None:
        """Attach a running app and its widgets (called from ``on_mount``)."""
        self._app = app
        self._output = output
        self._input = input
        self._spinner = spinner
        # Keep the spinner hidden until the agent is actually running.
        spinner.display = False
        self._bound = True
        # Replay anything queued before the output pane existed.
        with self._lock:
            buffered = self._write_buffer
            self._write_buffer = []
        for renderable in buffered:
            self.write_message(renderable)

    def is_active(self) -> bool:
        """Return ``True`` when the TUI app is bound and accepting I/O."""
        return self._bound and self._app is not None

    def write(self, renderable) -> None:
        """Render ``renderable`` into the output pane (thread-safe).

        """
        panel = MessageCard(
                title="a message",
                body=renderable,
                copy_text="some text",
        )
        self.write_message(panel)
        return 

        if self._app is None or self._output is None:
            # Buffer until bind() attaches the output pane.
            with self._lock:
                self._write_buffer.append(panel)
            return
        app = self._app
        output = self._output

        def _do() -> None:
            

            output.mount(panel)
            output.scroll_end(animate=False)
            with self._lock:
                self._write_count += 1

        self.run_on_app_thread(_do)

    def write_message(self, renderable) -> None:
        if self._app is None or self._output is None:
            # Buffer until bind() attaches the output pane.
            with self._lock:
                self._write_buffer.append(renderable)
            return
        app = self._app
        output = self._output

        def _do() -> None:
            
            output.mount(renderable)
            output.scroll_end(animate=False)
            with self._lock:
                self._write_count += 1

        self.run_on_app_thread(_do)



    def run_on_app_thread(self, fn) -> None:
        """Run ``fn`` on the Textual app thread, buffering if the app isn't live.

        The app's event loop must be running for widget mutation.  If the app is
        not yet active (bound but not running, or not bound yet), the call is
        buffered and replayed by :meth:`bind` once the output pane exists.
        """
        app = self._app
        if app is None:
            # No app bound yet — buffer; bind()/flush will replay.
            return
        app_thread = getattr(app, "_thread_id", None)
        if app_thread is not None and app_thread == threading.current_thread().ident:
            # Same thread as the app's loop: run directly, but inside the app
            # context so Textual's active_app ContextVar is set (required for
            # widget mount/compose — otherwise Collapsible/Markdown compose
            # raises NoActiveAppError).
            with app._context():
                fn()
        else:
            app.call_from_thread(fn)



    def scroll_output_to_bottom(self) -> None:
        """Scroll the output pane to the bottom (thread-safe).

        Used after ``ToolCallMessage.update_tool_result()`` populates
        the result area so the user sees it immediately.
        """
        if self._app is None or self._output is None:
            return
        output = self._output

        def _do() -> None:
            output.scroll_end(animate=False)

        self.run_on_app_thread(_do)

        """Number of times :meth:`write` committed to the output pane.

        Useful for tests that want to assert a render happened without poking
        at output-pane internals.
        """
        with self._lock:
            return self._write_count

    # ── sidebar usage (thread-safe, delegated to the running app) ───────

    def update_sidebar_usage(self, text: str | None) -> None:
        """Push the most recent usage summary to the right sidebar.

        Delegates to the running :class:`TextualHarnessApp`, which marshals the
        update onto the app thread.
        """
        if self._app is None:
            return
        self._app.update_sidebar_usage(text)

    def update_sidebar_tasks_from_payload(self, payload: TaskListPayload) -> None:
        """Push a TaskListPayload snapshot to the right sidebar (thread-safe).

        Delegates to the running :class:`TextualHarnessApp`, which marshals the
        update onto the app thread.
        """
        if self._app is None:
            return
        self._app.update_sidebar_tasks_from_payload(payload)

    def set_model_name(self, model_name: str | None) -> None:
        """Persist the agent's model name (survives before the app is mounted)."""
        self._model_name = model_name

    def get_model_name(self) -> str | None:
        """Return the persisted model name, or ``None`` if not yet known."""
        return self._model_name

    def update_sidebar_model_name(self, text: str | None) -> None:
        """Push the model name to the right sidebar widget (thread-safe).

        Persists the value on the controller so it survives the race where the
        agent.status.ready handler fires before on_mount binds the app (when
        ``self._app`` is still ``None``). If the app is already bound, the
        update is also delegated to :class:`TextualHarnessApp`, which updates and
        re-renders the sidebar widget.
        """
        # Persist before the guard: the app may not be bound yet, but the model
        # name must not be lost. on_mount seeds the sidebar from here.
        self.set_model_name(text)
        if self._app is None:
            return
        self._app.update_sidebar_model_name(text)

    # ── agent busy indicator (used by user_loop around handle_prompt) ────

    def show_spinner(self) -> None:
        """Reveal the spinner so the user knows the agent is working."""
        if self._spinner is not None:
            self._spinner.display = True

    def hide_spinner(self) -> None:
        """Hide the spinner once the agent has produced its response."""
        if self._spinner is not None:
            self._spinner.display = False

    # ── user input events ───────────────────────────────────────────────

    def publish_user_input(self, message: str) -> None:
        """Publish user input as an event instead of blocking.

        Called from the TUI when the user submits text via the input widget.
        This replaces the old prompt()/submit() blocking pattern with an
        event-driven approach that notifies subscribed agents.

        Args:
            message: The user's submitted text content.
        """
        from .event_publisher import get_tui_publisher

        publisher = get_tui_publisher()
        if publisher is not None:
            publisher.publish_user_input(message)

    def reset(self) -> None:
        """Detach the app (called on shutdown)."""
        self._app = None
        self._input = None
        self._output = None
        self._spinner = None
        self._bound = False


# Module-level controller singleton.
_tui = HarnessTUI()


def get_tui() -> HarnessTUI:
    """Return the process-wide :class:`HarnessTUI` controller."""
    return _tui
