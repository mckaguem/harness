"""Session class — manages conversation history and context injection."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from agent.session_utils import (
    format_session_yaml,
    parse_session_yaml,
    create_session_filename,
    ensure_sessions_dir,
)


class Session:
    """Owns the conversation state and handles message lifecycle.

    The Session is responsible for:
    - Storing and managing the list of conversation messages
    - Queuing injected text to prepend to user input
    - Preparing individual messages with task-state context before they enter the conversation
    """

    def __init__(self, system_prompt: str, task_list=None, auto_save: bool = True):
        """Initialize a Session.

        Args:
            system_prompt: The system prompt that becomes messages[0].
            task_list: Optional TaskList instance for context injection.
            auto_save: If True, automatically saves to .sessions/ after every change.
        """
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self._task_list = task_list
        self._injected_text: Optional[str] = None
        self._auto_save = auto_save
        self._agent_type_name: str = "main"
        self.filepath = None
        
        # Generate a unique filename for this session at creation time (if auto-save is enabled)
        if auto_save:
            sessions_dir = ensure_sessions_dir()
            self._session_filename = create_session_filename(agent_type_name=self._agent_type_name)
            # Write initial empty session to file
            filepath = sessions_dir / self._session_filename
            yaml_content = format_session_yaml(self.messages, agent_type_name=self._agent_type_name)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(yaml_content)

    # -- message manipulation -----------------------------------------------

    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation.

        Args:
            content: The text content of the user message.
        """
        self.messages.append({"role": "user", "content": content})
        if self._auto_save:
            self._auto_save_session()

    def add_assistant_message(self, message_dict: dict) -> None:
        """Append an assistant response (or tool-call response) to the conversation.

        Args:
            message_dict: The full message dictionary with 'role', 'content', etc.
        """
        self.messages.append(message_dict)
        if self._auto_save:
            self._auto_save_session()

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
        if self._auto_save:
            self._auto_save_session()

    def _auto_save_session(self) -> None:
        """Automatically save the current session to .sessions/ directory.

        Uses the stored session filename if available, otherwise generates a new one.
        """
        try:
            # Use stored filename if it exists, otherwise generate a new one
            if not self._session_filename:
                self._session_filename = create_session_filename(agent_type_name=self._agent_type_name)
            
            sessions_dir = ensure_sessions_dir()
            filepath = sessions_dir / self._session_filename
            yaml_content = format_session_yaml(
                self.messages, agent_type_name=self._agent_type_name,
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            self.filepath = str(filepath)  # Set filepath after saving

        except Exception:
            # Silently fail - don't break the conversation flow if save fails.
            pass

    def save(self) -> None:
        """Public method to trigger saving the session to disk."""
        self._auto_save_session()

    def _save_impl(self, new_filepath: str, save_state: bool = True) -> None:
        """Internal helper to write messages to a specific filepath as JSON.
        
        Used by compress_session for compressed file output.
        """
        import json
        from pathlib import Path
        
        # Ensure parent directory exists
        Path(new_filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(new_filepath, 'w', encoding='utf-8') as f:
            json.dump({"messages": self.messages}, f, ensure_ascii=False, indent=2)
        
        if save_state:
            self.filepath = new_filepath

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

        The injected payload uses JSON format with explicit IDs for machine-readability:
            {
              "tasks": [
                {"id": 1, "description": "...", "status": "pending"},
                ...
              ]
            }
        This is more reliable than markdown checkboxes because the LLM can parse JSON
        deterministically and agents are less likely to reference a non-existent task ID.

        Args:
            message: A single message dict (should have role='user').

        Returns:
            Modified message dict with task state prepended to its content, or the
            original if no injection is needed.
        """
        if not self._task_list or message.get("role") != "user":
            return message

        # Get original content and structured JSON task list
        original_content = message["content"]
        task_json_payload = json.dumps(self._task_list.to_json_list(), indent=2)

        # Wrap with explicit structural delimiters using JSON for machine-readability
        wrapped_content = f"""
[SYSTEM STATE]
The current state of your task execution list (JSON, IDs are 1-indexed):
{task_json_payload}

Execute the next logical step based on this state. Only reference tasks by their explicit ID above.

[USER NEW INSTRUCTION]
{original_content}
"""

        return {
            "role": message.get("role", "user"),
            "content": wrapped_content,
        }

    # -- export/import -------------------------------------------------------

    def export_session(
        self,
        filename: Optional[str] = None,
        directory: Optional[str] = None,
        agent_type_name: str = "main",
    ) -> tuple[bool, str]:
        """Export the current session to a YAML file.

        Args:
            filename: Optional custom filename. If not provided, generates one
                using :func:`create_session_filename` with timestamp and agent type.
            directory: Optional directory path. Defaults to ``.sessions/`` in cwd.
            agent_type_name: The agent type name for the default filename.

        Returns:
            A tuple ``(success, message)`` where *message* is either the file path
            on success or an error description.
        """
        try:
            if directory:
                sessions_dir = Path(directory)
            else:
                sessions_dir = ensure_sessions_dir()

            if filename is None:
                filename = create_session_filename(agent_type_name=agent_type_name)

            filepath = sessions_dir / filename

            yaml_content = format_session_yaml(
                self.messages, agent_type_name=agent_type_name,
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            return True, str(filepath)

        except Exception as exc:
            return False, f"Failed to export session: {exc}"

    @classmethod
    def from_file(
        cls,
        filepath: str,
        task_list=None,
    ) -> "Session":
        """Load a session from a YAML file.

        Args:
            filepath: Path to the YAML session file.
            task_list: Optional TaskList instance for context injection.

        Returns:
            A new :class:`Session` instance loaded from the file.

        Raises:
            FileNotFoundError: If *filepath* does not exist.
            ValueError: If the file cannot be parsed or contains invalid data.
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Session file not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            yaml_content = f.read()

        messages, error = parse_session_yaml(yaml_content)
        if error:
            raise ValueError(error)

        # The first message must be the system prompt.
        if not messages or messages[0].get("role") != "system":
            raise ValueError(
                f"Invalid session file '{filepath}': missing system prompt as first message."
            )

        system_prompt = messages[0]["content"]
        # Skip the system prompt (already used to initialize); remaining are history.
        conversation_messages = messages[1:]

        # Extract agent type name from file content if available.
        loaded_agent_type = None
        for line in yaml_content.split("\n"):
            if line.startswith("# Agent Type:"):
                loaded_agent_type = line.replace("# Agent Type:", "").strip()
                break

        session = cls(system_prompt=system_prompt, task_list=task_list, auto_save=False)

        # Preserve the original agent type name for auto-save filename consistency.
        if loaded_agent_type:
            session._agent_type_name = loaded_agent_type

        # Replay conversation messages into the session.
        for msg in conversation_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                session.add_user_message(content)
            elif role == "assistant":
                session.add_assistant_message(msg)
            elif role == "tool":
                func_name = msg.get("name", "unknown_tool")
                session.add_tool_result(func_name, content)

        # Re-enable auto_save after loading to ensure future changes are saved.
        session._auto_save = True

        return session
