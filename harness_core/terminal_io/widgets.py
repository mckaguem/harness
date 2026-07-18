"""Reusable Textual widgets for the harness TUI."""
from __future__ import annotations

from rich.text import Text
from rich.markdown import Markdown
from rich.console import Group
from rich.rule import Rule
from textual.widgets import Static

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

    def _get_model_name(self) -> str | None:
        """Return the model name from the agent's config, or None if unavailable."""
        if self._agent is None:
            return None
        try:
            model_name = getattr(getattr(self._agent, '_agent_type', None), 'model_name', '') or ''
            return model_name if model_name else None
        except Exception:
            return None

    def refresh_tasks(self) -> None:
        """Re-render the sidebar.

        The usage summary (if set) is always shown at the top, above the task
        list.  The task list renders below it whenever one exists (even when
        empty after completion); if no task list is available yet, only the
        usage block is shown.
        """
        model_name = self._get_model_name()
        model_render = None
        if model_name:
            model_render = Group(Text("🤖 Model", style="bold"), Text(model_name), Rule())

        usage_render = None
        if self._usage_text:
            # Render on two lines: the speed line, then the (optional) turn
            # line, so it does not wrap awkwardly in the narrow sidebar.
            sub = self._usage_text.split("\n")
            lines = [Text.from_markup(part) for part in sub if part]
            usage_render = Group(Text("📊 Usage", style="bold"), *lines, Rule())

        header = None
        if model_render is not None and usage_render is not None:
            header = Group(model_render, usage_render)
        elif model_render is not None:
            header = model_render
        elif usage_render is not None:
            header = usage_render

        if self._agent is None or self._agent.task_list is None:
            # No task list available yet — show usage only (or a placeholder).
            self.update(header if header is not None else Markdown("_No tasks yet._"))
            return

        tasks = self._agent.task_list
        if not tasks.tasks:
            body = Markdown("_No tasks yet._")
        else:
            body = Markdown(render_task_list_markdown(tasks))

        if header is not None:
            self.update(Group(header, body))
        else:
            self.update(body)

    def refresh_tasks_from_payload(self, payload: TaskListPayload) -> None:
        """Re-render the task list from a TaskListPayload (event-driven).

        Mirrors :meth:`refresh_tasks` but sources the task rows from an event
        payload rather than the agent's live TaskList, so sidebar updates can be
        driven directly by the TaskList EventBus.
        """
        model_name = self._get_model_name()
        model_render = None
        if model_name:
            model_render = Group(Text("🤖 Model", style="bold"), Text(model_name), Rule())

        usage_render = None
        if self._usage_text:
            sub = self._usage_text.split("\n")
            lines = [Text.from_markup(part) for part in sub if part]
            usage_render = Group(Text("📊 Usage", style="bold"), *lines, Rule())

        header = None
        if model_render is not None and usage_render is not None:
            header = Group(model_render, usage_render)
        elif model_render is not None:
            header = model_render
        elif usage_render is not None:
            header = usage_render

        if not payload.tasks:
            body = Markdown("_No tasks yet._")
        else:
            body = Markdown(render_task_list_markdown_from_payload(payload))

        if header is not None:
            self.update(Group(header, body))
        else:
            self.update(body)
