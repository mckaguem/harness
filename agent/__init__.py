"""Agent package — types, core agent class, utilities, and interactive loop."""

from agent.types import AgentType
from agent.core import (
    Agent,
    CURRENT_AGENT,
    RESPONSE,
    TOOL_CALL,
    TOOL_RESULT,
    ERROR,
)
from agent.utils import filter_tool_schemas
from agent.loop import user_loop
from agent.discovery import discover_agents, get_agent_yaml, get_agent_yaml_paths


__all__ = [
    "Agent",
    "CURRENT_AGENT",
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
]
