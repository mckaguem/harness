from textual.widgets import Collapsible, Static
from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Collapsible
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.rule import Rule

from .widgets import MessageCard


class UserMessage(Widget):
    """
    Displays a user's, with copy-on-click.
    """

    DEFAULT_CSS ="""
    UserMessage {
        margin: 0 0 0 0;
        padding: 0 0;
        height: auto
    }

    UserMessage > MessageCard {
        border: solid cyan;
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message: str = message

    def compose(self) -> ComposeResult:
        yield MessageCard(
                    title="User input",
                    body=Static(Markdown(self.message)),
                    copy_text=self.message
        )

class ReasoningMessage(Widget):
    """
    Displays reasoning trace in a Collapsible element, with copy-on-click once opened.
    """

    DEFAULT_CSS ="""
    ReasoningMessage {
        margin: 0 0 0 0;
        padding: 0 0;
        height: auto
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message: str = message

    def compose(self) -> ComposeResult:
        yield Collapsible(
                MessageCard(
                    title="Thinking",
                    body=Static(Markdown(self.message)),
                    copy_text=self.message
                ),
                title='Thinking'
        )

class AgentResponseMessage(Widget):
    """
    Displays an agent's response, with copy-on-click.
    """

    DEFAULT_CSS ="""
    AgentResponseMessage {
        margin: 0 0 0 0;
        padding: 0 0;
        height: auto
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message: str = message

    def compose(self) -> ComposeResult:
        yield MessageCard(
            title="Agent response",
            body=Static(Markdown(self.message)),
            copy_text=self.message
        )


class ErrorMessage(Widget):
    """Displays an error message in a red-bordered MessageCard."""

    DEFAULT_CSS = """
    ErrorMessage {
        margin: 0 0 0 0;
        padding: 0 0;
        height: auto
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message: str = message

    def compose(self) -> ComposeResult:
        yield MessageCard(
            title="Error",
            body=Static(f"[red]{self.message}[/red]"),
            copy_text=self.message
        )


class ToolCallMessage(Widget):
    """ToolCallMessage owns both its tool-call args display and its result area.

    ``display.py`` just creates this widget -- no legacy ``display_message_panel``
    stitching is needed. The three-part layout (args / separator / result) composes
    directly; the result slot is populated later via :meth:`update_tool_result`.

    Structure:
      Static(Markdown(tool_call_text))   -- args rendered as markdown
      Rule()                              -- horizontal rule separator
      Static(result)                      -- Markdown or Syntax, populated via update_tool_result()
    """

    DEFAULT_CSS = """
    ToolCallMessage {
        margin: 0 0 0 0;
        padding: 0 0;
        height: auto
    }
    """

    def __init__(self, title: str, tool_call_text: str, *, summary: str = ""):
        super().__init__()
        self._title = title
        self._tool_call_text = tool_call_text
        self._summary = summary or ""
        # Placeholder for result — populated later via update_tool_result().
        self._result_static: Widget | None = None

    @property
    def title(self) -> str:
        return self._title

    def compose(self) -> ComposeResult:
        """Yield the three-part layout wrapped in a Collapsible."""
        # Create the result placeholder BEFORE yielding, so we hold a reference.
        self._result_static = Static("")  # empty until update_tool_result() is called
        content_layout = Vertical(
            Static(Markdown(self._tool_call_text)),
            Static(Rule(style="dim")),
            self._result_static,
        )
        yield Collapsible(content_layout, title=f"Tool: {self._summary}")

    def update_tool_result(self, text: str, type_tag: str = "text") -> None:
        """Populate the tool call's result area with given text.

        If ``type_tag == "markdown"`` renders as Markdown; otherwise uses 
        Syntax highlighting with the given language tag (defaulting to "text").
        """
        if self._result_static is not None:
            if type_tag == "markdown":
                # Use Markdown rendering for markdown-type results.
                self._result_static.update(Markdown(text))
            else:
                # Use Syntax highlighting for code/json/text results.
                self._result_static.update(Syntax(text, type_tag or "text", theme="monokai"))
