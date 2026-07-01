"""execute_bash — run a shell command in the terminal."""


def execute_bash(command: str) -> str:
    """Execute bash command."""
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
        return output if output.strip() else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Execution Error: {str(e)}"


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
