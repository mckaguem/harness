"""Dispatcher — maps tool names to their callables for runtime dispatch."""

import importlib


def dispatch(func_name: str, args: dict) -> str:
    """Call the tool implementation matching *func_name* with keyword *args*.

    Returns the result string from whichever tool function is invoked.
    Raises ``KeyError`` if *func_name* isn't registered — callers should treat
    that as "unknown tool".
    """
    registry = {
        "execute_bash", "write_file", "read_file", "edit_file", "grep"
    }

    if func_name not in registry:
        raise KeyError(func_name)

    mod = importlib.import_module(f"tools.{func_name}")
    fn = getattr(mod, func_name)
    return fn(**args)
