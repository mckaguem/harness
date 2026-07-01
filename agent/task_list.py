"""TaskList — cache-friendly state machine for tracking agent execution.

This module provides a robust TaskList class that manages the lifecycle of
execution tasks within an LLM agent's context window. It is designed to be
cache-friendly by keeping all dynamic state in a structured format that can be
injected into message payloads without modifying the static system prompt.

The TaskList uses a singleton pattern for easy access from tools and core
agent logic, ensuring consistent state across the application.
"""

from dataclasses import dataclass
from typing import List


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


class TaskList:
    """Manages a collection of tasks and their lifecycle states.
    
    This class provides methods to initialize, update, and query the state
    of multiple tasks. It's designed to be thread-safe for use in concurrent
    agent environments and maintains a clean interface for serialization
    to markdown format for LLM context injection.
    """
    
    def __init__(self):
        """Initialize an empty TaskList instance."""
        self.tasks: List[Task] = []
    
    def initialize_tasks(self, tasks: list[str]) -> None:
        """Clear existing tasks and populate with a new list.
        
        Args:
            tasks: A list of task description strings. Each string becomes
                   the description for a new Task object with auto-incremented
                   IDs starting from 1 and status set to "pending".
        
        Raises:
            ValueError: If any task description is empty or None.
        """
        if not tasks:
            raise ValueError("Task list cannot be empty")
        
        self.tasks = []
        for i, desc in enumerate(tasks, start=1):
            if not desc or not desc.strip():
                raise ValueError(f"Task {i} description cannot be empty")
            self.tasks.append(Task(
                id=i,
                description=desc.strip(),
                status="pending"
            ))
    
    def update_status(self, task_id: int, status: str) -> bool:
        """Update the status of a specific task.
        
        Args:
            task_id: The unique identifier of the task to update.
            status: The new status value (must be one of VALID_STATUSES).
        
        Returns:
            True if the task was found and updated successfully, False otherwise.
        
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
                return True
        
        return False
    
    def has_incomplete_tasks(self) -> bool:
        """Check if there are any tasks that haven't been completed or failed.
        
        A task is considered incomplete if its status is either "pending" or
        "in_progress". Tasks with status "completed" or "failed" are excluded.
        
        Returns:
            True if at least one task has an incomplete status, False otherwise.
        """
        return any(task.status in ("pending", "in_progress") for task in self.tasks)
    
    def to_markdown(self) -> str:
        """Render the current task list state as a formatted markdown string.
        
        The output is designed to be injected directly into LLM message payloads
        with clear visual delimiters and status indicators:
        - [✓] for completed tasks
        - [>] for in-progress tasks (with CURRENT marker)
        - [ ] for pending or failed tasks
        
        Returns:
            A string containing the formatted task list ready for context injection.
        """
        lines = ["### SYSTEM STATE: CURRENT TASK LIST"]
        
        for task in self.tasks:
            if task.status == "completed":
                marker = "[✓]"
                line = f"{marker} {task.id}. {task.description}"
            elif task.status == "in_progress":
                marker = "[>]"
                line = f"{marker} {task.id}. {task.description} (CURRENT)"
            else:  # pending or failed
                marker = "[ ]"
                line = f"{marker} {task.id}. {task.description}"
            
            lines.append(line)
        
        return "\n".join(lines)


# Module-level singleton instance for easy access from tools and core logic
_task_list_singleton = TaskList()


def get_task_list() -> TaskList:
    """Get the module-level singleton TaskList instance.
    
    Returns:
        The shared TaskList instance used throughout the application.
    """
    return _task_list_singleton
