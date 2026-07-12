"""Tests for harness_core.tools.submit_results."""

import json

from harness_core.tools.tool_result import ToolResult
from harness_core.tools.submit_results import submit_results


class TestSubmitResults:
    """submit_results parses and echoes a 3-key payload."""

    def _valid_payload(self):
        return json.dumps({
            "summary_of_actions": "did a thing",
            "actionable_data": {"file_paths": ["/a.py"]},
            "unresolved_issues": None,
        })

    def test_valid_payload_echoes_markdown(self):
        result = submit_results(self._valid_payload())

        assert isinstance(result, ToolResult)
        assert result.type_tag == "markdown"
        # The payload is echoed back in both llm_text and display_text.
        assert "did a thing" in result.llm_text
        assert "did a thing" in result.display_text

    def test_missing_keys_returns_error(self):
        bad = json.dumps({"summary_of_actions": "only one key"})
        result = submit_results(bad)

        assert isinstance(result, ToolResult)
        assert result.theme == "error"
        assert "missing" in result.llm_text.lower()

    def test_malformed_json_returns_error_no_raise(self):
        # Must NOT raise on invalid JSON — returns an error ToolResult instead.
        result = submit_results("{not valid json")

        assert isinstance(result, ToolResult)
        assert result.theme == "error"
