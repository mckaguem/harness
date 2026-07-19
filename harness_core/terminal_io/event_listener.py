"""Backward-compatibility shim for TUI event-bus wiring.

The real implementation now lives in :mod:`harness_core.terminal_io.wiring`.
This module re-exports its public names so legacy imports such as
``from harness_core.terminal_io.event_listener import make_event_listener``
continue to work.
"""

from .wiring import (
    make_event_listener,
    subscribe_event_listener,
    make_task_list_listener,
    subscribe_task_list_listener,
)

__all__ = [
    "make_event_listener",
    "subscribe_event_listener",
    "make_task_list_listener",
    "subscribe_task_list_listener",
]
