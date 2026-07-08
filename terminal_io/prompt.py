"""User input prompt with readline support (arrow keys, history)."""

from pathlib import Path


def prompt_user(prompt: str = None) -> str:
    """Display the user prompt and read *multi-line* input.

    Parameters
    ----------
    prompt : str, optional
        The prompt string to display before reading input. If None, a default
        prompt is used.

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
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory

    history_path = Path.home() / ".history"

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

    session = PromptSession(**session_kwargs)

    while True:
        try:
            display_prompt = prompt if prompt is not None else "You> "
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
