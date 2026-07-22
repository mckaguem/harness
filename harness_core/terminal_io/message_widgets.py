
from textual.widgets import Collapsible, Static
from textual.widget import Widget
from textual.app import ComposeResult
from rich.markdown import Markdown

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

