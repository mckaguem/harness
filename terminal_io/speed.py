"""Token-speed formatting for chat responses."""


def format_speed(response: dict, context_length: int = 0) -> str:
    """Extract and format token usage from an OpenAI-style chat response.

    Reads ``response['usage']`` which must contain ``prompt_tokens`` and
    ``completion_tokens`` keys. If ``duration_ms`` is present in the response,
    calculates tokens/sec speed.

    Produces a stats string joined by `` | ``::

        ⏱ 50 tok (33.3 tok/s) | 1024 in (25.0% ctx)
    """
    parts = []
    usage = response.get('usage') or {}

    # ---- Completion tokens / speed ----------------------------------------
    completion_tokens = usage.get('completion_tokens', 0) or 0
    
    if completion_tokens > 0:
        duration_ms = response.get('duration_ms')
        
        if duration_ms and duration_ms > 0:
            # Calculate tokens per second from wall-clock time
            tps = completion_tokens / (duration_ms / 1000.0)
            parts.append(f"{completion_tokens} tok ({tps:.1f} tok/s)")
        else:
            parts.append(f"{completion_tokens} tok")

    # ---- Input token count / context --------------------------------------
    prompt_tokens = usage.get('prompt_tokens', 0) or 0
    if prompt_tokens > 0:
        ctx_pct_str = ""
        if context_length > 0 and prompt_tokens > 0:
            pct = (prompt_tokens / context_length) * 100
            ctx_pct_str = f" ({pct:.1f}% ctx)"
        parts.append(f"{prompt_tokens} in{ctx_pct_str}")

    if parts:
        return f"[dim]⏱ {' | '.join(parts)}[/dim]"
    return ""


def format_tool_elapsed(elapsed_seconds: float) -> str:
    """Format elapsed time for a tool execution as a compact string.

    Args:
        elapsed_seconds: Time in seconds (float).

    Returns:
        A formatted string like ``⏱ 1.2s`` or ``⏱ 450ms``.
    """
    if elapsed_seconds >= 1.0:
        return f"[dim]⏱ {elapsed_seconds:.1f}s[/dim]"
    else:
        ms = elapsed_seconds * 1000
        return f"[dim]⏱ {ms:.0f}ms[/dim]"
