"""TaskList — cache-friendly state machine for tracking agent execution.

This module provides a robust TaskList class that manages the lifecycle of
execution tasks within an LLM agent's context window. It is designed to be
cache-friendly by keeping all dynamic state in a structured format that can be
injected into message payloads without modifying the static system prompt.

Each Agent instance maintains its own TaskList for independent task tracking,
enabling multiple agents to operate concurrently without shared state conflicts.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from harness_core.eventbus import Event, event_bus, generate_unique_id
from harness_core.event_types import TaskListPayload


# Valid status values for task lifecycle management
VALID_STATUSES = ("pending", "in_progress", "completed", "failed")


@dataclass
class Task:
    """Represents a single executable task within the agent's workflow."""

    id: int
    description: str
    status: str = "pending"

    def __post_init__(self):
        """Validate that status is one of the allowed values."""
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

    def to_json(self) -> dict:
        """Serialize this task to a JSON-compatible dictionary with explicit ID."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
        }

    @property
    def is_active(self) -> bool:
        """Return True if the task is pending or in_progress."""
        return self.status in ("pending", "in_progress")


@dataclass
class NextTaskInfo:
    """Information about the next uncompleted task, returned by update_status.

    Used to guide agents toward the correct (1-indexed) task ID and to signal
    when all tasks are complete so the caller can clear the list.
    """

    has_next: bool = False          # True if there is still a pending/in_progress task
    id: int | None = None        # The next uncompleted task's ID (1-indexed)
    description: str = ""           # Description of that task
    status: str = ""                # Its current status
    all_complete: bool = False      # True when every task is completed or failed
    message: str = ""               # Human-readable summary


class TaskList:
    """Manages a collection of tasks and their lifecycle states.

    This class provides methods to initialize, update, and query the state
    of multiple tasks. It's designed for concurrent agent environments where
    each Agent instance holds its own independent TaskList.
    """

    def __init__(self, id: str | None = None, sender_id: str | None = None):
        """Initialize an empty TaskList instance.

        Args:
            id: Optional identifier. If provided, the TaskList's id is set to
                ``f"TaskList.{id}"`` (saved to ``self`` with the ``TaskList.``
                prefix). If None, a unique id is generated.
            sender_id: Optional id used as the event ``sender`` when this
                TaskList publishes events. Normally this is the owning agent's
                id (e.g. ``Agent.main``). If None, defaults to ``self.id``.
        """
        if id is not None:
            self.id = f"TaskList.{id}"
        else:
            self.id = "TaskList." + generate_unique_id()
        self._sender_id = sender_id if sender_id is not None else self.id
        self.tasks: list[Task] = []

    # -- event emission ----------------------------------------------------

    def _emit(self, topic: str) -> None:
        """Publish a tasklist event synchronously via the event bus.

        ``EventBus.publish`` is a plain synchronous call (no ``await`` and no
        requirement for a running event loop — it delivers directly via
        ``asyncio.Queue.put_nowait`` or ``loop.call_soon_threadsafe``). Therefore
        emission now happens inline on the calling thread, with no prior
        running-loop guard.

        When there are no subscribers bound to ``topic`` (including non-async
        contexts such as unit tests where nothing is registered), ``publish``
        returns immediately without raising — emission degrades gracefully and
        is effectively skipped.
        """

        event_bus.publish(
            Event(topic=topic, sender=self._sender_id, payload=TaskListPayload.from_task_list(self))
        )

    # -- initialization ----------------------------------------------------

    def initialize_tasks(self, tasks: list[str]) -> None:
        """Clear existing tasks and populate with a new list.

        Raises ValueError if there are currently incomplete (pending/in_progress)
        tasks remaining. Call :meth:`reset` to clear the list before re-initializing
        in that case.

        Args:
            tasks: A list of task description strings. Each string becomes
                   the description for a new Task object with auto-incremented
                   IDs starting from 1 and status set to "pending".

        Raises:
            ValueError: If any task description is empty or None,
                        or if there are incomplete tasks in the current list.
        """
        if not tasks:
            raise ValueError("Task list cannot be empty")

        # Guard against overwriting an unfinished task list silently
        if self.tasks and any(t.is_active for t in self.tasks):
            incomplete_ids = [t.id for t in self.tasks if t.is_active]
            raise ValueError(
                f"Cannot initialize: {len(incomplete_ids)} task(s) still incomplete "
                f"(IDs: {', '.join(map(str, incomplete_ids))}). Call reset() first, or complete all tasks."
            )

        self.tasks = []
        for i, desc in enumerate(tasks, start=1):
            if not desc or not desc.strip():
                raise ValueError(f"Task {i} description cannot be empty")
            self.tasks.append(Task(
                id=i,
                description=desc.strip(),
                status="pending",
            ))

        self._emit("agent.tasklist.initialize")

    def reset(self) -> None:
        """Clear all tasks from the list. Called internally when completion is detected."""
        self.tasks = []
        self._emit("agent.tasklist.reset")

    # -- status update -----------------------------------------------------

    def update_status(self, task_id: int, status: str) -> tuple[bool, NextTaskInfo]:
        """Update the status of a specific task.

        Args:
            task_id: The unique identifier of the task to update (1-indexed).
            status: The new status value (must be one of VALID_STATUSES).

        Returns:
            A tuple ``(success, next_task_info)`` where ``success`` is True if the
            task was found and updated, and ``next_task_info`` describes what tasks
            remain.  ``next_task_info`` always points agents toward the next ID to act on.

        Raises:
            ValueError: If the provided status is not in VALID_STATUSES.
        """
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                info = self._build_next_task_info()
                self._emit("agent.tasklist.update")
                return True, info

        # Task not found — still return info about remaining tasks so the caller knows
        info = self._build_next_task_info()
        self._emit("agent.tasklist.update")
        return False, info

    def _build_next_task_info(self) -> NextTaskInfo:
        """Build a NextTaskInfo describing the current state of remaining work."""
        info = NextTaskInfo()
        next_t = self.next_uncompleted_task()
        if next_t is not None:
            info.has_next = True
            info.id = next_t.id
            info.description = next_t.description
            info.status = next_t.status
            return info

        # All tasks are done (completed or failed)
        info.all_complete = len(self.tasks) > 0
        if info.all_complete:
            info.message = "All tasks have been completed or failed."
        else:
            info.message = "No tasks in list."
        return info

    # -- queries -----------------------------------------------------------

    def has_incomplete_tasks(self) -> bool:
        """Check if there are any tasks that haven't been completed or failed.

        Kept as a thin wrapper around ``not self.all_complete()`` plus an empty-list
        guard, for callers (e.g. the core loop terminator) that only need the boolean.
        """
        return not (len(self.tasks) == 0 or self.all_complete())

    def all_complete(self) -> bool:
        """Return True if every task is completed or failed (no pending/in_progress remain)."""
        return len(self.tasks) > 0 and not any(t.is_active for t in self.tasks)

    def next_uncompleted_task(self) -> Task | None:
        """Return the first task that is still pending or in_progress, or None."""
        for task in self.tasks:
            if task.is_active:
                return task
        return None

    # -- formatting (JSON) -------------------------------------------------

    def to_json_list(self) -> list[dict]:
        """Render the full task list as a list of JSON-compatible dicts with explicit IDs."""
        return [t.to_json() for t in self.tasks]

    def to_markdown(self) -> str:
        """Render the current task list state as a formatted markdown string.

        Deprecated: prefer the view function
        :func:`harness_core.terminal_io.task_display.render_task_list_markdown`,
        which keeps markdown rendering (the View) separate from this model. This
        method is retained only because the test suite still exercises it.

        The output is designed to be injected directly into LLM message payloads
        with clear visual delimiters and status indicators using checkbox syntax:
        - [x] for completed tasks (checkmark)
        - [*] for in-progress tasks (with CURRENT marker)
        - [ ] for pending tasks (empty checkbox)
        - [!] for failed tasks (exclamation mark, italic FAILED label)

        Returns:
            A string containing the formatted task list ready for context injection.
        """
        from harness_core.terminal_io.task_display import render_task_list_markdown

        return render_task_list_markdown(self)
