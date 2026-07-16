"""Textual-based terminal UI for the harness.

This module provides an idiomatic :mod:`textual` application for interactive
sessions.

* :class:`TextualHarnessApp` is a small, composable app: a header, a
  :class:`~textual.containers.VerticalScroll` output pane (a scrollable column
  of :class:`~textual.widgets.Static` wrappers — and, for tool calls,
  :class:`~textual.widgets.Collapsible` widgets whose result is rendered inline
  inside them), a multi-line :class:`~textual.widgets.TextArea` input, and a
  footer.
* :class:`HarnessTUI` is a controller singleton that owns the running app
  instance and exposes thread-safe ``write``/``prompt`` operations.

The interactive loop itself still lives in :func:`agent.loop.user_loop`; the
TUI simply runs it on a worker thread and routes all I/O through the
controller.
"""

from __future__ import annotations

import asyncio
import threading

from rich.panel import Panel
from textual.app import App
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Collapsible, Static, TextArea
from rich.console import Group
from rich.rule import Rule
from rich.text import Text
from rich.markdown import Markdown

from harness_core.event_types import TaskListPayload
from harness_core.terminal_io.task_display import (
    render_task_list_markdown,
    render_task_list_markdown_from_payload,
)


# Inline separator rendered between a tool call and its result inside a
# Collapsible widget.  Defined locally (rather than imported from display.py)
# to avoid a circular import.
TOOL_SEPARATOR = Rule(style="dim")


class StatusSpinner(Static):
    """A non-blocking animated "thinking" indicator for the message panel.

    Unlike Textual's built-in :class:`~textual.widgets.LoadingIndicator` this
    widget does *not* swallow input events, so the user's ``TextArea`` stays
    fully interactive while the agent is working.  It is docked to the bottom
    of the messages panel and simply cycles through a small set of glyphs.
    """

    # Frames for the animation (braille spinner + a trailing "thinking" hint).
    FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
    LABEL = "agent is thinking"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._frame_index = 0
        # 16 fps keeps the animation smooth without saturating the message pump.
        self.auto_refresh = 1 / 16

    def render(self) -> Text:
        glyph = self.FRAMES[self._frame_index % len(self.FRAMES)]
        self._frame_index += 1
        # Plain, unstyled text: ``Static`` (``markup=False``) would otherwise
        # try to resolve the ``[accent]``/``[dim]`` span styles through Rich's
        # color parser, which does not understand Textual theme variables and
        # raises ``MissingStyle``.  The widget's own ``color`` CSS paints it.
        return Text(f"{glyph} {self.LABEL}\u2026")


