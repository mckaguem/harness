"""Reusable Textual widgets for the harness TUI."""
from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Button, Static
from textual.events import Click
from rich.text import Text
from rich.markdown import Markdown
from rich.console import Group
from rich.rule import Rule
from textual.app import ComposeResult
from rich.console import RenderableType

from harness_core.event_types import TaskListPayload
from harness_core.terminal_io.task_display import render_task_list_markdown_from_payload

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
        self._model_name: str | None = None
        self._usage_text: str | None = None
        self.tasklist: str = '_No tasks yet_'

    def set_model_name(self, text: str | None) -> None:
        """Store the model name to display in the sidebar header."""
        self._model_name = text

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
        model_render = Group(
            Text("🤖 Model", style="bold"), 
            Text(self._model_name if self._model_name else "-"), 
            Rule())

        if self._usage_text:
            sub = self._usage_text.split("\n")
            lines = [Text.from_markup(part) for part in sub if part]
        else: 
            lines = [Text('-')]
        usage_render = Group(Text("📊 Usage", style="bold"), *lines, Rule())
        tasks_render = Markdown(self.tasklist)
        self.update(Group(model_render, usage_render, tasks_render))


    def refresh_tasks_from_payload(self, payload: TaskListPayload) -> None:
        """Re-render the task list from a TaskListPayload (event-driven).

        Mirrors :meth:`refresh_tasks` but sources the task rows from an event
        payload rather than the agent's live TaskList, so sidebar updates can be
        driven directly by the TaskList EventBus.
        """

        if not payload.tasks:
            self.tasklist = "_No tasks yet._"
        else:
            self.tasklist = render_task_list_markdown_from_payload(payload)

        self.refresh_tasks()

class MessageCard(Widget):
    """A reusable card for conversation messages.

    Features:
      - Title
      - Variant-based styling
      - Copy button
      - Arbitrary body widget
    """

    DEFAULT_CSS = """
    MessageCard {
        border: solid $surface;
        margin: 0 0 0 0;
        padding: 0 0;
        height: auto;
    }

    MessageCard {
    transition: background 150ms;
    }

    MessageCard > Static {
       background: transparent;
    }

    MessageCard:hover {
        border: white;
    }
    """

    def __init__(
        self,
        *,
        title: str,
        body: Widget | RenderableType,
        copy_text: str | None = "Something default",
    ) -> None:
        super().__init__()

        self.title = title
        if isinstance(body, Widget):
            self.body = body
        else:
            self.body = Static(body)

        self.copy_text = copy_text

    def compose(self) -> ComposeResult:

        yield self.body

    async def on_click(self, event: Click) -> None:
        await self.copy()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy":
            await self.copy()

    async def copy(self) -> None:
        if self.copy_text is None:
            return

        self.app.copy_to_clipboard(self.copy_text)
        self.app.notify("Copied to clipboard")
