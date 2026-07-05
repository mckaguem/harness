"""activate_skill — tool to activate a discovered skill during agent execution."""

from pathlib import Path
from tools.tool_result import ToolResult


def activate_skill(skill_name: str) -> ToolResult:
    """Activate a skill by reading its SKILL.md body and returning instructions.
    
    This is Phase 2 of the Progressive Disclosure pattern. The agent uses this 
    tool after discovering skills via the system prompt catalog (Phase 1). When 
    called, it returns the Markdown body from the skill's SKILL.md file, prefixed 
    with the absolute path so the agent knows where to run scripts and read files.
    
    Args:
        skill_name: The name of the skill to activate (must match directory name)
        
    Returns:
        A ``ToolResult`` with the formatted skill instructions, or an error result
        on failure.
    """
    try:
        from skills_discovery import get_skill_body

        # Look up and read the body directly using dual-path discovery.
        # This automatically searches project then global config paths.
        body, error = get_skill_body(skill_name)
        
        if error:
            return ToolResult(
                llm_text=(
                    f"Failed to activate skill '{skill_name}': {error}\n\n"
                    "Check that:\n"
                    "1. The skill exists in .harness_py/skills/ (project or global)\n"
                    "2. SKILL.md is present and valid\n"
                    "3. The name matches the directory name exactly"
                ),
                display_text=(
                    f"Failed to activate skill '{skill_name}': {error}\n\n"
                    "Check that:\n"
                    "1. The skill exists in .harness_py/skills/ (project or global)\n"
                    "2. SKILL.md is present and valid\n"
                    "3. The name matches the directory name exactly"
                ),
                type_tag="text",
                title="🚫 Error",
                theme="error"
            )
        
        if not body:
            return ToolResult(
                llm_text=f"Skill '{skill_name}' has no instructions in SKILL.md body.",
                display_text=(
                    f"**{skill_name}**: No description provided\n\n"
                    f"This skill has no instructions in its SKILL.md file."
                ),
                type_tag="text",
                title="🚫 Error",
                theme="error"
            )
        
        # Determine absolute path from config
        abs_path = None
        for base in [
            (Path.cwd() / ".harness_py" / "skills"),
            (Path.home() / ".harness_py" / "skills"),
        ]:
            if (base / skill_name).is_dir():
                abs_path = str((base / skill_name).resolve())
                break
        if not abs_path:
            # last-resort: relative to cwd
            abs_path = str((Path.cwd() / "skills" / skill_name).resolve())
        
        formatted_body = (
            f"=== SKILL ACTIVATED: {skill_name} ===\n\n"
            f"**Skill Root Directory:** `{abs_path}`\n\n"
            f"**Instructions:**\n{body}\n\n"
            f"---\n"
            f"To execute scripts or read references, use relative paths from the skill root.\n"
            f"For example: `scripts/run.sh` or `references/README.md`\n"
        )
        
        display_text = (
            f"**{skill_name}**: Skill activated\n\n"
            f"Skill root directory: `{abs_path}`"
        )
        
        return ToolResult(
            llm_text=formatted_body,
            display_text=display_text,
            type_tag="markdown",
            title=f"📖 Skill Activated: {skill_name}",
            theme="status"
        )
    
    except Exception as e:
        return ToolResult(
            llm_text=f"Unexpected error activating skill '{skill_name}': {e}",
            display_text=f"Unexpected error activating skill '{skill_name}': {e}",
            type_tag="text",
            title="🚫 Error",
            theme="error"
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
