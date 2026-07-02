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
    system_prompt: str = ""
    agent_tools: List[str] = field(default_factory=list)

    @staticmethod
    def _build_system_prompt(system_prompt: str) -> str:
        """Augment an inline base prompt with the current working directory name.

        This is intentionally minimal compared to :func:`agent.utils.build_system_prompt`
        because the system prompt now lives inside the YAML itself — there's no
        external base file to read. We only append a short cwd hint so the agent
        knows which project it's operating in.

        Args:
            system_prompt: The base prompt text sourced from the agent's YAML.

        Returns:
            The augmented prompt string with cwd name appended.
        """
        injection = f"\n\nCurrent working directory name:\n{Path.cwd().name}"
        return system_prompt + injection
    
    @classmethod
    def from_file(cls, path: str) -> "AgentType":
        """Load agent definition from a YAML file and build its system prompt.

        Expected format::
        
            name: "my_agent"                              # optional display name
            model_name: "model/identifier"
            system_prompt: "You are an autonomous coding assistant..."
            agent_tools: [execute_bash, write_file]       # or ["*"] for all
        
        The ``system_prompt`` is read directly from the YAML and augmented by
        appending the current working directory name.

        Args:
            path: Path to the YAML file.
            
        Returns:
            An AgentType instance with its system prompt fully built.
            
        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValueError: If required fields are absent or malformed, or if 
                        ``system_prompt`` is missing from the YAML.
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

        system_prompt_raw = config.get("system_prompt")
        if not system_prompt_raw:
            raise ValueError(
                f"YAML '{path}' is missing required 'system_prompt' field. "
                f"The system prompt must now be defined inline in the YAML, "
                f"not referenced via a separate file."
            )

        # Augment the inline system prompt with cwd name.
        system_prompt = cls._build_system_prompt(system_prompt_raw)

        return cls(
            name=name,
            model_name=model_name,
            system_prompt=system_prompt,
            agent_tools=agent_tools,
        )
    
    def inject_extra_system_prompt(self, text: str) -> None:
        """Append additional text to the existing system prompt.

        This is useful for injecting context-specific instructions without
        rebuilding the entire augmented prompt (which includes cwd name).

        Args:
            text: The string to append. Leading/trailing whitespace should be
                  provided by the caller if desired.
        """
        self.system_prompt = f"{self.system_prompt}\n\n{text}"
