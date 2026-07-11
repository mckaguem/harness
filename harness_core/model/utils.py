"""Model utilities — base URL resolution and tokenization."""


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





__all__ = [
    "get_base_url",
    "tokenize_prompt",
]
