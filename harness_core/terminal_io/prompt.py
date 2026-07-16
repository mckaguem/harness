"""User input prompt - delegates to the TUI controller."""

from . import tui as _tui


def prompt_user(prompt: str | None = None) -> str:
    """Display the user prompt and read multi-line input from the TUI.

    Parameters
    ----------
    prompt : str, optional
        The prompt string to display before reading input.

    Returns
    -------
    str
        The assembled input (newlines preserved). Returns ``""`` on EOF.
    """
    controller = _tui.get_tui()
    return controller.prompt(prompt if prompt is not None else "")
