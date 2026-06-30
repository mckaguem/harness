"""Shared utilities for the agent package."""

from pathlib import Path
from typing import Dict, List


def filter_tool_schemas(agent_type: "AgentType", all_schemas: List[Dict]) -> List[Dict]:
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


def build_system_prompt(base_prompt_path: str = "system_prompt.txt") -> str:
    """Read the base system prompt file and inject a listing of the current directory.

    Args:
        base_prompt_path: Path to the base system prompt text file. Defaults to 
                          ``system_prompt.txt`` in the project root so the default 
                          harness behavior is unchanged.

    If an ``AGENTS.md`` file exists in the working directory its contents are
    appended so the agent can follow any project-specific conventions.
    """
    prompt_path = Path(base_prompt_path)
    base = prompt_path.read_text(encoding="utf-8")

    # List files/dirs in the current working directory
    cwd_contents = "\n".join(
        entry.name for entry in sorted(Path.cwd().iterdir())
    )
    injection = (
        f"\n\nCurrent working directory contents:\n{cwd_contents}"
    )

    # Incorporate AGENTS.md if it exists.
    agents_md = Path.cwd() / "AGENTS.md"
    if agents_md.is_file():
        try:
            agents_content = agents_md.read_text(encoding="utf-8").strip()
            if agents_content:
                injection += (
                    f"\n\n--- AGENTS.md ---\n{agents_content}\n--- end AGENTS.md ---"
                )
        except Exception:
            pass

    return base + injection
