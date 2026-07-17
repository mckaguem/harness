"""HarnessTUI controller for the harness TUI."""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from rich.panel import Panel
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Static, TextArea
from rich.console import Group

from harness_core.event_types import TaskListPayload
from harness_core.terminal_io.widgets import (
    StatusSpinner,
    TaskListSidebar,
    TOOL_SEPARATOR,
)


if TYPE_CHECKING:
    from .tui_app import TextualHarnessApp


class HarnessTUI:
    """Controller singleton for the Textual TUI.

    The app runs on the main thread while :func:`agent.loop.user_loop` runs on
    a worker thread.  Widget mutation must therefore only happen on the app
    thread; every operation here funnels through ``app.call_from_thread`` so it
    is safe to call from the loop thread.
    """

    def __init__(self) -> None:
        self._app: TextualHarnessApp | None = None  # type: ignore[assignment]
        self._input: TextArea | None = None  # type: ignore[assignment]
        self._output: VerticalScroll | None = None  # type: ignore[assignment]
        self._spinner: StatusSpinner | None = None
        self._write_count = 0
        self._lock = threading.Lock()
        # Stack of ``(Collapsible, inner Static)`` pairs for in-flight tool
        # calls, each awaiting its matching result.  Pushed in begin_tool_panel(),
        # popped in complete_tool_panel().  Guarded by ``_lock``.
        self._tool_stack: list = []
        # True once bind() has been called in on_mount.  We treat the TUI as
        # active as soon as it is bound (even before ``app.is_running`` flips)
        # so the very first loop output routes into the output pane.
        self._bound = False

        # Pending prompt state.  The worker (loop) thread blocks on ``_pending``
        # while the app thread resolves it from the input widget.
        self._pending: threading.Event | None = None
        self._pending_value: str = ""
        self._pending_prompt: str | None = ""

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

    def is_active(self) -> bool:
        """Return ``True`` when the TUI app is bound and accepting I/O."""
        return self._bound and self._app is not None

    def write(self, renderable) -> None:
        """Render ``renderable`` into the output pane (thread-safe).

        The output pane is a Textual :class:`~textual.containers.VerticalScroll`
        of :class:`~textual.widgets.Static` wrappers (one per renderable).  This
        lets tool calls become :class:`~textual.widgets.Collapsible` widgets
        whose result can be appended *inside* them later, which a flat output
        log cannot do.
        """
        if self._app is None or self._output is None:
            return
        app = self._app
        output = self._output

        def _do() -> None:
            # ``call_from_thread`` already runs this on the app thread; mounting
            # synchronously here is correct and avoids races on the tool stack.
            output.mount(Static(renderable))
            output.scroll_end(animate=False)
            with self._lock:
                self._write_count += 1

        # When the caller is already on the app/Textual thread (e.g. an event
        # handler delivered inline by the event bus), calling ``call_from_thread``
        # itself raises RuntimeError (it must be a *different* thread).  In that
        # case mount synchronously here; otherwise marshal onto the app thread.
        app_thread = getattr(app, "_thread_id", None)
        if app_thread is not None and app_thread == threading.current_thread().ident:
            _do()
        else:
            app.call_from_thread(_do)

    def begin_tool_panel(self, title: str, call_renderable) -> None:
        """Create a collapsed-by-default ``Collapsible`` for a tool call.

        Called from :func:`terminal_io.display.display_tool_call`. The
        collapsible's title is the panel title (``"Tool: <name>"``), and its
        initial child is the tool-call renderable.  The widget is pushed onto
        ``_tool_stack`` so the matching :meth:`complete_tool_panel` (which is
        always emitted immediately after in the agent loop) can append the
        result into this same collapsible.
        """
        if self._app is None or self._output is None:
            return
        app = self._app
        output = self._output
        # `collapsed=True` so the call (and later the result) are invisible by
        # default; the user can click the title to see it.
        # The title bar is
        # itself a (CollapsibleTitle) Static, so the inner content Static gets
        # a stable id to disambiguate it later in complete_tool_panel().
        inner = Static(call_renderable, id="tool-content")
        collapsible = Collapsible(
            inner,
            title=title,
            collapsed=True,
        )
        with self._lock:
            # Stash the original call Panel so complete_tool_panel can rebuild
            # it with the inline result (call + separator + result) and swap it
            # into the same Collapsible without re-mounting the whole widget.
            self._tool_stack.append((collapsible, call_renderable))

        def _do() -> None:
            output.mount(collapsible)
            output.scroll_end(animate=False)

        # Marshal onto the app thread (widgets can only be mounted on the app thread).
        app_thread = getattr(app, "_thread_id", None)
        if app_thread is not None and app_thread == threading.current_thread().ident:
            _do()
        else:
            app.call_from_thread(_do)

    def complete_tool_panel(self, result_renderable) -> None:
        """Append a tool result into the most recent tool-call collapsible.

        Called from :func:`terminal_io.display.display_tool_result`.  Pops the
        most recent collapsible off ``_tool_stack`` and mounts the result
        renderable inside it, after a ``Rule`` separator, so the result is
        inline (not a separate panel).  Matches the stack-pop in
        ``begin_tool_panel`` because the agent loop always emits a TOOL_RESULT
        immediately after its TOOL_CALL.
        """
        if self._app is None or self._output is None:
            return
        app = self._app
        output = self._output
        with self._lock:
            entry = self._tool_stack.pop() if self._tool_stack else None
        collapsible = entry[0] if entry else None
        call_panel = entry[1] if entry else None

        if collapsible is None or call_panel is None:
            # No matching call on the stack (e.g. a stray result) — render
            # it as a standalone panel so it is not lost.
            def _do_standalone() -> None:
                output.mount(Static(result_renderable))
                output.scroll_end(animate=False)

            app_thread = getattr(app, "_thread_id", None)
            if app_thread is not None and app_thread == threading.current_thread().ident:
                _do_standalone()
            else:
                app.call_from_thread(_do_standalone)
            return
        # Rebuild the single call Panel to include the separator + result
        # inline, then swap it into the Collapsible via its inner content
        # Static (NOT the title bar — the title is also a Static, so we
        # target it by id).  Net effect: one Panel showing call + separator
        # + result, all nested inside the Collapsible.  The result must be
        # unwrapped (result.renderable) so we do not nest a second border
        # inside the call Panel.
        result_inner = (
            result_renderable.renderable
            if isinstance(result_renderable, Panel)
            else result_renderable
        )
        merged = Panel(
            Group(call_panel.renderable, TOOL_SEPARATOR, result_inner),
            title=call_panel.title,
            border_style=call_panel.border_style,
        )

        def _do_update() -> None:
            collapsible.query_one("#tool-content", Static).update(merged)
            output.scroll_end(animate=False)

        app_thread = getattr(app, "_thread_id", None)
        if app_thread is not None and app_thread == threading.current_thread().ident:
            _do_update()
        else:
            app.call_from_thread(_do_update)


    def write_count(self) -> int:
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

    # ── agent busy indicator (used by user_loop around handle_prompt) ────

    def show_spinner(self) -> None:
        """Reveal the spinner so the user knows the agent is working."""
        if self._spinner is not None:
            self._spinner.display = True

    def hide_spinner(self) -> None:
        """Hide the spinner once the agent has produced its response."""
        if self._spinner is not None:
            self._spinner.display = False

    # ── blocking prompt (used by prompt_user inside the TUI) ────────────

    def prompt(self, prompt_str: str = "") -> str:
        """Block the calling (loop) thread until the user submits input.

        Returns the assembled text (newlines preserved).  An empty submission
        returns ``""``.
        """
        # Import here to avoid circular import with display.py
        from harness_core.terminal_io.display import display_user_message

        if self._app is None:
            raise RuntimeError("HarnessTUI.prompt called while TUI is not bound")

        app = self._app
        event = threading.Event()
        with self._lock:
            self._pending = event
            self._pending_value = ""
            self._pending_prompt = prompt_str

        # Arm the input box on the app thread (it owns the live TextArea).
        def _arm() -> None:
            self._arm_input()

        app.call_from_thread(_arm)

        # Block the worker thread until the app thread resolves the event.
        event.wait()

        with self._lock:
            self._pending = None
            self._pending_prompt = None
            value = self._pending_value
        if value.strip():
            display_user_message(value)
        return value

    def _arm_input(self) -> None:
        """Focus + clear the input box. Called from the app thread only."""
        if self._input is None:
            return
        self._input.placeholder = self._pending_prompt or ""
        # Setting .text requires an active app; only valid on the app thread
        # while the widget is mounted, which is always the case here.
        self._input.text = ""
        self._input.focus()

    def submit(self) -> None:
        """Resolve a pending :meth:`prompt` with the current input text.

        Called from the app thread (e.g. the Ctrl+Enter key handler) where the
        ``TextArea`` is a live, mounted widget.  After capturing the text we
        immediately clear the box so the submitted content does not linger in
        the input for the rest of the turn; ``_arm_input`` also clears/focuses
        on the next prompt, but that only happens once the agent responds.
        """
        with self._lock:
            if self._pending is None or self._input is None:
                return
            input_widget = self._input
            self._pending_value = input_widget.text
            event = self._pending
        # Clear + refocus the box now (not when the next prompt arms) so it is
        # empty and ready for the user's next message immediately on submit.
        input_widget.text = ""
        input_widget.focus()
        event.set()

    def reset(self) -> None:
        """Detach the app (called on shutdown)."""
        self._app = None
        self._input = None
        self._output = None
        self._spinner = None
        self._pending = None
        self._pending_value = ""
        self._pending_prompt = ""
        self._bound = False
        self._tool_stack = []


# Module-level controller singleton.
_tui = HarnessTUI()


def get_tui() -> HarnessTUI:
    """Return the process-wide :class:`HarnessTUI` controller."""
    return _tui
