---
name: "harness_core.terminal_io.prompt.prompt_user"
description: "Display the user prompt and read *multi-line* input."
source: "harness_core/terminal_io/prompt.py"
---

Display the user prompt and read *multi-line* input.

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

## Signature
```python
prompt_user(prompt: str | None) -> str
```

## References
- [Module: harness_core.terminal_io.prompt](harness_core_terminal_io_prompt) - Parent module
