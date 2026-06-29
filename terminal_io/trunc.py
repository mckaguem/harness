"""Text truncation helpers for display."""


MAX_DISPLAY_LINES = 5


def _trunc_for_display(text: str) -> str:
    """Return *text* truncated to ``MAX_DISPLAY_LINES`` lines with a hidden-line count."""
    lines = text.splitlines()
    if len(lines) <= MAX_DISPLAY_LINES:
        return text
    shown = "\n".join(lines[:MAX_DISPLAY_LINES])
    hidden = len(lines) - MAX_DISPLAY_LINES
    return f"{shown}\n({hidden} more line{'s' if hidden != 1 else ''} truncated)"
