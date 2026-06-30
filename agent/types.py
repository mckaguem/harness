"""Agent type definition — model, tools, and system prompt configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class AgentType:
    """Definition of an agent — its model, tools, and system prompt."""
    
    name: str = ""
    model_name: str = ""
    system_prompt_path: str = "system_prompt.txt"  # Path to the base system prompt file
    system_prompt: str = ""
    agent_tools: List[str] = field(default_factory=list)
    
    @classmethod
    def from_file(cls, path: str) -> "AgentType":
        """Load agent definition from a YAML file.
        
        Expected format::
        
            name: "my_agent"                              # optional display name
            model_name: "model/identifier"
            system_prompt_path: "system_prompt.txt"       # or use inline system_prompt
            agent_tools: [execute_bash, write_file]       # or ["*"] for all
        
        Args:
            path: Path to the YAML file.
            
        Returns:
            An AgentType instance.
        """
        yaml_path = Path(path)
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Agent definition file not found: {path}")
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        name = config.get("name", Path(path).stem)  # fall back to filename stem
        model_name = config.get("model_name")
        if not model_name:
            raise ValueError("YAML must contain 'model_name'")
        
        # Load system prompt from file or use inline text
        system_prompt_path = config.get("system_prompt_path", "system_prompt.txt")
        agent_tools = config.get("agent_tools", [])
        
        if not isinstance(agent_tools, list):
            raise ValueError("'agent_tools' must be a list of strings")
        
        # Load system prompt from file
        sys_prompt_file = Path(system_prompt_path)
        if sys_prompt_file.is_file():
            system_prompt = sys_prompt_file.read_text(encoding="utf-8").strip()
        else:
            # Use inline system_prompt if provided
            system_prompt = config.get("system_prompt", "")
        
        return cls(
            name=name,
            model_name=model_name,
            system_prompt_path=system_prompt_path,
            system_prompt=system_prompt,
            agent_tools=agent_tools
        )
