"""ANSI colour helpers, box-drawing utilities, speed formatting, and display helpers."""


import os
import readline  # importing this enables arrow-key editing / history for input()
import re
from model_utils import tokenize_prompt as _tokenize_prompt

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
        """Split text respecting terminal colour codes and embedded newlines.

        Unlike the old plain-text-only version, this preserves ANSI escape
        sequences in each output line so coloured words (e.g. bold **Harness**)
        stay intact across wraps — never split mid-segment.
        """
        # First pass: split on any embedded newlines so each inner segment is
        # a single visual line (no '\n' inside it).
        flat_segments = []
        for seg in re.split(r'(\033\[[^m]*m)', text):
            if seg.startswith('\033'):
                flat_segments.append(seg)
            elif '\n' not in seg:
                flat_segments.append(seg)
            else:
                # Split plain chunks on newlines.  Newline markers become empty
                # segments so the flush logic below treats them as line breaks.
                parts = re.split(r'\n', seg)
                for i, p in enumerate(parts):
                    if p:
                        flat_segments.append(p)
                    if i < len(parts) - 1:
                        flat_segments.append('')

        lines: list[str] = []
        current_line_segments: list[str] = []
        current_visible_length = 0

        for segment in flat_segments:
            if segment.startswith('\033'):
                # ANSI code — carry through to the next output line.
                current_line_segments.append(segment)
            elif segment == '':
                # Explicit newline → flush and start a fresh line.
                if current_line_segments:
                    lines.append(''.join(current_line_segments))
                    current_line_segments = []
                    current_visible_length = 0
            else:
                seg_len = len(segment)

                # If this plain chunk is wider than max_len on its own, force-break it.
                while seg_len > max_len:
                    candidate = segment[:max_len]
                    last_space = -1
                    if ' ' in candidate[:-1]:
                        last_space = candidate.rfind(' ', 0, -1)

                    if last_space >= 0:
                        piece = segment[:last_space + 1].rstrip()
                        lines.append(''.join(current_line_segments + [piece]))
                        current_line_segments = []
                        current_visible_length = 0
                        segment = segment[last_space + 1:]
                        seg_len = len(segment)
                    else:
                        piece = segment[:max_len]
                        lines.append(''.join(current_line_segments + [piece]))
                        current_line_segments = []
                        current_visible_length = 0
                        segment = segment[max_len:]
                        seg_len = len(segment)

                needed = current_visible_length + seg_len

                if needed <= max_len:
                    # Fits on the current line — just append.
                    current_line_segments.append(segment)
                    current_visible_length += seg_len
                else:
                    # Doesn't fit — try to break at a space within the remaining width.
                    remaining_space = max_len - current_visible_length
                    candidate = segment[:remaining_space]
                    last_space = -1
                    if ' ' in candidate[:-1]:
                        last_space = candidate.rfind(' ', 0, -1)

                    if last_space >= 0:
                        piece = segment[:last_space + 1].rstrip()
                        lines.append(''.join(current_line_segments + [piece]))
                        current_line_segments = []
                        current_visible_length = 0
                        segment = segment[last_space + 1:]
                        if segment:
                            current_line_segments.append(segment)
                            current_visible_length += len(segment)
                    else:
                        # No space in remaining width — force break.
                        piece = segment[:remaining_space]
                        lines.append(''.join(current_line_segments + [piece]))
                        current_line_segments = []
                        current_visible_length = 0
                        remainder = segment[remaining_space:]
                        if remainder:
                            current_line_segments.append(remainder)
                            current_visible_length += len(remainder)

        # Flush any trailing content.
        if current_line_segments:
            lines.append(''.join(current_line_segments))

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


# ── Speed formatting & tokenization ───────────────────────────────────





