"""execute_bash — run a shell command in the terminal."""

from tools.utils import _strip_ansi
from tools.tool_result import ToolResult


def execute_bash(command: str) -> ToolResult:
    """Execute bash command.

    Returns:
        A ``ToolResult`` with the output text for both LLM and display,
        or an error result for failures.
    """
    try:
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        msg = _strip_ansi(output) if output.strip() else "Command executed successfully with no output."
        return ToolResult(llm_text=msg, display_text=msg, type_tag="bash", title="🐛 Execute Bash")
    except subprocess.TimeoutExpired:
        msg = _strip_ansi("Error: Command timed out after 30 seconds.")
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")
    except Exception as e:
        msg = f"Execution Error: {e}"
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")


function_def = {
    "type": "function",
    "function": {
        "name": "execute_bash",
        "description": "Execute a bash command in the terminal.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to run."}
            },
            "required": ["command"]
        }
    }
}