class TaskListSidebar(Static):
    """A right-hand panel that renders the main agent's task list.

    Its content is refreshed from the agent's :class:`~harness_core.agent.task_list.TaskList`
    via :meth:`refresh_tasks`, which is normally driven by a change listener on the
    TaskList so it stays in sync with every ``initialize_task_list`` / ``update_task_status``
    tool call.  A periodic interval keeps it correct even if the listener is missed.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._agent = None
        self._usage_text: str | None = None

    def set_agent(self, agent) -> None:
        """Provide the agent whose task list should be displayed."""
        self._agent = agent

    def set_usage(self, text: str | None) -> None:
        """Store the most recent LLM usage summary to render above the tasks.

        ``text`` is the ``format_speed`` summary string (or ``None`` to clear).
        It is rendered on the next :meth:`refresh_tasks`.
        """
        self._usage_text = text

    def refresh_tasks(self) -> None:
        """Re-render the sidebar.

        The usage summary (if set) is always shown at the top, above the task
        list.  The task list renders below it whenever one exists (even when
        empty after completion); if no task list is available yet, only the
        usage block is shown.
        """
        usage_render = None
        if self._usage_text:
            # Render on two lines: the speed line, then the (optional) turn
            # line, so it does not wrap awkwardly in the narrow sidebar.
            sub = self._usage_text.split("\n")
            lines = [Text.from_markup(part) for part in sub if part]
            usage_render = Group(Text("📊 Usage", style="bold"), *lines, Rule())

        if self._agent is None or self._agent.task_list is None:
            # No task list available yet — show usage only (or a placeholder).
            self.update(usage_render if usage_render is not None else Markdown("_No tasks yet._"))
            return

        tasks = self._agent.task_list
        if not tasks.tasks:
            body = Markdown("_No tasks yet._")
        else:
            body = Markdown(render_task_list_markdown(tasks))

        if usage_render is not None:
            self.update(Group(usage_render, body))
        else:
            self.update(body)

    def refresh_tasks_from_payload(self, payload: TaskListPayload) -> None:
        """Re-render the task list from a TaskListPayload (event-driven).

        Mirrors :meth:`refresh_tasks` but sources the task rows from an event
        payload rather than the agent's live TaskList, so sidebar updates can be
        driven directly by the TaskList EventBus.
        """
        usage_render = None
        if self._usage_text:
            sub = self._usage_text.split("\n")
            lines = [Text.from_markup(part) for part in sub if part]
            usage_render = Group(Text("📊 Usage", style="bold"), *lines, Rule())

        if not payload.tasks:
            body = Markdown("_No tasks yet._")
        else:
            body = Markdown(render_task_list_markdown_from_payload(payload))

        if usage_render is not None:
            self.update(Group(usage_render, body))
        else:
            self.update(body)


class HarnessTUI:
    """Controller singleton for the Textual TUI.

    The app runs on the main thread while :func:`agent.loop.user_loop` runs on
    a worker thread.  Widget mutation must therefore only happen on the app
    thread; every operation here funnels through ``app.call_from_thread`` so it
    is safe to call from the loop thread.
    """

    def __init__(self) -> None:
        self._app: "TextualHarnessApp" | None = None
        # Guarded by ``_lock``; only touched from the app thread.
        self._input: TextArea | None = None
        self._output: VerticalScroll | None = None
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

    def bind(self, app: "TextualHarnessApp", output: VerticalScroll, input: TextArea, spinner: "StatusSpinner") -> None:
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
            # No matching call on the stack (e.g. a stray result) \u2014 render
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
    import threading

    def show_spinner(self) -> None:
        """Reveal the spinner so the user knows the agent is working.

        Thread-safe: the loop/worker thread may call this while the spinner
        widget lives on the app thread; the visibility change is marshalled
        through ``app.call_from_thread``. If called from the app thread
        directly, runs synchronously.
        """
        if self._spinner is None:
            return
        assert self._app is not None
        app = self._app

        def _do() -> None:
            assert self._spinner is not None
            self._spinner.display = True

        app_thread = getattr(app, "_thread_id", None)
        if app_thread is not None and app_thread == threading.current_thread().ident:
            _do()
        else:
            app.call_from_thread(_do)

    def hide_spinner(self) -> None:
        """Hide the spinner once the agent has produced its response.

        Thread-safe (see :meth:`show_spinner`).
        """
        if self._spinner is None:
            return
        assert self._app is not None
        app = self._app

        def _do() -> None:
            assert self._spinner is not None
            self._spinner.display = False

        app_thread = getattr(app, "_thread_id", None)
        if app_thread is not None and app_thread == threading.current_thread().ident:
            _do()
        else:
            app.call_from_thread(_do)

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

    def compose(self) -> "ComposeResult":  # type: ignore[name-defined]
        from textual.app import ComposeResult

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
        controller = get_tui()
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
                from harness_core.agent.loop import user_loop

                user_loop(self._agent, on_exit=self._on_exit)
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
        get_tui().submit()


def launch(agent, on_exit=None) -> None:
    """Launch the Textual TUI and drive ``user_loop`` on a worker thread.

    Args:
        agent: An initialized :class:`~agent.core.Agent` instance.
        on_exit: Optional callback invoked when the loop ends (see
            :func:`agent.loop.user_loop`).
    """
    app = TextualHarnessApp(agent=agent, on_exit=on_exit)
    app.run()
