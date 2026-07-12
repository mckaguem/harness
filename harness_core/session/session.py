import json
import os
from pathlib import Path


from .session_utils import (
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

    def __init__(self, system_prompt: str, task_list=None, auto_save: bool = True,
                 provider=None, model_name: str = "", agent_type_name: str = "main"):
        """Initialize a Session.

        Args:
            system_prompt: The system prompt that becomes messages[0].
            task_list: Optional TaskList instance for context injection.
            auto_save: If True, automatically saves to .sessions/ after every change.
            provider: Optional LLM Provider instance (needed for summarize()).
            model_name: Model name string (needed for summarize() calls).
            agent_type_name: The agent type name (e.g. 'analyst', 'coder') used
                in the auto-save filename. Captured at construction so the saved
                file always carries the correct agent type (even for subagents).
        """
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self._task_list = task_list
        self._injected_text: str | None = None
        self._auto_save = auto_save
        self._agent_type_name: str = agent_type_name
        self.filepath = None
        self._provider = provider          # type: object | None
        self._model_name: str = model_name
        
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

    def add_tool_result(self, func_name: str, llm_text: str, tool_call_id: str) -> None:
        """Append a tool result message to the conversation.

        Args:
            func_name: The name of the tool that was called.
            llm_text: The text content for the LLM (ToolResult.llm_text).
        """
        self.messages.append({
            "role": "tool",
            "content": llm_text,
            "name": func_name,
            "tool_call_id": tool_call_id
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

        except Exception as exc:  # noqa: BLE001
            # Surface the failure instead of swallowing it (AGENTS.md §4: never
            # silently swallow). Go to stderr so it doesn't pollute the
            # LLM-facing output or break the conversation flow.
            import sys
            print(
                f"[session] Warning: failed to auto-save session to "
                f"{getattr(self, 'filepath', '<unknown>')}: {exc}",
                file=sys.stderr,
            )

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

    def consume_injected_text(self) -> str | None:
        """Return and clear any queued injected text.

        Returns the currently queued text (or ``None`` if nothing is queued)
        and resets the queue so it is only applied to one user turn.
        """
        text = self._injected_text
        self._injected_text = None
        return text

    # -- summarization -------------------------------------------------------

    def summarize(self, summary_prompt: str | None = None) -> str:
        """Ask the LLM to summarise the conversation accumulated so far.

        Builds a temporary message list from recent history and appends a
        summary prompt. The resulting turn is *not* persisted in ``self.messages``
        — the session's own history remains untouched.

        Args:
            summary_prompt: Optional override for how to summarise. If provided,
                this replaces the default "expert summarizer" system message and
                user instruction, letting the caller specify any custom guidance.

        Returns:
            A string containing the generated summary, or an empty string on
            failure.
        
        Raises:
            RuntimeError: If no provider is configured (call Agent to use summarize).
        """
        if self._provider is None:
            raise RuntimeError(
                "Session.summarize() requires a Provider. "
                "Ensure the agent was initialized with a valid provider."
            )

        transcript_lines = []
        for msg in self.messages:
            if msg['role'] == 'system':
                continue
            elif msg['role'] == 'tool':
                # Turn a technical tool response into a simple narrative note
                transcript_lines.append(f"[The agent received a tool call response.]")
            else:
                transcript_lines.append(f"{msg['role'].capitalize()}: {msg['content']}")

        formatted_transcript = "\n".join(transcript_lines)

        if summary_prompt is not None:
            messages = [
                {
                    'role': 'user',
                    'content': f"{summary_prompt}\n\nConversation transcript:\n\n{formatted_transcript}"
                }
            ]
        else:
            messages = [{
                'role': 'system',
                'content': (
                    "You are an expert summarizer. Your job is to provide a concise, "
                    "bulleted summary of the provided conversation transcript. "
                    "Focus purely on the core topics discussed and key conclusions. "
                    "Do not include introductory or concluding conversational filler."
                )
            },
            {
                'role': 'user',
                'content': f"Please summarize this conversation transcript:\n\n{formatted_transcript}"
            }
        ]

        # Call the provider directly to get the LLM response
        try:
            raw_response = self._provider.chat_completion(
                messages=messages,
                model=self._model_name,
            )
        except Exception as exc:
            raise RuntimeError(f"Provider chat request failed: {exc}") from exc

        # Extract just the content string from the response (fixing bug in original)
        choices = raw_response.get("choices", [])
        if not choices:
            return ""
        
        message_obj = choices[0].get("message", {})
        summary_content = message_obj.get("content", "") or ""

        return summary_content

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
        filename: str | None = None,
        directory: str | None = None,
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

        session = cls(system_prompt=system_prompt, task_list=task_list,
                      auto_save=False, agent_type_name=loaded_agent_type or "main")

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
