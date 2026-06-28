import os
import subprocess
from pathlib import Path
import ollama
import time
import re

# ── ANSI colour helpers ────────────────────────────────────────────────
# These are kept at module level so every print call can reference them.
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

# Foreground colours
CYAN      = "\033[96m"   # user prompts
GREEN     = "\033[92m"   # agent text / success
BLUE      = "\033[94m"   # tool calls
YELLOW    = "\033[93m"   # warnings / approval requests
RED       = "\033[91m"   # errors
MAGENTA   = "\033[95m"   # system / info

# Background colours (used sparingly for emphasis)
BG_YELLOW = "\033[43m"
BG_RED    = "\033[41m"

def c(text: str, colour: str, bold: bool = False) -> str:
    """Wrap *text* in ANSI colour codes (and optional bold)."""
    prefix = BOLD if bold else ""
    return f"{prefix}{colour}{text}{RESET}"


# ── Box-drawing helpers ────────────────────────────────────────────────

def _safe_len(s: str) -> int:
    """Length of *s* with ANSI escape sequences ignored."""
    import re
    return len(re.sub(r'\033\[[^m]*m', '', s))


def print_box(title: str, content: str, colour: str, width: int = 64,
              style: str = "rounded") -> None:
    """Print *content* inside a coloured box with an optional title bar.

    Uses Unicode box-drawing characters for a clean look (top and bottom borders only).
    The box auto-sizes to the terminal width when *width* is set to 0.
    """
    # Auto-size to terminal columns when width=0
    if width == 0:
        width = os.get_terminal_size().columns

    border_top    = "-" * width if style == "rounded" else "+" + "-" * (width - 2) + "+"
    border_bot    = "-" * width if style == "rounded" else "+" + "-" * (width - 2) + "+"

    # Build body lines, auto-wrapping if content is wider than the box.
    def _wrap(text: str, max_len: int):
        """Split text respecting terminal colour codes."""
        import re
        segments = re.split(r'(\033\[[^m]*m)', text)
        plain = "".join(s for s in segments if not s.startswith("\033"))
        lines: list[str] = []
        cursor = 0
        while cursor < len(plain):
            if max_len <= 0 or cursor >= len(plain):
                break
            chunk = plain[cursor:cursor + max_len]
            # Don't break mid-word unless it's the first chunk on a line.
            if cursor > 0 and " " in chunk[:-1]:
                last_sp = chunk.rfind(" ", 0, -1)
                chunk = chunk[:last_sp + 1].rstrip()
            lines.append(chunk)
            cursor += len(chunk) + 1
        return lines

    # Title line (no side borders)
    title_plain = re.sub(r'\033\[[^m]*m', '', title)
    if len(title_plain) + 4 <= width - 2:
        title_line = f" {c(title, colour, bold=True)}{' ' * (width - len(title_plain) - 1)} "
    else:
        title_line = f" {title} "

    # Content lines (no side borders)
    body_lines = _wrap(content.strip(), width - 2) if content.strip() else []

    parts = [border_top, title_line]
    for line in body_lines:
        pad = " " * (width - _safe_len(line) - 2)
        parts.append(f" {line}{pad} ")
    parts.append(border_bot)

    print("\n" + "\n".join(parts) + RESET + "\n")


# Configuration
MODEL_NAME = 'hf.co/deepreinforce-ai/Ornith-1.0-35B-GGUF:Q6_K'
OLLAMA_HOST = os.environ.get(
    "OLLAMA_HOST",
    os.environ.get("OPENAI_BASE_URL", "http://localhost:11435"),
)
# strip trailing /v1 if the user passed an OpenAI-format URL — Ollama client needs bare base
if OLLAMA_HOST.rstrip("/").endswith("/v1"):
    OLLAMA_HOST = OLLAMA_HOST[: -len("/v1")]
OLLAMA_CLIENT = ollama.Client(host=OLLAMA_HOST)

