"""Base skill class and interfaces."""

from abc import ABC, abstractmethod
from typing import Any


class Skill(ABC):
    """Base class for skills."""
    
    def __init__(self, name: str, description: str):
        """Initialize a skill.
        
        Args:
            name: Skill name
            description: Skill description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def activate(self, **kwargs) -> dict[str, Any]:
        """Activate the skill.
        
        Args:
            **kwargs: Skill-specific arguments
            
        Returns:
            Dictionary with skill activation results
        """
        pass
    
    def get_instructions(self) -> str | None:
        """Get detailed instructions for using this skill.
        
        Returns:
            Instructions string, or None if no instructions
        """
        return None


class YamlSkill(Skill):
    """Skill defined by YAML configuration."""
    
    def __init__(self, name: str, yaml_data: dict[str, Any]):
        """Initialize a YAML-based skill.
        
        Args:
            name: Skill name
            yaml_data: Parsed YAML data
        """
        super().__init__(name, yaml_data.get("description", ""))
        self.yaml_data = yaml_data
        self.scripts = yaml_data.get("scripts", {})
    
    def activate(self, script_name: str = "main", **kwargs) -> dict[str, Any]:
        """Activate the skill by running a script.
        
        Args:
            script_name: Which script to run (default: "main")
            **kwargs: Script arguments
            
        Returns:
            Dictionary with script execution results
        """
        script_path = self.scripts.get(script_name)
        if not script_path:
            return {
                "success": False,
                "error": f"Script '{script_name}' not found in skill '{self.name}'"
            }
        
        # Import here to avoid circular imports
        import subprocess
        import json
        from pathlib import Path
        
        try:
            # Run the script
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                cwd=Path(script_path).parent
            )
            
            # Parse JSON output if available
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {"output": result.stdout}
            
            return {
                "success": result.returncode == 0,
                "output": output,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


__all__ = [
    "Skill",
    "YamlSkill",
]