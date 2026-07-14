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
class ToolErrorPayload(EventPayload):
    """Event payload for an error reported by a tool call.

    Carries a ``title`` (short identifier, e.g. "Tool Error") and a longer
    ``message`` body describing what went wrong. Mirrors the signature of
    :func:`harness_core.terminal_io.display.print_system` so that subscribers
    can render it through the existing ``display_error`` helper.

    Attributes:
        title: Short error title (e.g. "Tool Error"). Defaults to "Tool Error".
        message: Human-readable description of the tool-related failure.
    """

    title: str = "Tool Error"
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