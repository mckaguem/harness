"""Token-speed formatting for chat responses."""


def _resolve_usage(response: dict) -> tuple[int, int]:
    """Extract (completion_tokens, prompt_tokens) from a response.

    Supports both OpenAI-style and Ollama-native formats:
      - OpenAI:  {"usage": {"completion_tokens": N, "prompt_tokens": M}}
      - Ollama:  {"eval_count": N, "prompt_eval_count": M}
    Returns (0, 0) if neither format is present.
    """
    usage = response.get("usage") or {}

    # OpenAI-style keys take precedence when both are present.
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)

    if completion_tokens > 0 or prompt_tokens > 0:
        return completion_tokens, prompt_tokens

    # Fall back to Ollama-native keys.
    eval_count = int(response.get("eval_count") or 0)
    prompt_eval_count = int(response.get("prompt_eval_count") or 0)

    if eval_count > 0 or prompt_eval_count > 0:
        return eval_count, prompt_eval_count

    return 0, 0


def _resolve_duration_ms(response: dict) -> float | None:
    """Extract wall-clock duration in milliseconds from a response.

    Supports:
      - OpenAI-style: {"duration_ms": N} (already in ms)
      - Ollama eval:   {"eval_duration": N} (nanoseconds → ms)
      - Ollama prompt: {"prompt_eval_duration": N} (nanoseconds → ms)

    Returns None when no duration information is available.
    """
    # OpenAI-style wall-clock duration.
    if "duration_ms" in response:
        val = response["duration_ms"]
        return float(val) if val else None

    # Ollama: prefer eval_duration (completion phase), fall back to prompt_eval_duration.
    for key in ("eval_duration", "prompt_eval_duration"):
        val = response.get(key)
        if val is not None and int(val) > 0:
            return int(val) / 1_000_000.0  # ns → ms

    return None


def format_speed(response: dict, context_length: int = 0) -> str:
    """Extract and format token usage from an OpenAI-style or Ollama-native response.

    Reads ``response['usage']`` (OpenAI) or top-level ``eval_count`` /
    ``prompt_eval_count`` keys (Ollama).  If a wall-clock duration is present
    in the response, calculates tokens/sec speed.

    Produces a stats string joined by `` | ``::

        ⏱ 50 tok (33.3 tok/s) | 1024 in (25.0% ctx)
    """
    completion_tokens, prompt_tokens = _resolve_usage(response)
    duration_ms = _resolve_duration_ms(response)

    parts: list[str] = []

    # ---- Completion tokens / speed ----------------------------------------
    if completion_tokens > 0:
        if duration_ms and duration_ms > 0:
            tps = completion_tokens / (duration_ms / 1000.0)
            parts.append(f"{completion_tokens} tok ({tps:.1f} tok/s)")
        else:
            parts.append(f"{completion_tokens} tok")

    # ---- Input token count / context --------------------------------------
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
