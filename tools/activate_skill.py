"""activate_skill — tool to activate a discovered skill during agent execution."""

from pathlib import Path
import sys


def activate_skill(skill_name: str) -> tuple:
    """Activate a skill by reading its SKILL.md body and returning instructions.
    
    This is Phase 2 of the Progressive Disclosure pattern. The agent uses this 
    tool after discovering skills via the system prompt catalog (Phase 1). When 
    called, it returns the Markdown body from the skill's SKILL.md file, prefixed 
    with the absolute path so the agent knows where to run scripts and read files.
    
    Args:
        skill_name: The name of the skill to activate (must match directory name)
        
    Returns:
        A tuple of (type_tag, result_text). On success, type_tag is "text" and 
        result_text contains the formatted skill instructions. On failure, 
        type_tag is "_error_" with an error message.
    """
    try:
        from skills_discovery import get_skill_body
        
        # Get absolute path to skills directory
        skills_dir = Path.cwd() / "skills"
        
        # Retrieve the skill body
        body, error = get_skill_body(skill_name, skills_dir)
        
        if error:
            return (
                "_error_",
                f"Failed to activate skill '{skill_name}': {error}\n\n"
                "Check that:\n"
                "1. The skill directory exists in skills/\n"
                "2. SKILL.md is present and valid\n"
                "3. The name matches the directory name exactly"
            )
        
        if not body:
            return (
                "_error_",
                f"Skill '{skill_name}' has no instructions in SKILL.md body."
            )
        
        # Prepend absolute path for Phase 3 execution context
        skill_root = skills_dir / skill_name
        abs_path = str(skill_root.resolve())
        
        formatted_body = (
            f"=== SKILL ACTIVATED: {skill_name} ===\n\n"
            f"**Skill Root Directory:** `{abs_path}`\n\n"
            f"**Instructions:**\n{body}\n\n"
            f"---\n"
            f"To execute scripts or read references, use relative paths from the skill root.\n"
            f"For example: `scripts/run.sh` or `references/README.md`\n"
        )
        
        return ("text", formatted_body)
    
    except Exception as e:
        return (
            "_error_",
            f"Unexpected error activating skill '{skill_name}': {e}"
        )


function_def = {
    "type": "function",
    "function": {
        "name": "activate_skill",
        "description": (
            "Activate a discovered skill to receive detailed instructions. "
            "Use this when you need to perform a task covered by one of your available skills. "
            "After activation, the response contains step-by-step instructions and file paths "
            "you can use with read_file and execute_bash tools."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": (
                        "The exact name of the skill to activate. Must match a skill "
                        "listed in your available skills catalog."
                    )
                }
            },
            "required": ["skill_name"]
        }
    }
}
