"""User input prompt with readline support (arrow keys, history)."""

import os
import readline
from rich.console import Console


console = Console()


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
    main_prompt_shown = False

    while True:
        try:
            if not main_prompt_shown:
                console.print("[cyan bold]You> [/cyan bold]", end="")
                main_prompt_shown = True
            
            line = input("  ... " if lines else "")
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
