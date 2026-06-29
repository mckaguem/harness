"""Tool definitions and implementations for the agent."""

import subprocess
from pathlib import Path
from terminal_io import c, RED, GREEN, DIM


AGENT_TOOLS = [
    {
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
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file."},
                    "content": {"type": "string", "description": "The exact content to write to the file."}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file to read."}
                },
                "required": ["filename"]
            }
        }
    }
]


def is_safe_path(filename: str) -> bool:
    """Ensure the target path is strictly within the current working directory."""
    try:
        cwd = Path.cwd().resolve()
        target = (Path.cwd() / filename).resolve()
        return target.is_relative_to(cwd)
    except Exception:
        return False


def execute_bash(command: str) -> str:
    """Execute bash command."""
    try:
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
        return c("Error: Command timed out after 30 seconds.", RED)
    except Exception as e:
        return c(f"Execution Error: {str(e)}", RED)


def write_file(filename: str, content: str) -> str:
    """Write to a file if it is within the current working directory."""
    if not is_safe_path(filename):
        return c(
            "Error: Path traversal detected. You may only write to the current directory.",
            RED
        )

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return c(f"Success: Wrote to {filename}", GREEN)
    except Exception as e:
        return c(f"Error writing to file: {str(e)}", RED)


def read_file(filename: str) -> str:
    """Read a file if it is within the current working directory."""
    if not is_safe_path(filename):
        return c(
            "Error: Path traversal detected. You may only read from the current directory.",
            RED
        )

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(c(f"Read {filename} ({len(content)} chars)", DIM))
        return content
    except FileNotFoundError:
        return c(f"Error: File {filename} not found.", RED)
    except Exception as e:
        return c(f"Error reading file: {str(e)}", RED)
