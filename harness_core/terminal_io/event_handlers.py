"""Handler methods for terminal I/O topics, extracted from event_listener.py.

This module contains the 13 topic handler methods that were previously nested
inside :class:`HarnessEventListener` in ``event_listener.py``.  Each method is
a standalone async function on :class:`TopicHandlers`, without any filter or
decorator — sender filtering is applied at the subscription layer instead.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from harness_core.eventbus import Event, EventBus, EventListener, event_bus, filter_by_sender
from harness_core.event_types import (
    AgentResponsePayload, SessionErrorPayload, SystemMessagePayload, TaskListPayload, ToolCallPayload, ToolErrorPayload, ToolResultPayload, TurnStatsPayload,
)
from .display import display_agent_response, display_error, display_tool_call, display_tool_result, display_turn_stats, print_system
from .task_display import render_task_list_markdown_from_payload
from .tui import get_tui


def _make_refresh_handler() -> Callable:
    """Build the shared async handler used by each task-list event handler."""

    async def _refresh(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, TaskListPayload):
            return
        get_tui().update_sidebar_tasks_from_payload(payload)

    return _refresh


def _make_system_message_handler() -> Callable:
    """Build the shared async handler used by each system-message event handler."""

    async def _system_message(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, SystemMessagePayload):
            return
        print_system(payload.title, payload.message)

    return _system_message


class TopicHandlers:
    """Async handlers for each ``agent.*`` topic.

    Each method receives an :class:`~harness_core.eventbus.Event` and renders or
    dispatches it to the appropriate display / TUI routine.  Sender filtering is
    *not* applied here — that lives at the subscription layer (see
    ``event_listener.py``).
    """

    def __init__(self) -> None:
        self._refresh = _make_refresh_handler()
        self._system_message = _make_system_message_handler()

    async def handle_agent_tasklist_initialize(self, event: Event) -> None:
        await self._refresh(self, event)

    async def handle_agent_tasklist_update(self, event: Event) -> None:
        await self._refresh(self, event)

    async def handle_agent_tasklist_reset(self, event: Event) -> None:
        await self._refresh(self, event)

    async def handle_agent_session_autocompress(self, event: Event) -> None:
        await self._system_message(self, event)

    async def handle_agent_status_ready(self, event: Event) -> None:
        await self._system_message(self, event)
        payload = event.payload
        if isinstance(payload, SystemMessagePayload):
            tui = get_tui()
            if tui is not None and payload.model:
                # Only update if the payload has a non-empty model string.
                # This prevents overwriting the correct value set in on_mount().
                tui.update_sidebar_model_name(payload.model)

    async def handle_agent_turn_start(self, event: Event) -> None:
        get_tui().show_spinner()

    async def handle_agent_turn_stop(self, event: Event) -> None:
        get_tui().hide_spinner()

    async def handle_agent_tool_error(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, ToolErrorPayload):
            return
        display_error(payload.message)
        from harness_core.terminal_io import display as _display
        _display.reset_pending_tool_panel()

    async def handle_agent_session_error(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, SessionErrorPayload):
            return
        display_error(payload.message)

    async def handle_agent_tool_call(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, ToolCallPayload):
            return
        display_tool_call(
            payload.func_name,
            payload.args_str,
            summary=payload.summary,
            pre_content=payload.pre_content or "",
            reasoning=payload.reasoning,
        )

    async def handle_agent_tool_result(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, ToolResultPayload):
            return
        display_tool_result(
            payload.func_name,
            result_title=payload.result_title,
            result_display_text=payload.result_display_text or "",
            result_theme=payload.result_theme or "info",
            result_type_tag=payload.result_type_tag or "text",
        )

    async def handle_agent_turn_response(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, AgentResponsePayload):
            return
        display_agent_response(
            payload.content,
            payload.response,
            payload.context_length,
            reasoning=payload.reasoning,
        )

    async def handle_agent_turn_stats(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, TurnStatsPayload):
            return
        display_turn_stats(
            payload.response,
            payload.context_length,
            elapsed_seconds=payload.elapsed_seconds,
        )
