"""Token-speed formatting for Ollama chat responses."""


from .colors import DIM, c


def _format_speed(response: dict, context_length: int = 0,
                  prompt_token_count: int | None = None) -> str:
    """Extract and format tokens/sec and context usage from an Ollama chat response.

    When ``prompt_token_count`` is supplied (e.g. via :func:`_tokenize_prompt` it
    takes precedence over the possibly-zero ``prompt_eval_count`` that Ollama
    returns after a cache hit.

    Produces two stats joined by `` | ``::

        ⏱ 138 tok (5405.3 tok/s) | 6806 in (27.2% ctx)
    """
    parts = []

    eval_count = response.get('eval_count', 0) or 0
    eval_duration_ns = response.get('eval_duration', 0) or 0

    if eval_count > 0:
        if eval_duration_ns > 0:
            tps = eval_count / (eval_duration_ns / 1_000_000_000)
            parts.append(f"{eval_count} tok ({tps:.1f} tok/s)")
        else:
            parts.append(f"{eval_count} tok")

    # Use client-side tokenized count when available (more reliable under cache).
    prompt_eval_count = response.get('prompt_eval_count', 0) or 0
    if prompt_token_count is not None and prompt_token_count > 0:
        prompt_eval_count = max(prompt_eval_count, prompt_token_count)

    if prompt_eval_count > 0:
        ctx_pct_str = ""
        if context_length > 0 and prompt_eval_count > 0:
            pct = (prompt_eval_count / context_length) * 100
            ctx_pct_str = f" ({pct:.1f}% ctx)"
        parts.append(f"{prompt_eval_count} in{ctx_pct_str}")

    if parts:
        return c(f"⏱ {' | '.join(parts)}", DIM)
    return ""
