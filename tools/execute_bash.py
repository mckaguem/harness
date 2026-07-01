"""execute_bash — run a shell command in the terminal."""

from tools.utils import _strip_ansi


def execute_bash(command: str) -> tuple:
    """Execute bash command.

    Returns:
        A ``(type, text)`` tuple.  ``type`` is ``"bash"`` for successful output or
        ``"_error_"`` to signal a distinct error rendering in the display layer.
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
        return ("bash", _strip_ansi(output)) if output.strip() else ("bash", "Command executed successfully with no output.")
    except subprocess.TimeoutExpired:
        return ("_error_", _strip_ansi("Error: Command timed out after 30 seconds."))
    except Exception as e:
        return ("_error_", f"Execution Error: {e}")


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
