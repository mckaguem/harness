"""Agent type definition — model, tools, and system prompt configuration."""

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

    @staticmethod
    def _build_system_prompt(system_prompt_path: str) -> str:
        """Build an augmented system prompt from a base file.

        Loads the base system prompt at *system_prompt_path* and augments it by
        appending a listing of the current working directory plus the contents
        of ``AGENTS.md`` (if present). This centralises that logic so callers
        don't need to invoke :func:`build_system_prompt` themselves.

        Args:
            system_prompt_path: Path to the base prompt text file.

        Returns:
            The augmented prompt string.

        Raises:
            FileNotFoundError: If the base prompt file does not exist.
        """
        from agent.utils import build_system_prompt
        return build_system_prompt(system_prompt_path)
    
    @classmethod
    def from_file(cls, path: str) -> "AgentType":
        """Load agent definition from a YAML file and build its system prompt.

        Expected format::
        
            name: "my_agent"                              # optional display name
            model_name: "model/identifier"
            system_prompt_path: "system_prompt.txt"       # base system prompt file
            agent_tools: [execute_bash, write_file]       # or ["*"] for all
        
        The ``system_prompt_path`` is resolved into a full augmented prompt by
        loading the referenced base file and appending cwd listing + AGENTS.md.

        Args:
            path: Path to the YAML file.
            
        Returns:
            An AgentType instance with its system prompt fully built.
            
        Raises:
            FileNotFoundError: If the YAML or its ``system_prompt_path`` is missing.
            ValueError: If required fields are absent or malformed.
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
        
        agent_tools = config.get("agent_tools", [])
        if not isinstance(agent_tools, list):
            raise ValueError("'agent_tools' must be a list of strings")

        # Build the augmented system prompt from the base file referenced in YAML.
        system_prompt_path = config.get("system_prompt_path", "system_prompt.txt")
        
        try:
            system_prompt = cls._build_system_prompt(system_prompt_path)
        except FileNotFoundError:
            if config.get("system_prompt"):
                # Fall back to inline system prompt if provided.
                system_prompt = config["system_prompt"]
            else:
                raise
        
        return cls(
            name=name,
            model_name=model_name,
            system_prompt_path=system_prompt_path,
            system_prompt=system_prompt,
            agent_tools=agent_tools,
        )
    
    def inject_extra_system_prompt(self, text: str) -> None:
        """Append additional text to the existing system prompt.

        This is useful for injecting context-specific instructions without
        rebuilding the entire augmented prompt (which includes cwd listing + AGENTS.md).

        Args:
            text: The string to append. Leading/trailing whitespace should be
                  provided by the caller if desired.
        """
        self.system_prompt = f"{self.system_prompt}\n\n{text}"
