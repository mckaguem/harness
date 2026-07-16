---
name: "harness_core.tools.web_search.web_search"
description: "Web search using DuckDuckGo (via ddgs)."
source: "harness_core/tools/web_search.py"
---

Web search using DuckDuckGo (via ddgs).

Performs a text-based web search and returns formatted results.

Parameters
----------
query : str
    The search query string. Supports operators like ``filetype:pdf``
    for filtering result types.
region : str, optional
    Search region/locale code (e.g. ``"us-en"``, ``"uk-en"``, ``"ru-ru"``).
    Defaults to ``"us-en"``.
safesearch : str, optional
    Safe search level: ``"on"``, ``"moderate"``, or ``"off"``.
    Defaults to ``"moderate"``.
timelimit : str | None, optional
    Time-based filter: ``"d"`` (day), ``"w"`` (week), ``"m"`` (month),
    or ``"y"`` (year). Defaults to ``None`` (no limit).
max_results : int | None, optional
    Maximum number of results to return. Defaults to 10.
page : int, optional
    Results page number. Defaults to 1.
backend : str, optional
    Backend selector: a single or comma-delimited list of backends.
    Use ``"auto"`` for automatic selection. Defaults to ``"auto"``.

Returns
-------
ToolResult
    A ``ToolResult`` containing formatted search results or error messages.

## Signature
```python
web_search(query: str, region: str, safesearch: str, timelimit: str | None, max_results: int | None, page: int, backend: str) -> ToolResult
```

## References
- [Module: harness_core.tools.web_search](harness_core_tools_web_search) - Parent module
