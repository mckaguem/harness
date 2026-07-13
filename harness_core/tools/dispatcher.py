"""Dispatcher — routes a tool name to its callable at runtime."""

import inspect
from typing import Any, Callable

from harness_core.agent.tool_context import current_tool_context
from harness_core.tools.tool_result import ToolResult
import harness_core.tools as tools_module


def _accepts_ctx(fn: Callable[..., Any]) -> bool:
    """Return True if *fn* declares a ``ctx`` parameter in its signature."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    return "ctx" in params


def dispatch(func_name: str, args: dict) -> ToolResult | tuple:
    """Call the tool implementation matching *func_name* with keyword *args*.

    Tools that need the calling agent declare a ``ctx`` parameter; the dispatcher
    builds a :class:`~agent.tool_context.ToolContext` from the currently active
    agent (``CURRENT_AGENT``) and passes it automatically. Callers may also pass
    their own ``ctx`` via *args* to override the active agent. Because the
    context is injected based on the tool's own signature, tools that don't need
    it (e.g. ``submit_results``) keep their original signatures untouched — no
    special case required.

    Returns whatever the underlying tool function returns — typically a
    :class:`ToolResult`. Raises ``KeyError`` if *func_name* isn't registered;
    callers should treat that as "unknown tool".
    """
    mod = tools_module.DISPATCH_REGISTRY[func_name]  # raises KeyError for unknown tools
    fn = getattr(mod, func_name)

    # Inject the execution context only for tools that opt in via a `ctx` param.
    if "ctx" not in args and _accepts_ctx(fn):
        args = {**args, "ctx": current_tool_context()}

    return fn(**args)


def summarize(func_name: str, args: dict) -> str:
    """Return a summary string for the tool *func_name* with keyword *args*.

    Looks up the tool's summary function in SUMMARY_REGISTRY and calls it
    with **args. If the summary function isn't registered or raises an
    exception, falls back to "{func_name}: (summary unavailable)".
    """
    try:
        summary_fn = tools_module.SUMMARY_REGISTRY[func_name]
        return summary_fn(**args)
    except Exception:
        return f"{func_name}: (summary unavailable)"
