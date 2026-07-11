"""Tests for agent/task_list.py — Task and TaskList classes."""

import pytest

from harness_core.agent.task_list import Task, VALID_STATUSES, TaskList


# ── Task dataclass ──────────────────────────────────────────────────────


class TestTaskDataclass:
    """Tests for `Task` dataclass initialization and validation."""

    def test_basic_initialization(self):
        task = Task(id=1, description="Test task")
        assert task.id == 1
        assert task.description == "Test task"
        assert task.status == "pending"  # default status

    def test_custom_status(self):
        task = Task(id=2, description="Active task", status="in_progress")
        assert task.status == "in_progress"

    def test_all_valid_statuses(self):
        for valid_status in VALID_STATUSES:
            task = Task(id=100, description=f"Task with {valid_status}", status=valid_status)
            assert task.status == valid_status

    def test_invalid_status_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid status"):
            Task(id=1, description="Bad task", status="invalid_status")

    def test_empty_string_description_accepted(self):
        # Empty string is technically allowed by the dataclass __init__
        task = Task(id=1, description="")
        assert task.description == ""


# ── TaskList.initialize_tasks() ────────────────────────────────────────


class TestTaskListInitializeTasks:
    """Tests for `TaskList.initialize_tasks()` — task creation."""

    def test_valid_task_creation(self):
        task_list = TaskList()
        tasks = ["First task", "Second task", "Third task"]
        
        task_list.initialize_tasks(tasks)
        
        assert len(task_list.tasks) == 3
        for i, task in enumerate(task_list.tasks, start=1):
            assert task.id == i
            assert task.description == tasks[i - 1]
            assert task.status == "pending"

    def test_empty_list_raises_value_error(self):
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Task list cannot be empty"):
            task_list.initialize_tasks([])

    def test_single_task_creation(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Only task"])
        
        assert len(task_list.tasks) == 1
        assert task_list.tasks[0].id == 1
        assert task_list.tasks[0].description == "Only task"

    def test_overwrites_existing_tasks(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Old task"])
        
        # Should raise error because old task is still pending
        with pytest.raises(ValueError, match="Cannot initialize"):
            task_list.initialize_tasks(["New task"])

    def test_auto_incremented_ids(self):
        task_list = TaskList()
        tasks = ["A", "B", "C", "D"]
        
        task_list.initialize_tasks(tasks)
        
        ids = [t.id for t in task_list.tasks]
        assert ids == [1, 2, 3, 4]

    def test_whitespace_stripped_from_descriptions(self):
        task_list = TaskList()
        tasks = ["  Leading and trailing spaces  ", "\ttab indented"]
        
        task_list.initialize_tasks(tasks)
        
        assert task_list.tasks[0].description == "Leading and trailing spaces"
        assert task_list.tasks[1].description == "tab indented"


# ── TaskList.update_status() ───────────────────────────────────────────


class TestTaskListUpdateStatus:
    """Tests for `TaskList.update_status()` — status transitions."""

    def test_valid_status_transition_pending_to_in_progress(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Test task"])
        
        success, next_info = task_list.update_status(1, "in_progress")
        
        assert success is True
        assert task_list.tasks[0].status == "in_progress"
        # in_progress IS still incomplete - has_next should be True (task 1 is the next to work on)
        assert next_info.has_next is True

    def test_valid_status_transition_pending_to_completed(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Test task"])
        
        success, next_info = task_list.update_status(1, "completed")
        
        assert success is True
        assert task_list.tasks[0].status == "completed"
        assert next_info.all_complete is True  # Single task completed

    def test_valid_status_transition_to_failed(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Test task"])
        
        success, next_info = task_list.update_status(1, "failed")
        
        assert success is True
        assert task_list.tasks[0].status == "failed"
        assert next_info.all_complete is True  # Single task failed

    def test_invalid_status_raises_value_error(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Test task"])
        
        with pytest.raises(ValueError, match="Invalid status"):
            task_list.update_status(1, "invalid")

    def test_nonexistent_task_id_returns_false(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        
        success, next_info = task_list.update_status(999, "completed")
        
        assert success is False  # Task not found
        assert next_info.has_next is True  # Still have pending tasks
        assert next_info.id == 1  # First task is next to work on

    def test_update_multiple_tasks(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2", "Task 3"])
        
        success, _ = task_list.update_status(1, "in_progress")
        assert success is True
        
        success, _ = task_list.update_status(2, "completed")
        assert success is True
        
        success, next_info = task_list.update_status(3, "failed")
        assert success is True
        # Task 1 still has in_progress status
        assert task_list.tasks[0].status == "in_progress"
        assert next_info.has_next is True

    def test_chained_updates(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Test task"])
        
        # pending -> in_progress -> completed
        success, _ = task_list.update_status(1, "in_progress")
        assert success is True
        assert task_list.tasks[0].status == "in_progress"
        
        success, next_info = task_list.update_status(1, "completed")
        assert success is True
        assert task_list.tasks[0].status == "completed"
        assert next_info.all_complete is True  # All done


# ── TaskList.has_incomplete_tasks() ────────────────────────────────────


class TestTaskListHasIncompleteTasks:
    """Tests for `TaskList.has_incomplete_tasks()` — incomplete task detection."""

    def test_all_pending_returns_true(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        
        assert task_list.has_incomplete_tasks() is True

    def test_one_in_progress_returns_true(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        task_list.update_status(1, "completed")
        
        assert task_list.has_incomplete_tasks() is True

    def test_all_completed_returns_false(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        task_list.update_status(1, "completed")
        task_list.update_status(2, "completed")
        
        assert task_list.has_incomplete_tasks() is False

    def test_all_failed_returns_false(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        task_list.update_status(1, "failed")
        task_list.update_status(2, "failed")
        
        assert task_list.has_incomplete_tasks() is False

    def test_mixed_states_returns_true(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2", "Task 3"])
        task_list.update_status(1, "completed")
        task_list.update_status(2, "in_progress")
        task_list.update_status(3, "failed")
        
        assert task_list.has_incomplete_tasks() is True

    def test_empty_task_list_returns_false(self):
        task_list = TaskList()
        
        assert task_list.has_incomplete_tasks() is False


# ── TaskList.to_markdown() ─────────────────────────────────────────────


class TestTaskListToMarkdown:
    """Tests for `TaskList.to_markdown()` — markdown generation."""

    def test_basic_markdown_output(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        
        md = task_list.to_markdown()
        
        assert "### SYSTEM STATE: CURRENT TASK LIST" in md
        assert "- [ ] Task 1" in md
        assert "- [ ] Task 2" in md

    def test_completed_task_shows_checkmark(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Done task"])
        task_list.update_status(1, "completed")
        
        md = task_list.to_markdown()
        
        assert "- [x] Done task" in md

    def test_in_progress_task_shows_star_and_current(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Active task"])
        task_list.update_status(1, "in_progress")
        
        md = task_list.to_markdown()
        
        assert "- [*] Active task *(CURRENT)*" in md

    def test_pending_task_shows_empty_checkbox(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Pending task"])
        
        md = task_list.to_markdown()
        
        assert "- [ ] Pending task" in md

    def test_failed_task_shows_empty_checkbox(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Failed task"])
        task_list.update_status(1, "failed")
        
        md = task_list.to_markdown()
        
        assert "- [!] Failed task *(FAILED)*" in md

    def test_mixed_statuses_correct_markers(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Done", "Active", "Pending"])
        task_list.update_status(1, "completed")
        task_list.update_status(2, "in_progress")
        
        md = task_list.to_markdown()
        
        assert "- [x] Done" in md
        assert "- [*] Active *(CURRENT)*" in md
        assert "- [ ] Pending" in md

    def test_empty_task_list_returns_header_only(self):
        task_list = TaskList()
        
        md = task_list.to_markdown()
        
        assert "### SYSTEM STATE: CURRENT TASK LIST" in md
        # No task lines after header - just the header line itself with no newlines

    def test_multiple_in_progress_tasks_all_show_current(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task A", "Task B"])
        task_list.update_status(1, "in_progress")
        task_list.update_status(2, "in_progress")
        
        md = task_list.to_markdown()
        
        # Both tasks should show *(CURRENT)* marker
        assert md.count("*(CURRENT)*") == 2

    def test_newline_separated_lines(self):
        task_list = TaskList()
        task_list.initialize_tasks(["Task 1", "Task 2"])
        
        md = task_list.to_markdown()
        lines = md.split("\n")
        
        assert len(lines) == 3  # header + 2 tasks


# ── TaskList initialization ────────────────────────────────────────────


class TestTaskListInit:
    """Tests for `TaskList.__init__()` — initialization."""

    def test_empty_tasks_list(self):
        task_list = TaskList()
        
        assert task_list.tasks == []
