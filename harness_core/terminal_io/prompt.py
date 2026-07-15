"""User input prompt with readline support (arrow keys, history).

When a textual TUI is active, :func:`prompt_user` delegates to the TUI
controller's blocking :meth:`~terminal_io.tui.HarnessTUI.prompt`, which reads
from the on-screen ``TextArea``.  Otherwise the original ``prompt_toolkit``
multi-line session (with ``~/.history`` persistence) is used unchanged.
"""

from pathlib import Path

from prompt_toolkit import PromptSession


def prompt_user(prompt: str | None = None) -> str:
    """Display the user prompt and read *multi-line* input.

    Parameters
    ----------
    prompt : str, optional
        The prompt string to display before reading input. If None, a default
        prompt is used.

    Features (classic / non-TUI path)
    ----------------------------------
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
    # Inside the textual TUI, read from the on-screen TextArea instead.
    from . import tui as _tui

    controller = _tui.get_tui()
    if controller.is_active():
        return controller.prompt(prompt if prompt is not None else "")

    from prompt_toolkit.history import FileHistory

    history_path = Path.home() / ".history"  # noqa: S306

    session_kwargs: dict = {
        "multiline": True,
        "auto_suggest": False,
        "enable_history_search": True,
        "search_ignore_case": True,
        "complete_while_typing": False,
        "mouse_support": False,
        "wrap_lines": True,
        "history": FileHistory(str(history_path)),
    }

    session: PromptSession = PromptSession(**session_kwargs)

    while True:
        try:
            display_prompt = prompt if prompt is not None else ""
            text = session.prompt(display_prompt, multiline=True)
            if not text.strip():
                continue  # skip accidental empty submissions
            return text
        except KeyboardInterrupt:
            print("^C")
            continue
        except EOFError:
            break

    return ""
