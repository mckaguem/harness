"""Dispatcher — routes a tool name to its callable at runtime."""

import inspect
from typing import Any, Callable

from harness_core.tools.tool_result import ToolResult
import harness_core.tools as tools_module


def _accepts_agent(fn: Callable[..., Any]) -> bool:
    """Return True if *fn* declares an ``agent`` parameter in its signature."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    return "agent" in params


async def dispatch(func_name: str, args: dict, agent: Any) -> ToolResult | tuple:
    """Call the tool implementation matching *func_name* with keyword *args*.

    Tools that need the calling agent declare an ``agent`` parameter; the dispatcher
    passes it automatically. Because the agent is injected based on the tool's own
    signature, tools that don't need it (e.g. ``submit_results``, ``execute_bash``)
    keep their original signatures untouched — no special case required.

    Args:
        func_name: The registered tool name to dispatch.
        args: Keyword arguments forwarded to the tool function.
        agent: The calling Agent instance (passed only if the tool declares it).

    Returns:
        Whatever the underlying tool function returns — typically a :class:`ToolResult`.
        Raises ``KeyError`` if *func_name* isn't registered; callers should treat
        that as "unknown tool".
    """
    mod = tools_module.DISPATCH_REGISTRY[func_name]  # raises KeyError for unknown tools
    fn = getattr(mod, func_name)

    # Inject the agent only for tools that opt in via an `agent` param.
    if "agent" not in args and _accepts_agent(fn):
        args = {**args, "agent": agent}

    if inspect.iscoroutinefunction(fn):
        return await fn(**args)
    
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