SYSTEM_PROMPT = """You are a concise, expert coding assistant running in a terminal environment. 

You have access to tools for executing bash commands, reading files, and writing files. 

Operating Rules:
* When a user asks you to perform a task, use the tools to complete it step-by-step.
* Only call one tool at a time to verify the output before proceeding.
* Do not explain the code or commands before using the tool; just execute the tool.
* Strict Security Restriction: You are only allowed to read or write files within the current working directory. Do not attempt to use absolute paths outside of this directory or relative path traversal (like ../) to access external files.
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
    # print(f"\n{c('[⚠️  WARNING: Agent wants to execute]', YELLOW, bold=True)} -> {command}")
    # approval = input(c("Approve? (y/n/enter=y): ", CYAN)).strip().lower()

    # if approval in ['y', 'yes', '']:
    if True:
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
    else:
        return c("Error: User denied permission to execute this command.", RED)

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

def _format_speed(response: dict, context_length: int = 0) -> str:
    """Extract and format tokens/sec from an Ollama chat response."""
    parts = []

    eval_count = response.get('eval_count', 0) or 0
    eval_duration_ns = response.get('eval_duration', 0) or 0

    if eval_count > 0:
        tps_line = f"{eval_count} tok"
        if context_length > 0 and eval_duration_ns > 0:
            tps = eval_count / (eval_duration_ns / 1_000_000_000)
            tps_line += f" ({tps:.1f} tok/s)"
        parts.append(tps_line)

    prompt_eval_count = response.get('prompt_eval_count', 0) or 0
    prompt_eval_duration_ns = response.get('prompt_eval_duration', 0) or 0

    if prompt_eval_count > 0:
        ctx_pct_str = ""
        if context_length > 0 and prompt_eval_count > 0:
            pct = (prompt_eval_count / context_length) * 100
            ctx_pct_str = f" ({pct:.1f}% ctx)"

        tps_line = f"{prompt_eval_count} in"
        if context_length > 0 and prompt_eval_duration_ns > 0:
            tps = prompt_eval_count / (prompt_eval_duration_ns / 1_000_000_000)
            parts.append(f"{tps:.1f} in tok/s{ctx_pct_str}")
        else:
            parts.append(tps_line + ctx_pct_str)

    if parts:
        return c(f"⏱ {' | '.join(parts)}", DIM)
    return ""


def _get_context_length() -> int:
    """Fetch the model's context length from Ollama's show endpoint.

    Ollama stores this as a dotted key in *model_info*, e.g.
    ``"tokenizer.ggml.context-length"``.  We walk every entry (including
    nested dicts) to find it regardless of depth or exact prefix.
    """
    try:
        info = OLLAMA_CLIENT.show(MODEL_NAME)
        mi = info.get('model_info', {}) or {}

        # Direct flat key fallback
        if 'context_length' in mi:
            return int(mi['context_length'])

        def _search(obj):
            """Recursively search *obj* for a context-length value."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'context' in str(k).lower() and 'length' in str(k).lower():
                        try:
                            return int(v)
                        except (ValueError, TypeError):
                            continue
                    result = _search(v)
                    if result > 0:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = _search(item)
                    if result > 0:
                        return result
            return 0

        return _search(mi) or 0
    except Exception:
        return 0


def main():
    context_length = _get_context_length()
    term_width = os.get_terminal_size().columns

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print_box(
        f"🚀 Agent Ready — {MODEL_NAME}",
        "Type a message to begin. Type 'exit' or 'quit' to stop.",
        MAGENTA, width=0   # 0 → auto-size to terminal columns
    )

    while True:
        user_input = input(c("\nYou> ", CYAN, bold=True))
        if user_input.strip().lower() in ['exit', 'quit']:
            print_box("Goodbye!", "See you next time.", MAGENTA, width=0)
            break

        messages.append({"role": "user", "content": user_input})

        # Show the prompt inside a fancy box.
        print_box(f"📝 Your Prompt ({len(user_input)} chars)", user_input, CYAN, width=0)

        while True:
            response = OLLAMA_CLIENT.chat(
                model=MODEL_NAME,
                messages=messages,
                tools=AGENT_TOOLS
            )

            message = response['message']
            messages.append(message)

            if not message.get('tool_calls'):
                content = message.get('content', '')
                print_box("🤖 Agent Response", content, GREEN, width=0)
                speed_info = _format_speed(response, context_length)
                if speed_info:
                    print(speed_info)
                break

            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']

                # Format arguments as a readable block.
                import json
                try:
                    args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)

                print_box(f"🔧 {func_name}", args_str, BLUE, width=0, style="rounded")

                if func_name == 'execute_bash':
                    result = execute_bash(args.get('command', ''))
                elif func_name == 'write_file':
                    result = write_file(args.get('filename', ''), args.get('content', ''))
                    print(f"   → {result}")
                elif func_name == 'read_file':
                    result = read_file(args.get('filename', ''))
                else:
                    result = c(f"Error: Unknown function {func_name}", RED)

                # Show the tool result in its own box.
                print_box(f"✅ {func_name} Result", str(result), YELLOW, width=0, style="rounded")

                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name
                })

if __name__ == "__main__":
    main()
