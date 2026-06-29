# This is the original source code that harness.py was created from.

import os
import subprocess
from pathlib import Path
import ollama

# Configuration
MODEL_NAME = 'qwen-3.6:27b'

SYSTEM_PROMPT = """You are a concise, expert coding assistant running in a terminal environment. 

You have access to tools for executing bash commands, reading files, and writing files. 

Operating Rules:
* When a user asks you to perform a task, use your tools to complete it step-by-step.
* Only call one tool at a time to verify the output before proceeding.
* Do not explain the code or commands before using the tool; just execute the tool.
* Strict Security Restriction: You are only allowed to read or write files within the current working directory. Do not attempt to use absolute paths outside this directory or relative path traversal (like ../) to access external files.
* If a command fails or a file cannot be read, analyze the error output and attempt to fix it.
* When the entire task is finished, output a brief text summary of what you accomplished."""

# Define the JSON schemas for the tools
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
    """Prompt user for approval, then execute bash command."""
    print(f"\n[⚠️  WARNING: Agent wants to execute] -> {command}")
    approval = input("Approve? (y/n/enter=y): ").strip().lower()
    
    if approval in ['y', 'yes', '']:
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
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Execution Error: {str(e)}"
    else:
        return "Error: User denied permission to execute this command."

def write_file(filename: str, content: str) -> str:
    """Write to a file if it is within the current working directory."""
    if not is_safe_path(filename):
        return "Error: Path traversal detected. You may only write to the current directory."
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Wrote to {filename}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

def read_file(filename: str) -> str:
    """Read a file if it is within the current working directory."""
    if not is_safe_path(filename):
        return "Error: Path traversal detected. You may only read from the current directory."
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File {filename} not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"

def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"Minimalist AI Agent initialized ({MODEL_NAME}). Type 'exit' to quit.\n")

    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ['exit', 'quit']:
            break

        messages.append({"role": "user", "content": user_input})

        while True:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                tools=AGENT_TOOLS
            )
            
            message = response['message']
            messages.append(message)

            if not message.get('tool_calls'):
                print(f"\nAgent: {message.get('content', '')}")
                break 

            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']
                
                print(f"\n[🔧 Tool Call: {func_name}]")
                
                if func_name == 'execute_bash':
                    result = execute_bash(args.get('command', ''))
                elif func_name == 'write_file':
                    result = write_file(args.get('filename', ''), args.get('content', ''))
                    print(result) 
                elif func_name == 'read_file':
                    result = read_file(args.get('filename', ''))
                    print(f"Read {args.get('filename', '')} ({len(result)} chars)") 
                else:
                    result = f"Error: Unknown function {func_name}"

                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name
                })

if __name__ == "__main__":
    main()