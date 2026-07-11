"""Agent package — types, core agent class, utilities, and interactive loop."""

from agent.types import AgentType
from agent.core import (
    Agent,
)
from agent.constants import (
    RESPONSE,
    TOOL_CALL,
    TOOL_RESULT,
    ERROR,
)
from agent.context import CURRENT_AGENT
from agent.tool_context import ToolContext, current_tool_context
from agent.utils import filter_tool_schemas
from agent.loop import user_loop
from agent.discovery import discover_agents, get_agent_yaml, get_agent_yaml_paths

try:
    from agent.task_list import TaskList
except ImportError:
    pass


__all__ = [
    "Agent",
    "CURRENT_AGENT",
    "ToolContext",
    "current_tool_context",
    "AgentType",
    "RESPONSE",
    "TOOL_CALL",
    "TOOL_RESULT",
    "ERROR",
    "filter_tool_schemas",
    "user_loop",
    "discover_agents",
    "get_agent_yaml",
    "get_agent_yaml_paths",
    "TaskList",
]