def _format_speed(response: dict, context_length: int = 0,
                  prompt_token_count: int | None = None) -> str:
    """Extract and format tokens/sec and context usage from an Ollama chat response.

    When ``prompt_token_count`` is supplied (e.g. via :func:`_tokenize_prompt` it
    takes precedence over the possibly-zero ``prompt_eval_count`` that Ollama
    returns after a cache hit.

    Produces two stats joined by `` | ``::

        ⏱ 138 tok (5405.3 tok/s) | 6806 in (27.2% ctx)
    """
    parts = []

    eval_count = response.get('eval_count', 0) or 0
    eval_duration_ns = response.get('eval_duration', 0) or 0

    if eval_count > 0:
        if eval_duration_ns > 0:
            tps = eval_count / (eval_duration_ns / 1_000_000_000)
            parts.append(f"{eval_count} tok ({tps:.1f} tok/s)")
        else:
            parts.append(f"{eval_count} tok")

    # Use client-side tokenized count when available (more reliable under cache).
    prompt_eval_count = response.get('prompt_eval_count', 0) or 0
    if prompt_token_count is not None and prompt_token_count > 0:
        prompt_eval_count = max(prompt_eval_count, prompt_token_count)

    if prompt_eval_count > 0:
        ctx_pct_str = ""
        if context_length > 0 and prompt_eval_count > 0:
            pct = (prompt_eval_count / context_length) * 100
            ctx_pct_str = f" ({pct:.1f}% ctx)"
        parts.append(f"{prompt_eval_count} in{ctx_pct_str}")

    if parts:
        return c(f"⏱ {' | '.join(parts)}", DIM)
    return ""


# ── Display helpers (high-level, role-specific) ───────────────────────

MAX_DISPLAY_LINES = 5


def print_system(title: str, message: str) -> None:
    """Print a system-level notification box."""
    print_box(title, message, style="system")


# readline needs ANSI codes wrapped in \001...\002 (invisible markers)
# so it can track cursor position correctly for multi-line input.
_PROMPT_MAIN   = c("\nYou> ", CYAN, bold=True).replace(RESET, "\001" + RESET + "\002")
_PROMPT_CONT   = "  ... "


def prompt_user() -> str:
    """Display the user prompt and read *multi-line* input.

    Features
    --------
    - Arrow keys, backspace / delete, Home/End/Ctrl-A/Z etc. work via GNU
      ``readline`` (imported at module load).
    - Copy/paste multiple lines: each newline continues the entry; an empty
      line or Ctrl+D submits what you've typed so far.
    - History is persisted to ``~/.history`` so entries survive across runs.

    Returns
    -------
    str
        The assembled input (newlines preserved).  Returns ``""`` if the user
        hits Ctrl+D on a blank line at the very start of an entry.
    """
    history_path = os.path.expanduser("~/.history")
    try:
        readline.read_history_file(history_path)
    except FileNotFoundError:
        pass

    lines: list[str] = []

    while True:
        try:
            if lines:
                line = input(_PROMPT_CONT)
            else:
                line = input(_PROMPT_MAIN)
        except EOFError:
            # Ctrl+D at any point submits what's been typed so far.
            break

        # Empty line on a fresh entry with nothing accumulated → submit empty.
        if line == "" and not lines:
            return ""

        # Empty line on a continuation row finishes the multi-line entry.
        if line == "":
            break

        lines.append(line)

    text = "\n".join(lines)

    # Persist non-empty submissions to history.
    if text.strip():
        try:
            readline.append_history_file(1, history_path)
        except Exception:
            pass

    return text


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


def display_agent_response(content: str, response: dict, context_length: int,
                           prompt_token_count: int | None = None) -> None:
    """Print the agent's text response along with token-speed stats."""
    print_box("🤖 Agent Response", content, style="agent")
    speed_info = _format_speed(response, context_length, prompt_token_count)
    if speed_info:
        print(speed_info)


def display_tool_success(func_name: str, message: str) -> None:
    """Print a one-line success/confirmation for tools that don't return text."""
    print(c(f"   → {message}", GREEN))


def display_error(message: str) -> None:
    """Print an error message in red."""
    print(c(f"Error: {message}", RED))
