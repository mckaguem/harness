"""ANSI colour helpers, box-drawing utilities, speed formatting, and display helpers."""

import os
import re

# ── ANSI colour helpers ────────────────────────────────────────────────
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


# ── Box styles ─────────────────────────────────────────────────────────

STYLES = {
    "system":      {"colour": MAGENTA,  "border": "-"},
    "user":        {"colour": CYAN,     "border": "-"},
    "agent":       {"colour": GREEN,    "border": "-"},
    "tool_call":   {"colour": BLUE,     "border": "+-+"},
    "tool_result": {"colour": YELLOW,   "border": "+-+"},
}


def _safe_len(s: str) -> int:
    """Length of *s* with ANSI escape sequences ignored."""
    return len(re.sub(r'\033\[[^m]*m', '', s))


def print_box(title: str, content: str, colour: str | None = None, width: int = 0,
              style: str | None = None) -> None:
    """Print *content* inside a coloured box with an optional title bar.

    Uses Unicode-friendly line-drawing characters for the top/bottom borders:
    ``-`` for solid lines (system/user/agent) and ``+-`` corners for tool boxes.

    The style can be provided via :data:`STYLES` by name::

        print_box("🤖 Response", text, style="agent")       # GREEN + rounded
        print_box("📝 Prompt",   text,   style="user")      # CYAN  + rounded
        print_box("🔧 bash",     cmd,    style="tool_call") # BLUE  + corners

    Explicit *colour* overrides the one resolved from the style dict; if no style
    is given, ``rounded`` borders are used as default.
    """
    # Resolve colour and border from style name (or keep explicit values)
    if style and style in STYLES:
        resolved = STYLES[style]
        colour = colour if colour is not None else resolved["colour"]
        border_char = resolved["border"]
    else:
        border_char = "+-+"  # default corners

    if width == 0:
        width = os.get_terminal_size().columns

    if border_char.startswith("+"):
        border_top = "+" + "-" * (width - 2) + "+"
        border_bot = "+" + "-" * (width - 2) + "+"
    else:
        # solid line — "rounded" look
        border_top = "-" * width
        border_bot = "-" * width

    def _wrap(text: str, max_len: int):
        """Split text respecting terminal colour codes."""
        segments = re.split(r'(\033\[[^m]*m)', text)
        plain = "".join(s for s in segments if not s.startswith("\033"))
        lines: list[str] = []
        cursor = 0
        while cursor < len(plain):
            if max_len <= 0 or cursor >= len(plain):
                break
            chunk = plain[cursor:cursor + max_len]
            if cursor > 0 and " " in chunk[:-1]:
                last_sp = chunk.rfind(" ", 0, -1)
                chunk = chunk[:last_sp + 1].rstrip()
            lines.append(chunk)
            cursor += len(chunk) + 1
        return lines

    title_plain = re.sub(r'\033\[[^m]*m', '', title)
    if len(title_plain) + 4 <= width - 2:
        title_line = f" {c(title, colour or GREEN, bold=True)}{' ' * (width - len(title_plain) - 1)} "
    else:
        title_line = f" {title} "

    body_lines = _wrap(content.strip(), width - 2) if content.strip() else []

    parts = [border_top, title_line]
    for line in body_lines:
        pad = " " * (width - _safe_len(line) - 2)
        parts.append(f" {line}{pad} ")
    parts.append(border_bot)

    print("\n" + "\n".join(parts) + RESET + "\n")


# ── Speed formatting ──────────────────────────────────────────────────

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
            parts.append(f"{tps:.1f} in tok/s{ctx_pct_str}")
        else:
            parts.append(tps_line + ctx_pct_str)

    if parts:
        return c(f"⏱ {' | '.join(parts)}", DIM)
    return ""


def _get_context_length(client, model_name: str) -> int:
    """Fetch the model's context length from Ollama's show endpoint.

    Ollama stores this as a dotted key in *model_info*, e.g.
    ``"tokenizer.ggml.context-length"``.  We walk every entry (including
    nested dicts) to find it regardless of depth or exact prefix.
    """
    try:
        info = client.show(model_name)
        mi = info.get('model_info', {}) or {}

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


# ── Display helpers (high-level, role-specific) ───────────────────────

MAX_DISPLAY_LINES = 5


def print_system(title: str, message: str) -> None:
    """Print a system-level notification box."""
    print_box(title, message, style="system")


def prompt_user() -> str:
    """Display the user prompt line and read input. Returns the raw string."""
    return input(c("\nYou> ", CYAN, bold=True))


def display_user_prompt(user_input: str) -> None:
    """Print a box showing what the user typed (with char count)."""
    print_box(f"📝 Your Prompt ({len(user_input)} chars)", user_input, style="user")


def _trunc_for_display(text: str) -> str:
    """Return *text* truncated to ``MAX_DISPLAY_LINES`` lines with a hidden-line count."""
    lines = text.splitlines()
    if len(lines) <= MAX_DISPLAY_LINES:
        return text
    shown = "\n".join(lines[:MAX_DISPLAY_LINES])
    hidden = len(lines) - MAX_DISPLAY_LINES
    return f"{shown}\n({hidden} more line{'s' if hidden != 1 else ''} truncated)"


def display_tool_call(func_name: str, args_str: str) -> None:
    """Print a tool-call box showing the function name and its arguments."""
    print_box(f"🔧 {func_name}", args_str, style="tool_call")


def display_tool_result(func_name: str, result: str) -> None:
    """Print a truncated tool-result box (full result is kept separately)."""
    display_result = _trunc_for_display(str(result))
    print_box(f"✅ {func_name} Result", display_result, style="tool_result")


def display_agent_response(content: str, response: dict, context_length: int) -> None:
    """Print the agent's text response along with token-speed stats."""
    print_box("🤖 Agent Response", content, style="agent")
    speed_info = _format_speed(response, context_length)
    if speed_info:
        print(speed_info)


def display_tool_success(func_name: str, message: str) -> None:
    """Print a one-line success/confirmation for tools that don't return text."""
    print(c(f"   → {message}", GREEN))


def display_error(message: str) -> None:
    """Print an error message in red."""
    print(c(f"Error: {message}", RED))
