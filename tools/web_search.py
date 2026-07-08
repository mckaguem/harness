"""web_search — search the web using DuckDuckGo via the ddgs package."""

from tools.utils import _strip_ansi, make_error_result
from tools.tool_result import ToolResult


def web_search(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int | None = 10,
    page: int = 1,
    backend: str = "auto",
) -> ToolResult:
    """Web search using DuckDuckGo (via ddgs).

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
    """
    if not query:
        return make_error_result("`query` must be a non-empty string.")

    valid_regions = {"us-en", "uk-en", "ru-ru", "de-de", "fr-fr", "es-es", "it-it", "ja-jp", "ko-kr", "pt-br", "zh-cn"}
    if region and not all(r.strip() in valid_regions for r in region.split(",")):
        return make_error_result(
            f"Invalid `region` value. Supported values include: {', '.join(sorted(valid_regions))[:80]}..."
        )

    valid_safesearch = {"on", "moderate", "off"}
    if safesearch not in valid_safesearch:
        return make_error_result(f"`safesearch` must be one of: {', '.join(valid_safesearch)}.")

    valid_timelimits = {"d", "w", "m", "y"}
    if timelimit is not None and timelimit not in valid_timelimits:
        return make_error_result(f"`timelimit` must be one of: d (day), w (week), m (month), y (year).")

    if max_results is not None and (not isinstance(max_results, int) or max_results < 1):
        return make_error_result("`max_results` must be a positive integer.")

    if page < 1:
        return make_error_result("`page` must be >= 1.")

    try:
        from ddgs import DDGS
    except ImportError as e:
        return make_error_result(f"Error: The 'ddgs' package is not available. {e}", title="❌ Web Search Error")

    try:
        ddgs = DDGS()
        results = ddgs.text(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        )
    except Exception as e:
        return make_error_result(f"Search failed: {e}", title="❌ Web Search Error")

    if not results:
        msg = f"No results found for query: `{query}`."
        return ToolResult(
            llm_text=msg, display_text=msg, type_tag="text", title="🔍 Web Search", theme="info"
        )

    # Format results into a readable string.
    lines_out = []
    for idx, r in enumerate(results, start=1):
        title = _strip_ansi(r.get("title", "No Title"))
        href = _strip_ansi(r.get("href", ""))
        body = _strip_ansi(r.get("body", ""))

        lines_out.append(f"**[{idx}] {title}**")
        if href:
            lines_out.append(f"   URL: {href}")
        if body:
            lines_out.append(f"   {body}")
        lines_out.append("")  # blank line between results

    result_str = (
        f"**Web Search Results for:** `{query}`\n"
        f"(region={region}, safesearch={safesearch}, timelimit={timelimit or 'none'}, "
        f"max_results={max_results}, page={page})\n\n"
        + "\n".join(lines_out)
    )

    return ToolResult(
        llm_text=result_str, display_text=result_str, type_tag="text", title="🔍 Web Search", theme="info"
    )


function_def = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web using DuckDuckGo via the ddgs metasearch library. "
            "Returns formatted search results with titles, URLs, and snippets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The text search query."
                },
                "region": {
                    "type": "string",
                    "description": (
                        "Search region/locale code. Examples: us-en, uk-en, ru-ru, de-de, fr-fr. "
                        "Defaults to 'us-en'."
                    ),
                    "default": "us-en"
                },
                "safesearch": {
                    "type": "string",
                    "description": (
                        "Safe search level: on, moderate, or off. Defaults to 'moderate'."
                    ),
                    "enum": ["on", "moderate", "off"],
                    "default": "moderate"
                },
                "timelimit": {
                    "type": "string",
                    "description": (
                        "Time-based filter: d (day), w (week), m (month), y (year). "
                        "Defaults to None (no limit)."
                    ),
                    "enum": ["d", "w", "m", "y"]
                },
                "max_results": {
                    "type": "integer",
                    "description": (
                        "Maximum number of results to return. Defaults to 10."
                    )
                },
                "page": {
                    "type": "integer",
                    "description": (
                        "Results page number for pagination. Defaults to 1."
                    ),
                    "default": 1
                },
                "backend": {
                    "type": "string",
                    "description": (
                        "A single or comma-delimited list of backends. "
                        "Use 'auto' for automatic selection. Defaults to 'auto'."
                    ),
                    "default": "auto"
                }
            },
            "required": ["query"]
        }
    }
}
