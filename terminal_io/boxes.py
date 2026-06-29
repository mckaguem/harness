"""Box-drawing utilities for the terminal UI."""


import os
import re

from .colors import c, RESET, GREEN


# ── Box styles ────────────────────────────────────────────────────────
STYLES = {
    "system":      {"colour": "\033[95m",  "border": "-"},
    "user":        {"colour": "\033[96m",   "border": "-"},
    "agent":       {"colour": "\033[92m",    "border": "-"},
    "tool_call":   {"colour": "\033[94m",     "border": "+-+"},
    "tool_result": {"colour": "\033[93m",   "border": "+-+"},
}


def _safe_len(s: str) -> int:
    """Length of *s* with ANSI escape sequences ignored."""
    return len(re.sub(r'\033\[[^m]*m', '', s))


def print_box(title: str, content: str, colour=None, width=0, style=None):
    """Print a coloured box around *content*, optionally titled.

    Parameters
    ----------
    title : str
        Label shown in the top bar (e.g. ``"🤖 Agent Response"``).
    content : str
        Body text.  Will be wrapped to fit within *width* columns.
    colour : str, optional
        Explicit ANSI foreground code. Overrides the style's default.
    width : int
        Total box width in columns (default: current terminal width).
    style : {"system", "user", "agent", "tool_call", "tool_result"}, optional
        Look-up a preset colour + border from :data:`STYLES`.

    Notes
    -----
    Uses Unicode-friendly line-drawing characters for the top/bottom borders:
    ``-`` for solid lines (system/user/agent) and ``+-`` corners for tool boxes.
    """
    # Resolve colour and border from style name (or keep explicit values)
    if style and style in STYLES:
        resolved = STYLES[style]
        colour = colour if colour is not None else resolved["colour"]
        border_char = resolved["border"]
    else:
        border_char = "+-+"  # default corners

    if width == 0:
        try:
            width = os.get_terminal_size().columns
        except (OSError, AttributeError):
            width = 80

    if border_char.startswith("+"):
        border_top = "+" + "-" * (width - 2) + "+"
        border_bot = "+" + "-" * (width - 2) + "+"
    else:
        # solid line — "rounded" look
        border_top = "-" * width
        border_bot = "-" * width

    def _wrap(text, max_len):
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

        # Remove phantom empty segments between consecutive ANSI codes.
        # re.split produces '' between adjacent escapes like '\x1b[1m\x1b[94m';
        # those must NOT be treated as newlines (only real \n should).
        cleaned: list[str] = []
        idx = 0
        while idx < len(flat_segments):
            seg = flat_segments[idx]
            if seg == '' and idx + 1 < len(flat_segments) and \
               flat_segments[idx - 1].startswith('\033') and \
               flat_segments[idx + 1].startswith('\033'):
                # Phantom empty — skip it; the two surrounding ANSI codes stay
                # on the same line.
                idx += 1
            else:
                cleaned.append(seg)
                idx += 1
        flat_segments = cleaned

        lines = []
        current_line_segments = []
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
