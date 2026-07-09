"""Model utilities — base URL resolution, tokenization, context length."""


import os
import urllib.error
import json
import urllib.request


def get_base_url(openai_client) -> str:
    """Return the OpenAI base URL as a plain string, if we can find it.

    The openai-python ``Client`` stores its `base_url` directly on the instance.
    If that fails, fall back to environment variables or default endpoint.
    """
    try:
        url = getattr(openai_client, "base_url", None)
        return str(url).rstrip("/")
    except Exception:
        pass

    # Last resort — read from env or use the well-known default.
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def tokenize_prompt(openai_client, messages: list[dict], model_name: str) -> int | None:
    """Ask OpenAI-compatible API to tokenize the accumulated *messages* and return the count.

    Used as a client-side source of truth for prompt token count — useful when
    caching causes ``prompt_eval_count`` to be zero in chat responses.

    Returns ``None`` on any failure (network, model load, etc.) so callers can
    fall back gracefully.
    """
    base_url = get_base_url(openai_client)
    payload = {
        "model":  model_name,
        "prompt": "\n".join(m.get("content", "") for m in messages if m.get("content")),
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base_url}/api/tokenize",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            tokens = result.get("tokens") or []
            return len(tokens) if isinstance(tokens, list) else None
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError):
        return None


def get_context_length(client, model_name: str) -> int:
    """Fetch the model's context length from OpenAI-compatible show endpoint.

    Tries multiple sources in order of reliability:
    1. Direct ``context_length`` key in model_info (top-level)
    2. Recursively search for keys containing "context" and "length" anywhere
       inside model_info (handles dotted keys, nested dicts, lists, etc.)
    3. Check submodel params for ``n_ctx`` or ``context_length``
    4. Fall back to 8192 if nothing found — most modern models support at least this

    The fallback ensures the context percentage is always displayed in the UI,
    even when the OpenAI-compatible show endpoint doesn't expose a clean value (common with
    some GGUF repos or older model cards).
    """
    try:
        info = client.show(model_name)
        mi = info.get('model_info', {}) or {}

        # 1. Direct key at top level (less common but possible)
        if 'context_length' in mi:
            val = int(mi['context_length'])
            return max(val, 1024)  # ensure at least 1K tokens
        
        # 2. Recursive search — handles dotted keys, nested dicts/lists anywhere
        def _search(obj):
            """Recursively search *obj* for a context-length value."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'context' in str(k).lower() and 'length' in str(k).lower():
                        try:
                            return int(v)
                        except (ValueError, TypeError):
                            continue
                    result = _search(v)
                    if result > 0:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = _search(item)
                    if result > 0:
                        return result
            return 0

        found = _search(mi)
        if found > 0:
            return max(found, 1024)

        # 3. Check submodels — GGUF models often store n_ctx there
        submodels = info.get('submodels', []) or []
        for sm in submodels:
            if isinstance(sm, dict):
                params = sm.get('params', {}) or {}
                for key in ('n_ctx', 'context_length'):
                    if key in params:
                        val = int(params[key])
                        if val > 0:
                            return max(val, 1024)

        # 4. Fallback default — most models support at least 8K tokens
        return 8192
    except Exception:
        return 8192


__all__ = [
    "get_base_url",
    "tokenize_prompt",
    "get_context_length",
]
