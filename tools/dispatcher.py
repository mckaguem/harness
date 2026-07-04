"""Dispatcher — routes a tool name to its callable at runtime."""

from tools.tool_result import ToolResult
from . import DISPATCH_REGISTRY


def dispatch(func_name: str, args: dict) -> ToolResult | tuple:
    """Call the tool implementation matching *func_name* with keyword *args*.

    Returns whatever the underlying tool function returns — typically a
    :class:`ToolResult`. Raises ``KeyError`` if *func_name* isn't registered;
    callers should treat that as "unknown tool".
    """
    mod = DISPATCH_REGISTRY[func_name]  # raises KeyError for unknown tools
    fn = getattr(mod, func_name)
    return fn(**args)
