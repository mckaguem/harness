"""Event payload types for the Harness event system.

This module defines base classes and concrete payload types used for
structured event data passed through the event bus. Using typed payloads
enables better IDE support, runtime validation, and clearer APIs.
"""

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from harness_core.agent.task_list import TaskList


@dataclass(kw_only=True)
class EventPayload:
    """Base class for all event payloads.

    This class provides a common base for typed event payloads that can be
    passed through the event bus. Subclasses should define their own fields
    to represent the specific data for each event type.

    Using `kw_only=True` allows subclasses to define required fields without
    default values while still having optional fields with defaults in the base.

    Example:
        @dataclass(kw_only=True)
        class MyEventPayload(EventPayload):
            message: str
            count: int = 0
    """

    # Optional metadata that can be attached to any event
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the payload to a dictionary for serialization.

        Returns:
            A dictionary representation of the payload including all fields.
        """
        # Use dataclasses.asdict for proper conversion
        from dataclasses import asdict

        return asdict(self)


@dataclass
class TaskInfo:
    """Represents a single task with its status information.

    This is a lightweight, serializable representation of a task that can
    be included in event payloads without carrying the full Task object.
    """

    id: int
    description: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
        }


@dataclass(kw_only=True)
class TaskListPayload(EventPayload):
    """Event payload containing a complete task list snapshot.

    This payload is emitted when the task list changes, providing subscribers
    with the full current state of all tasks. It's designed to be lightweight
    and serializable for use across process boundaries or in logs.

    Attributes:
        tasks: List of TaskInfo objects representing each task's current state.
        total_tasks: Total number of tasks in the list.
        completed_tasks: Number of tasks with status 'completed' or 'failed'.
        has_incomplete: Whether there are any pending or in_progress tasks.
    """

    tasks: list[TaskInfo] = field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    has_incomplete: bool = False

    @classmethod
    def from_task_list(cls, task_list: "TaskList") -> "TaskListPayload":
        """Create a TaskListPayload from a TaskList instance.

        This factory method extracts the relevant state from a TaskList
        and creates a serializable payload suitable for event emission.

        Args:
            task_list: The TaskList instance to convert.

        Returns:
            A new TaskListPayload containing the task list's current state.
        """
        task_infos = [
            TaskInfo(
                id=task.id,
                description=task.description,
                status=task.status,
            )
            for task in task_list.tasks
        ]

        total = len(task_infos)
        completed = sum(1 for t in task_infos if t.status in ("completed", "failed"))
        has_incomplete = any(t.status in ("pending", "in_progress") for t in task_infos)

        return cls(
            tasks=task_infos,
            total_tasks=total,
            completed_tasks=completed,
            has_incomplete=has_incomplete,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the payload to a dictionary for serialization.

        Returns:
            A dictionary representation with tasks converted to dicts.
        """
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "has_incomplete": self.has_incomplete,
            "metadata": self.metadata,
        }


@dataclass(kw_only=True)
class SystemMessagePayload(EventPayload):
    """Event payload for a system-level status/notification message.

    Carries a short ``title`` and a longer ``message`` body, suitable for
    rendering as a system panel (e.g. an "Agent Ready" banner or an
    "Auto-Compression" notice). Mirrors the signature of
    :func:`harness_core.terminal_io.display.print_system`.
    """

    title: str = ""
    message: str = ""


@dataclass(kw_only=True)
class SessionErrorPayload(EventPayload):
    """Event payload for an error reported at session level (e.g. auto-compression).

    Carries a ``title`` and a longer ``message`` body. Mirrors the signature of
    :func:`harness_core.terminal_io.display.print_system` so that subscribers
    can render it through the existing ``display_error`` helper.

    Attributes:
        title: Short error title (e.g. "Auto-Compression Error"). Defaults to
            "Auto-Compression Error".
        message: Human-readable description of the session-level failure.
    """

    title: str = "Auto-Compression Error"
    message: str = ""


