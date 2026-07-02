"""ToolResult — structured return value for tools with display metadata."""

from dataclasses import dataclass


@dataclass
class ToolResult:
    """Structured result from a tool call.

    Separates what is sent back to the LLM from what is rendered in the
    user-visible panel, and carries styling hints (theme, title) so the
    display layer can render them consistently without each tool knowing
    about Rich or console specifics.

    Attributes:
        llm_text:
            The text sent back to the agent as its tool response. This is
            what the LLM sees — it should be machine-friendly (concise,
            structured, unambiguous).
        display_text:
            The human-friendly representation rendered in the Rich panel on
            screen. May differ from ``llm_text`` when a more readable format
            (e.g., markdown) is appropriate for humans but not needed by the
            LLM.
        type_tag:
            A hint used by the display layer to choose syntax highlighting,
            e.g. ``"markdown"``, ``"json"``, ``"diff"``, ``"text"``.
        title:
            Custom panel title (including any icon character), e.g.
            ``"📋 Task List"``.  If empty the display layer falls back to a
            function-name-derived default.
        theme:
            One of ``"error"``, ``"status"``, ``"read"``, ``"write"``,
            ``"command"`` — selects the panel border color and overall style.
    """

    llm_text: str
    display_text: str
    type_tag: str = "text"
    title: str = ""
    theme: str = "status"


__all__ = ["ToolResult"]
