"""Shared utilities for the agent package."""

from pathlib import Path
from typing import Dict

from harness_core.agent.types import AgentType


def filter_tool_schemas(agent_type: AgentType, all_schemas: list[Dict]) -> list[Dict]:
    """Filter tool schemas to include only those named in ``agent_type.agent_tools``.

    If ``agent_type.agent_tools`` contains ``"*"``, all schemas are returned.
    Otherwise, only schemas whose ``function.name`` is in the list are kept.

    Args:
        agent_type: The agent definition specifying which tools to use.
        all_schemas: All available tool schema dicts (each must have a 
                     ``"function"`` key with a ``"name"`` field).
                     
    Returns:
        Filtered list of tool schemas.
        
    Raises:
        ValueError: If any name in ``agent_type.agent_tools`` is not in the 
                    available schemas (and the name is not ``"*"``).
    """
    if "*" in agent_type.agent_tools:
        return all_schemas
    
    # Build a lookup of name -> schema for fast matching.
    name_to_schema = {schema["function"]["name"]: schema for schema in all_schemas}
    
    requested_names = set(agent_type.agent_tools)
    
    missing = requested_names - name_to_schema.keys()
    if missing:
        raise ValueError(
            f"AgentType '{agent_type.model_name}' requests tools "
            f"{sorted(missing)} that are not available."
        )
    
    return [name_to_schema[name] for name in agent_type.agent_tools]