@dataclass(kw_only=True)
class AgentResponsePayload(EventPayload):
    """Event payload for an agent turn response (the LLM's text reply).

    Carries everything needed to render a single ``display_agent_response`` call.
    Subscribers reconstruct the display by forwarding all fields back through
    :func:`harness_core.terminal_io.display.display_agent_response`.

    Attributes:
        content: The raw agent response text (may be empty string).
        response: Additional metadata dict from the provider (e.g. token usage),
            or ``None`` when absent.
        context_length: Length of the model's context window used for the call.
        reasoning: Chain-of-thought / reasoning text, or ``None`` if not present.
    """

    content: str = ""
    response: dict | None = None
    context_length: int = 0
    reasoning: str | None = None

@dataclass(kw_only=True)
class TurnStatsPayload(EventPayload):
    """Event payload for post-turn usage + elapsed-time stats pushed to the sidebar.

    Carries everything needed to render a single ``display_turn_stats`` call.
    Subscribers reconstruct the display by forwarding all fields back through
    :func:`harness_core.terminal_io.display.display_turn_stats`.

    Attributes:
        response: The raw LLM response dict (usage, eval counts, etc.), or None when absent.
        context_length: Length of the model's context window used for the call.
        elapsed_seconds: Wall-clock time spent on the turn in seconds, or None if not tracked.
    """

    response: dict | None = None
    context_length: int = 0
    elapsed_seconds: float | None = None


@dataclass(kw_only=True)
class ToolCallPayload(EventPayload):
    """Event payload for an in-progress tool call.

    Carries everything needed to render a single ``display_tool_call`` invocation.
    Subscribers reconstruct the display by forwarding all fields back through
    :func:`harness_core.terminal_io.display.display_tool_call`.

    Attributes:
        func_name: Name of the tool being called (e.g. "read_file").
        args_str: JSON-encoded arguments string passed to the tool.
        summary: Optional panel title override; if None, display falls back
            to ``"Tool: <func_name>"``.
        pre_content: Agent text said *before* the tool call, rendered in an
            "Agent" panel above the tool-call panel. Defaults to empty string.
        reasoning: Chain-of-thought / reasoning to prepend (above a "---")
            before ``pre_content``. Optional.
    """

    func_name: str = ""
    args_str: str = ""
    summary: str | None = None
    pre_content: str = ""
    reasoning: str | None = None


@dataclass(kw_only=True)
class ToolResultPayload(EventPayload):
    """Event payload for a tool result.

    Carries everything needed to render a single ``display_tool_result`` invocation.
    Subscribers reconstruct the display by forwarding all fields back through
    :func:`harness_core.terminal_io.display.display_tool_result`.

    Attributes:
        func_name: Name of the tool that produced the result (used as fallback title).
        result_title: Title override from the ToolResult object, or None.
        result_display_text: The display text content of the ToolResult.
        result_theme: Color/theme string for rendering (e.g. "info", "error").
        result_type_tag: Type tag from the ToolResult, defaults to "text".
    """

    func_name: str = ""
    result_title: str | None = None
    result_display_text: str = ""
    result_theme: str = "info"
    result_type_tag: str = "text"


@dataclass(kw_only=True)
class ToolErrorPayload(EventPayload):
    """Event payload for a tool-call error.

    Carries everything needed to render a single ``display_error`` invocation
    triggered by an ERROR kind output from agent.handle_prompt(). Subscribers
    reconstruct the display by forwarding all fields back through
    :func:`harness_core.terminal_io.display.display_error`.

    Attributes:
        message: The error description text, or None if no message provided.
    """

    message: str = ""


@dataclass(kw_only=True)
class ControlPayload(EventPayload):
    """Event payload for control events (spinner start/stop, turn start/stop).

    These lightweight events control UI elements like the spinner in the TUI
    messages panel. They carry a generic action dictionary.

    Attributes:
        action: Dictionary describing the control action (e.g., {"type": "spinner.start"}).
    """

    action: dict[str, Any] | None = None