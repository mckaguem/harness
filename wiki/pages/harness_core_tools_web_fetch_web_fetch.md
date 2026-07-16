---
name: "harness_core.tools.web_fetch.web_fetch"
description: "Fetch a web page by URL and return its content as text."
source: "harness_core/tools/web_fetch.py"
---

Fetch a web page by URL and return its content as text.

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

## Signature
```python
web_fetch(url: str) -> ToolResult
```

## References
- [Module: harness_core.tools.web_fetch](harness_core_tools_web_fetch) - Parent module
