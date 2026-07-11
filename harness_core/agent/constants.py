"""Module-level constants used throughout the agent package."""

RESPONSE = "response"        # Final text from the LLM (no more tool calls).
TOOL_CALL = "tool_call"      # A function call request from the LLM.
TOOL_RESULT = "tool_result"  # The result of executing a tool.
ERROR = "error"              # An error that is not tied to a specific tool result.
