"""web_fetch — fetch and read the contents of web pages."""

import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from harness_core.tools.utils import _strip_ansi, make_error_result
from harness_core.tools.tool_result import ToolResult


def web_fetch(url: str) -> ToolResult:
    """Fetch a web page by URL and return its content as text.

    Uses Python's standard library ``urllib`` — no external dependencies required.

    Parameters
    ----------
    url : str
        The full URL of the web page to fetch (must start with http:// or https://).

    Returns
    -------
    dict
        A JSON-serializable dictionary containing:
        - ``status_code`` (int): HTTP status code.
        - ``content_type`` (str): Content-Type header value, if present.
        - ``url`` (str): Final URL after any redirects.
        - ``text`` (str | None): Decoded text content of the page (truncated to 10000 chars).
        - ``length`` (int): Character length of ``text``, or total bytes if text is None.

    Raises
    ------
    ValueError
        If ``url`` is empty, not a string, or does not start with http:// or https://.
    URLError / HTTPError
        If the URL cannot be reached (e.g. DNS failure, 404, connection timeout).
    """

    if not isinstance(url, str):
        return make_error_result("url must be a non-empty string.")

    url = url.strip()
    if not url:
        return make_error_result("url must be a non-empty string.")

    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            break
    else:
        return make_error_result(
            f"Invalid URL. Only http:// and https:// schemes are supported, got: {url[:40]}..."
        )

    try:
        req = Request(url)
        req.add_header("User-Agent", "HarnessAgent/1.0 (Python urllib)")

        with urlopen(req, timeout=30) as response:
            status_code = response.status
            content_type = response.headers.get("Content-Type", "")
            final_url = response.url or url

            raw_data = response.read()

        # Try to decode; fall back to latin-1 (which never raises).
        charset_match = ""
        for token in content_type.split(";"):
            if "charset=" in token:
                charset_match = token.strip().split("=", 1)[1].strip()
                break

        try:
            text = raw_data.decode(charset_match or "utf-8")
        except (LookupError, UnicodeDecodeError):
            text = raw_data.decode("latin-1")

    except HTTPError as e:
        msg = f"HTTP Error {e.code}: {e.reason}"
        return make_error_result(msg)
    except URLError as e:
        msg = f"URL Error: {e.reason}"
        return make_error_result(_strip_ansi(msg))
    except Exception as e:
        msg = _strip_ansi(f"Failed to fetch URL: {e}")
        return make_error_result(msg)

    # Truncate very long pages so the agent doesn't get overwhelmed.
    MAX_CHARS = 10_000
    truncated = len(text) > MAX_CHARS
    if truncated:
        text = text[:MAX_CHARS] + f"\n\n... [truncated, page longer than {MAX_CHARS} characters]"

    result_data = {
        "status_code": status_code,
        "content_type": content_type,
        "url": final_url,
        "length": len(raw_data),
        "text": text if not truncated else None,
        "truncated": truncated,
    }

    # Build a readable string for display + JSON-encoded data.
    result_str = (
        f"Fetched: {final_url}\n"
        f"Status: {status_code} | Content-Type: {content_type} | Size: {len(raw_data)} bytes\n"
        f"{'[TRUNCATED]' if truncated else ''}"
    )
    
    return ToolResult(
        llm_text=json.dumps(result_data),
        display_text=_strip_ansi(result_str),
        type_tag="json",
        title="🌐 Web Fetch",
        theme="info",
    )


function_def = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": (
            "Fetch and read the contents of a web page given its URL. "
            "Returns status code, content type, final URL after redirects, "
            "and decoded text content (up to 10,000 characters)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "The full URL of the web page to fetch. Must start with http:// or https://."
                    ),
                },
            },
            "required": ["url"],
        },
    },
}
