"""submit_results — sub-agent termination signal.

When a sub-agent has finished executing its assigned task, it must invoke this
tool exactly once to return structured findings back to the calling (parent)
agent.  This is the *final* action of the sub-agent's lifecycle — no further
text response should be issued after invoking it.

The ``json_payload`` argument is a JSON object with three required fields:

- ``summary_of_actions`` — concise high-level summary of what was accomplished.
- ``actionable_data``  — exhaustive technical data (file paths, line numbers,
                         verbatim code snippets or error logs).
- ``unresolved_issues`` — detailed explanation of any errors encountered or
                          data that could not be found; ``null`` if everything
                          succeeded.

The function itself just parses the payload and echoes a confirmation string so
the parent agent can see it in its tool-result display before reading the JSON.
"""

from tools.tool_result import ToolResult
from tools.utils import make_error_result


def submit_results(json_payload: str) -> ToolResult:
    """Signal task completion and return structured findings to the parent agent.

    Args:
        json_payload: A single, valid JSON object (stringified — as passed by
                      Ollama's function-calling parser).  The object must
                      conform to the schema documented in this module docstring.

    Returns:
        On success: a :class:`ToolResult` containing the parsed payload for display and
                    downstream consumption.
        On failure: an error ToolResult describing why parsing failed.
    """
    import json as _json

    try:
        data = _json.loads(json_payload)
    except Exception as exc:
        return make_error_result(
            f"'submit_results' received invalid JSON payload ({exc}). "
            "The calling agent must fix the payload and call submit_results again."
        )

    missing = [k for k in required_keys if k not in data]
    if missing:
        return make_error_result(
            f"'submit_results' payload is missing required key(s): "
            f"{', '.join(missing)}."
        )

    # Echo the structured data back so the parent agent can consume it.
    return ToolResult(
        llm_text=_json.dumps(data, indent=2),
        display_text=_json.dumps(data, indent=2),
        type_tag="markdown",
        title="ℹ️ Submit Results",
        theme="info"
    )


function_def = {
    "type": "function",
    "function": {
        "name": "submit_results",
        "description": (
            "Signal task completion and return structured findings to the "
            "parent agent.  The 'json_payload' argument must be a single, "
            "valid JSON object conforming to this schema:\n"
            "{\n"
            '  "summary_of_actions": {"type": "string", "description": '
            '"A concise, high-level summary of what you accomplished."},\n'
            '  "actionable_data": {"type": "object", "properties": {\n'
            '    "file_paths": {"type": "array", "items": {"type": "string"}, "description": '
            '"Exact, absolute paths to any files analyzed or changed."},\n'
            '    "line_numbers": {"type": "array", "items": {"type": "integer"}, "description": '
            '"Specific line numbers where issues were found or edits were made."},\n'
            '    "verbatim_snippets": {"type": "array", "items": {"type": "string"}, "description": '
            '"Exact code snippets or error logs relevant to the outcome."}\n'
            "  }},\n"
            '  "unresolved_issues": {"type": "string", "description": '
            '"Detailed explanation of any errors encountered or data you could not find."\n'
            "}\n"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "json_payload": {
                    "type": "string",
                    "description": (
                        "A single, valid JSON object. The string must be the "
                        "raw JSON text — do NOT wrap it in markdown code fences."
                    ),
                },
            },
            "required": ["json_payload"],
        },
    },
}
