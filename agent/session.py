"""Session class — manages conversation history and context injection."""

from typing import Dict, List, Optional


class Session:
    """Owns the conversation state and handles message lifecycle.

    The Session is responsible for:
    - Storing and managing the list of conversation messages
    - Queuing injected text to prepend to user input
    - Preparing individual messages with task-state context before they enter the conversation
    """

    def __init__(self, system_prompt: str, task_list=None):
        """Initialize a Session.

        Args:
            system_prompt: The system prompt that becomes messages[0].
            task_list: Optional TaskList instance for context injection.
        """
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self._task_list = task_list
        self._injected_text: Optional[str] = None

    # -- message manipulation -----------------------------------------------

    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation.

        Args:
            content: The text content of the user message.
        """
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, message_dict: dict) -> None:
        """Append an assistant response (or tool-call response) to the conversation.

        Args:
            message_dict: The full message dictionary with 'role', 'content', etc.
        """
        self.messages.append(message_dict)

    def add_tool_result(self, func_name: str, llm_text: str) -> None:
        """Append a tool result message to the conversation.

        Args:
            func_name: The name of the tool that was called.
            llm_text: The text content for the LLM (ToolResult.llm_text).
        """
        self.messages.append({
            "role": "tool",
            "content": llm_text,
            "name": func_name,
        })

    def get_messages(self) -> list[dict]:
        """Return the full message list for sending to the LLM.

        Returns:
            The complete conversation history (including system prompt).
        """
        return self.messages

    # -- injection API -------------------------------------------------------

    def inject_text(self, s: str) -> None:
        """Queue *s* to be prepended to the next user input.

        The text is wrapped in a delimiter so that when it is injected into the
        conversation the agent (and any downstream logic) can tell it apart from
        genuine user input.

        Args:
            s: The string to inject. Leading/trailing whitespace is preserved.
        """
        self._injected_text = f"<<INJECTED>>\n{s}\n<<END_INJECTED>>"

    # -- context injection ---------------------------------------------------

    def prepare_message_for_injection(self, message: dict) -> dict:
        """Take a single user message, inject task state if applicable, return modified copy.

        This is the simplified version of the old _inject_task_state. It operates on
        one message at a time BEFORE it gets added to self.messages.

        If there is no task_list or the message is not a user-role message, returns
        the original unchanged. Otherwise wraps the content with structural delimiters
        so the LLM can distinguish injected state from new instructions.

        Args:
            message: A single message dict (should have role='user').

        Returns:
            Modified message dict with task state prepended to its content, or the
            original if no injection is needed.
        """
        if not self._task_list or message.get("role") != "user":
            return message

        # Get original content and task state markdown
        original_content = message["content"]
        task_state_md = self._task_list.to_markdown()

        # Wrap with explicit structural delimiters
        wrapped_content = f"""
[SYSTEM STATE]
The current state of your task execution list is:
{task_state_md}

Execute the next logical step based on this state.

[USER NEW INSTRUCTION]
{original_content}
"""

        return {**message, "content": wrapped_content}
