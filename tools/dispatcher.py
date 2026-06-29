"""Dispatcher — routes a tool name to its callable at runtime."""

from . import DISPATCH_REGISTRY


def dispatch(func_name: str, args: dict) -> str:
    """Call the tool implementation matching *func_name* with keyword *args*.

    Returns the result string from whichever tool function is invoked.
    Raises ``KeyError`` if *func_name* isn't registered — callers should treat
    that as "unknown tool".
    """
    mod = DISPATCH_REGISTRY[func_name]  # raises KeyError for unknown tools
    fn = getattr(mod, func_name)
    return fn(**args)
