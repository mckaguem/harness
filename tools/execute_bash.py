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
        from terminal_io import c, RED
        return c("Error: Command timed out after 30 seconds.", RED)
    except Exception as e:
        from terminal_io import c, RED
        return c(f"Execution Error: {str(e)}", RED)


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
