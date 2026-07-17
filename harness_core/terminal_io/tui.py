"""Textual-based terminal UI for the harness.

This module is now a thin re-export shim.  The actual implementations live in
``harness_core.terminal_io.widgets`` (StatusSpinner, TaskListSidebar) and
``harness_core.terminal_io.harness_tui`` (HarnessTUI, TextualHarnessApp, launch).
"""
from __future__ import annotations

# Re-export everything that external code imports from this module so existing
# call-sites continue to work without modification.
from harness_core.terminal_io.harness_tui import (  # noqa: F401
    HarnessTUI,
    TextualHarnessApp,
    get_tui,
    launch,
)

from harness_core.terminal_io.widgets import StatusSpinner  # noqa: F401
from harness_core.terminal_io.widgets import TaskListSidebar  # noqa: F401

__all__ = ["HarnessTUI", "TextualHarnessApp", "get_tui", "launch",
           "StatusSpinner", "TaskListSidebar"]
