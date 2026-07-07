"""Agent class — owns the conversation and processes one user prompt to completion."""

import json
import os
from typing import Dict, Generator, List, Optional, TYPE_CHECKING
from pprint import pprint

if TYPE_CHECKING:
    from agent.task_list import TaskList

from openai import OpenAI

from agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from agent.context import CURRENT_AGENT
from agent.session import Session


class Agent:
    """Owns the conversation state and handles a single user turn."""
    
    def __init__(self, 
                 agent_type: "AgentType", 
                 openai_client: "OpenAI",
                 context_length: int,
                 tool_schemas: Optional[List[Dict]] = None,
                 extra_tools: Optional[List[Dict]] = None):
        """Initialize an Agent.
        
        Args:
            agent_type: The agent definition (model, system prompt, tools).
            openai_client: An initialized OpenAI client.
            context_length: Model's context window size.
            tool_schemas: All available tool schema dicts. If provided, the 
                         agent will only expose the schemas whose names are in 
                         ``agent_type.agent_tools`` (or all if ``"*"`` is used).
            extra_tools: Additional function_def dicts that should be added to
                         the filtered tool list regardless of YAML constraints.
                         Useful for tools injected at runtime (e.g. ``submit_results``
                         in sub-agent sessions) without modifying agent YAML files.
        """
        self._agent_type = agent_type
        self._client = openai_client
        self._context_length = context_length
        
        # Resolve base URL, stripping trailing /v1 if present (OpenAI-compatible URLs).
        raw_host = getattr(openai_client, "base_url", None) or os.environ.get("OPENAI_BASE_URL", "")
        self._base_url = str(raw_host).rstrip("/") if raw_host else ""

        # Filter tool schemas based on AgentType.
        from agent.utils import filter_tool_schemas
        if tool_schemas:
            self._tools = filter_tool_schemas(agent_type, tool_schemas)
        else:
            self._tools = []
        
        # Append any extra tools (e.g. runtime-injected ones like submit_results).
        if extra_tools:
            self._tools.extend(extra_tools)

        # Tool execution pipeline — handles dispatch, error wrapping, and termination blocking.
        from agent.executor import ToolExecutor
        self._executor = ToolExecutor(agent_type.name)

        # Cache-friendly task state management — all dynamic state is injected
        # at the tail end of messages, never touching messages[0].
        from agent.task_list import TaskList
        self._task_list: Optional[TaskList] = TaskList()

        # Conversation state is now owned by the Session object.
        self._session = Session(agent_type.system_prompt, self._task_list)

        self._max_loops: int = 30  # Safety ceiling to prevent infinite loops

        # Bind this instance as the current agent in the thread context so tools
        # can spawn sub-agents without an explicit parent reference.
        CURRENT_AGENT.set(self)

    # -- task list access --------------------------------------------------

    @property
    def task_list(self) -> "TaskList":
        """Public accessor for the agent's task list."""
        return self._task_list

    @property
    def client(self):
        """Public accessor for the OpenAI client instance (kept for backward compatibility)."""
        return self._client

    @property
    def context_length(self) -> int:
        """Public accessor for the model's context window size."""
        return self._context_length
    
    # -- injection API -------------------------------------------------------

    def inject_text(self, s: str) -> None:
        """Queue *s* to be prepended to the next user input.

        The text is wrapped in a delimiter so that when it is injected into the
        conversation the agent (and any downstream logic) can tell it apart from
        genuine user input.

        Args:
            s: The string to inject. Leading/trailing whitespace is preserved.
        """
        self._session.inject_text(s)

    # -- internal helpers ----------------------------------------------------

    def _chat(self, messages: list[dict]) -> dict:
        """Send *messages* to the OpenAI client and return a normalized response dict.

        Normalizes both legacy Ollama-style dicts and OpenAI ChatCompletion objects so that
        callers can consistently do::

            resp = self._chat(messages)
            message = resp["message"]  # has .content, .tool_calls
            usage = resp.get("usage")   # has prompt_tokens, etc.
        """
        if hasattr(self._client, 'chat') and hasattr(self._client.chat, 'completions'):
            kwargs: dict = {
                "model": self._agent_type.model_name,
                "messages": messages,
                "tools": self._tools if self._tools else None,
            }

            try:
                completion = self._client.chat.completions.create(**{k: v for k, v in kwargs.items() if v is not None})
            except Exception as exc:
                raise RuntimeError(f"OpenAI chat request failed: {exc}") from exc

            choice = completion.choices[0]
            message_obj = choice.message  # ChatCompletionMessage with .content and .tool_calls

            # Build a dict that mirrors Ollama's shape so callers don't need changes.
            resp_dict: dict = {
                "message": {
                    "role": message_obj.role or "assistant",
                    "content": message_obj.content,
                },
                "model": completion.model,
                "usage": {
                    "prompt_tokens": (completion.usage.prompt_tokens if completion.usage else None),
                    "completion_tokens": (completion.usage.completion_tokens if completion.usage else None),
                    "total_tokens": (completion.usage.total_tokens if completion.usage else None),
                },
            }

            if message_obj.tool_calls:
                resp_dict["message"]["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message_obj.tool_calls 
                ] 

            return resp_dict
        else:
            # Legacy Ollama fallback.
            raise NotImplementedError(
                "Only OpenAI clients are supported in this build."
            )
    
    # -- public API ----------------------------------------------------------
    
    def handle_prompt(self, user_input: str) -> Generator[tuple[str, ...], None, None]:
        """Process a single user prompt to completion.
        
        Yields tuples of ``(kind, ...)`` where ``kind`` is one of
        :data:`RESPONSE`, :data:`TOOL_CALL`, :data:`TOOL_RESULT` or
        :data:`ERROR`.  The agent dispatches and executes each tool internally;
        it never calls display functions itself.
        
        Yields::
        
            (RESPONSE,         content, openai_response)
            (TOOL_CALL,        func_name, args_str)
            (TOOL_RESULT,      func_name, result)
            (ERROR,            description)
        """
        # 1. Prepend any injected text to the user input, then clear queue
        effective_input = user_input
        if self._session._injected_text is not None:
            effective_input = f"{self._session._injected_text}\n\n{user_input}"
            self._session._injected_text = None

        # 2. Build message dict and prepare it (inject task state BEFORE adding to list)
        user_msg_dict = {"role": "user", "content": effective_input}
        prepared = self._session.prepare_message_for_injection(user_msg_dict)
        self._session.add_user_message(prepared["content"])
        
        # 3. Loop as before, but use session methods instead of self.messages.append() etc.
        loop_count = 0
        while True:
            if loop_count >= self._max_loops:
                yield (ERROR, f"Maximum loop count ({self._max_loops}) exceeded. Breaking out of handle_prompt.")
                break
            
            messages_to_send = self._session.get_messages()
            response = self._chat(messages_to_send)
            
            message = response["message"]
            self._session.add_assistant_message(message)
            
            if not message.get("tool_calls"):
                if self._task_list and self._task_list.has_incomplete_tasks():
                    block_content = """
[SYSTEM ERROR] Execution termination blocked.
You still have incomplete tasks in your tasks list.
You must finish them and update their status to 'complete',
or update their status to 'failed' before stopping.
"""

                    # Wrap with prepare_message_for_injection to match old behavior
                    block_dict = {"role": "user", "content": block_content}
                    prepared_block = self._session.prepare_message_for_injection(block_dict)
                    self._session.add_user_message(prepared_block["content"])
                    
                    print("incomplete tasks!")
                                     
                    continue
                    
                else:
                    content = message.get("content", "")
                    yield (RESPONSE, content, response)
                    break
            
            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
                
                # Termination circuit breaker (Component 4): block submit_results if tasks remain.
                if func_name == "submit_results" and self._task_list and self._task_list.has_incomplete_tasks():
                    block_info = self._executor.make_submit_results_block(True)
                    if block_info:
                        # This is a user-role message from the executor — also wrap with prepare_message_for_injection
                        inner_block_dict = {"role": "user", "content": block_info["content"]}
                        prepared_inner = self._session.prepare_message_for_injection(inner_block_dict)
                        self._session.add_user_message(prepared_inner["content"])
                        yield (TOOL_RESULT, func_name, block_info["result"])
                        loop_count += 1
                        continue
                
                try:
                    if func_name == "initialize_task_list":
                        args_str = ""
                    else:
                        args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)
                
                yield (TOOL_CALL, func_name, args_str)

                # Execute the tool via the executor and handle its result.
                try:
                    return_result = self._executor.execute(func_name, args)
                except KeyError:
                    description = f"Unknown function '{func_name}'."
                    return_result = self._executor.make_error_result(func_name, description)
                    yield (ERROR, description)
                except Exception as exc:
                    # Handle unexpected errors (e.g., wrong args to tool)
                    description = f"Error calling {func_name}: {exc}"
                    return_result = self._executor.make_error_result(func_name, description)
                    yield (ERROR, description)
                
                # Use session.add_tool_result instead of self.messages.append({"role":"tool",...})
                self._session.add_tool_result(func_name, return_result.llm_text)
                yield (TOOL_RESULT, func_name, return_result)

    @classmethod
    def spawn_subagent(cls, sub_name: str, parent_agent: Optional["Agent"] = None,
                       tool_schemas: Optional[List[Dict]] = None,
                       extra_tools: Optional[List[Dict]] = None):
        """Build and return a configured ``Agent`` for the named sub-agent.

        Pure factory — does **not** start any conversation or display anything.
        The returned agent can be driven however the caller wants (interactive
        loop, single prompt via :meth:`handle_prompt`, tool-based invocation, etc.).

        The sub-agent is looked up via :func:`agent.discovery.get_agent_yaml`, which
        searches project and global config paths (``cwd/.harness_py/agents/`` then
        ``~/.harness_py/agents/``, with project taking precedence). It inherits the parent's
        base URL and context length, gets an augmented system prompt (cwd listing +
        AGENTS.md) from :meth:`AgentType._build_system_prompt`, and has its tool schemas
        filtered by its own ``agent_tools``.

        Args:
            sub_name: The YAML file stem (e.g. ``"analyst"`` from ``/sub analyst``).
            parent_agent: The calling agent — used for the base URL and context length.
            tool_schemas: All available tool schemas passed through to :meth:`filter_tool_schemas`.
                          If ``None``, defaults to all tools (equivalent to ``["*"]``).
            extra_tools: Additional function_def dicts added after filtering. Useful for
                         runtime-injected tools like ``submit_results`` without modifying
                         agent YAML files.

        Returns:
            A fully-constructed :class:`Agent` instance ready for prompting.

        Raises:
            FileNotFoundError: If no matching agent YAML is found in any configured discovery path.
        """
        from pathlib import Path
        from agent.types import AgentType
        from agent.discovery import get_agent_yaml

        yaml_path_str, error_msg = get_agent_yaml(sub_name)
        if yaml_path_str is None:
            raise FileNotFoundError(error_msg)
        
        # ``AgentType.from_file`` now builds the augmented system prompt internally,
        # so no extra work is needed here.
        agent_type = AgentType.from_file(str(yaml_path_str))

        # Reuse the parent's client host and context window.
        if parent_agent is None:
            from agent.context import CURRENT_AGENT
            parent_agent = CURRENT_AGENT.get()
        if parent_agent is None:
            raise RuntimeError(
                "No sub-agent name provided and no current agent in context. "
                "Pass sub_name or call run_subagent from within a handle_prompt loop."
            )
        client = OpenAI(base_url=parent_agent._base_url, api_key=os.environ.get("OPENAI_API_KEY", ""))
        context_length = parent_agent._context_length

        if tool_schemas is None:
            from tools import AGENT_TOOLS
            tool_schemas = AGENT_TOOLS

        return cls(
            agent_type=agent_type,
            openai_client=client,
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
        for msg in self._session.get_messages():
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
