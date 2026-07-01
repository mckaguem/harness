"""Agent class — owns the conversation and processes one user prompt to completion."""

import contextvars
import json
import os
from typing import Dict, Generator, List, Optional

import ollama


# Current agent in the running conversation (set by handle_prompt).
CURRENT_AGENT: contextvars.ContextVar = contextvars.ContextVar("current_agent", default=None)

# ---------------------------------------------------------------------------
# Output kinds yielded by ``handle_prompt``.
# ---------------------------------------------------------------------------

RESPONSE = "response"        # Final text from the LLM (no more tool calls).
TOOL_CALL = "tool_call"      # A function call request from the LLM.
TOOL_RESULT = "tool_result"  # The result of executing a tool.
ERROR = "error"              # An error that is not tied to a specific tool result.


# ---------------------------------------------------------------------------
# Agent — owns the conversation and processes one user prompt to completion.
# ---------------------------------------------------------------------------

class Agent:
    """Owns the conversation state and handles a single user turn."""
    
    def __init__(self, 
                 agent_type: "AgentType", 
                 ollama_client: "ollama.Client", 
                 context_length: int,
                 tool_schemas: Optional[List[Dict]] = None,
                 extra_tools: Optional[List[Dict]] = None):
        """Initialize an Agent.
        
        Args:
            agent_type: The agent definition (model, system prompt, tools).
            ollama_client: An initialized Ollama client.
            context_length: Model's context window size.
            tool_schemas: All available tool schema dicts. If provided, the 
                         agent will only expose the schemas whose names are in 
                         ``agent_type.agent_tools`` (or all if ``"*"`` is used).
            extra_tools: Additional function_def dicts that should be added to
                         the filtered tool list regardless of YAML constraints.
                         Useful for tools injected at runtime (e.g. ``complete_task``
                         in sub-agent sessions) without modifying agent YAML files.
        """
        self._agent_type = agent_type
        self._client = ollama_client
        self._context_length = context_length
        
        # Resolve Ollama host, stripping trailing /v1 if present (OpenAI-compatible URLs).
        raw_host = getattr(ollama_client, "host", None) or os.environ.get(
            "OLLAMA_HOST",
            os.environ.get("OPENAI_BASE_URL", "http://localhost:11435"),
        )
        self._ollama_host = (
            raw_host[:-len("/v1")]
            if raw_host.rstrip("/").endswith("/v1")
            else raw_host
        )
        # Filter tool schemas based on AgentType.
        from agent.utils import filter_tool_schemas
        if tool_schemas:
            self._tools = filter_tool_schemas(agent_type, tool_schemas)
        else:
            self._tools = []
        
        # Append any extra tools (e.g. runtime-injected ones like complete_task).
        if extra_tools:
            self._tools.extend(extra_tools)

        self.messages: list[dict] = [{"role": "system", "content": agent_type.system_prompt}]
        self._injected_text: Optional[str] = None
        
        # Cache-friendly task state management — all dynamic state is injected
        # at the tail end of messages, never touching messages[0].
        from agent.task_list import get_task_list, TaskList
        self._task_list: Optional[TaskList] = get_task_list()
        self._max_loops: int = 5  # Safety ceiling to prevent infinite loops

        # Bind this instance as the current agent in the thread context so tools
        # can spawn sub-agents without an explicit parent reference.
        CURRENT_AGENT.set(self)
    
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

    # -- internal helpers ----------------------------------------------------

    def _inject_task_state(self, messages: list[dict]) -> list[dict]:
        """Inject task state into the last user message without modifying system prompt.
        
        This method preserves Ollama's prefix cache by keeping messages[0] (system)
        completely static. It intercepts the very last message in the array (which
        should be the latest user turn) and wraps its content with formatted task
        state markdown using explicit structural delimiters.
        
        Args:
            messages: The conversation history to modify.
            
        Returns:
            A new list of messages with task state injected into the last user message.
        """
        if not self._task_list or len(messages) < 2:
            return messages
        
        # Create a copy to avoid mutating the original
        modified_messages = messages.copy()
        
        # Find the last user message (index -1 should be the latest user turn)
        last_msg_idx = len(modified_messages) - 1
        if modified_messages[last_msg_idx]["role"] != "user":
            return messages  # Don't modify non-user messages
        
        # Get original content and task state markdown
        original_content = modified_messages[last_msg_idx]["content"]
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
        
        # Update only the content, preserving role and other metadata
        modified_messages[last_msg_idx] = {
            **modified_messages[last_msg_idx],
            "content": wrapped_content
        }
        
        return modified_messages

    def _chat(self, messages: list[dict]) -> str:
        """Send *messages* to the Ollama client and return the response content.

        This is the single point for building the request payload (model,
        tools, context length) so callers don't have to repeat it.

        Args:
            messages: The full conversation history to send.

        Returns:
            The ``message.content`` string from the chat response.
        """
        response = self._client.chat(
            model=self._agent_type.model_name,
            messages=messages,
            tools=self._tools if self._tools else None,
            options={"num_ctx": self._context_length},
        )
        return response["message"].get("content", "")
    
    # -- public API ----------------------------------------------------------
    
    def handle_prompt(self, user_input: str) -> Generator[tuple[str, ...], None, None]:
        """Process a single user prompt to completion.
        
        Yields tuples of ``(kind, ...)`` where ``kind`` is one of
        :data:`RESPONSE`, :data:`TOOL_CALL`, :data:`TOOL_RESULT` or
        :data:`ERROR`.  The agent dispatches and executes each tool internally;
        it never calls display functions itself.
        
        Yields::
        
            (RESPONSE,         content, ollama_response)
            (TOOL_CALL,        func_name, args_str)
            (TOOL_RESULT,      func_name, result)
            (ERROR,            description)
        """
        from tools.dispatcher import dispatch

        # Prepend any injected text to the user input, then clear the queue.
        effective_input = user_input
        if self._injected_text is not None:
            effective_input = f"{self._injected_text}\n\n{user_input}"
            self._injected_text = None

        self.messages.append({"role": "user", "content": effective_input})
        
        loop_count = 0
        while True:
            # Safety ceiling to prevent infinite loops (Component 4)
            if loop_count >= self._max_loops:
                yield (ERROR, f"Maximum loop count ({self._max_loops}) exceeded. Breaking out of handle_prompt.")
                break
            
            # Apply cache-friendly context injection before sending to Ollama (Component 3)
            messages_to_send = self._inject_task_state(self.messages)
            
            response = self._client.chat(
                model=self._agent_type.model_name,
                messages=messages_to_send,
                tools=self._tools if self._tools else None,
                options={"num_ctx": self._context_length},
            )
            
            message = response["message"]
            self.messages.append(message)
            
            if not message.get("tool_calls"):
                content = message.get("content", "")
                yield (RESPONSE, content, response)
                break
            
            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                
                # Termination circuit breaker (Component 4)
                if func_name == "complete_task":
                    if self._task_list and self._task_list.has_incomplete_tasks():
                        # Block termination - append error instruction to history
                        blocked_message = {
                            "role": "user",
                            "content": (
                                "[SYSTEM ERROR] Execution termination blocked. "
                                "You still have incomplete tasks in your state machine. "
                                "You must finish them or update their status to 'failed' "
                                "before you can invoke complete_task."
                            )
                        }
                        self.messages.append(blocked_message)
                        yield (TOOL_RESULT, func_name, "_error_", 
                               blocked_message["content"])
                        loop_count += 1
                        continue
                
                try:
                    args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)
                
                yield (TOOL_CALL, func_name, args_str)

                try:
                    result = dispatch(func_name, args)
                except KeyError as exc:
                    description = f"Unknown function '{func_name}'."
                    result_type = "_error_"
                    yield (ERROR, description)
                    result_text = description
                except Exception as exc:
                    # Handle unexpected errors (e.g., wrong args to tool)
                    description = f"Error calling {func_name}: {exc}"
                    result_type = "_error_"
                    yield (ERROR, description)
                    result_text = description
                else:
                    # Unpack tuple from tools — handle both new-style and legacy plain-string returns.
                    if isinstance(result, tuple) and len(result) == 2:
                        result_type, result_content = result
                    else:
                        result_type, result_content = "text", str(result)
                    result_text = result_content
                
                self.messages.append({
                    "role": "tool",
                    "content": result_text,
                    "name": func_name,
                })
                yield (TOOL_RESULT, func_name, result_type, result_text)

    @classmethod
    def spawn_subagent(cls, sub_name: str, parent_agent: Optional["Agent"] = None,
                       tool_schemas: Optional[List[Dict]] = None,
                       extra_tools: Optional[List[Dict]] = None):
        """Build and return a configured ``Agent`` for the named sub-agent.

        Pure factory — does **not** start any conversation or display anything.
        The returned agent can be driven however the caller wants (interactive
        loop, single prompt via :meth:`handle_prompt`, tool-based invocation, etc.).

        The sub-agent is built from ``agents/<sub_name>.yaml``, inherits the parent's
        Ollama host and context length, gets an augmented system prompt (cwd listing +
        AGENTS.md) from :meth:`AgentType._build_system_prompt`, and has its tool schemas
        filtered by its own ``agent_tools``.

        Args:
            sub_name: The YAML file stem (e.g. ``"analyst"`` from ``/sub analyst``).
            parent_agent: The calling agent — used for the Ollama host and context length.
            tool_schemas: All available tool schemas passed through to :meth:`filter_tool_schemas`.
                          If ``None``, defaults to all tools (equivalent to ``["*"]``).
            extra_tools: Additional function_def dicts added after filtering. Useful for
                         runtime-injected tools like ``complete_task`` without modifying
                         agent YAML files.

        Returns:
            A fully-constructed :class:`Agent` instance ready for prompting.

        Raises:
            FileNotFoundError: If the YAML file or its base system prompt file is missing and no
                               inline fallback was provided in the YAML.
            ValueError: If required fields are absent or malformed in the YAML.
        """
        from pathlib import Path
        from agent.types import AgentType

        yaml_path = Path("agents") / f"{sub_name}.yaml"
        # ``AgentType.from_file`` now builds the augmented system prompt internally,
        # so no extra work is needed here.
        agent_type = AgentType.from_file(str(yaml_path))

        # Reuse the parent's Ollama client host and context window.
        if parent_agent is None:
            from agent.core import CURRENT_AGENT
            parent_agent = CURRENT_AGENT.get()
        if parent_agent is None:
            raise RuntimeError(
                "No sub-agent name provided and no current agent in context. "
                "Pass sub_name or call run_subagent from within a handle_prompt loop."
            )
        client = ollama.Client(host=parent_agent._ollama_host)
        context_length = parent_agent._context_length

        if tool_schemas is None:
            from tools import AGENT_TOOLS
            tool_schemas = AGENT_TOOLS

        return cls(
            agent_type=agent_type,
            ollama_client=client,
            context_length=context_length,
            tool_schemas=tool_schemas,
            extra_tools=extra_tools,
        )

    def summarize(self, summary_prompt: Optional[str] = None) -> str:
        """Ask the LLM to summarise the conversation accumulated so far.

        Builds a temporary message list from recent history and appends a
        summary prompt.  The resulting turn is *not* persisted in ``self.messages``
        — the agent's own history remains untouched.

        Args:
            summary_prompt: Optional override for how to summarise. If provided,
                this replaces the default "expert summarizer" system message and
                user instruction, letting the caller specify any custom guidance.

        Returns:
            A string containing the generated summary, or an empty string on
            failure.
        """
        
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
            messages = [ {
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
        
        return self._chat(messages)
