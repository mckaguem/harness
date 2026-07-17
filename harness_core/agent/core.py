"""Agent class — owns the conversation and processes one user prompt to completion."""

import json
import os
from typing import (Any, Dict, Generator, Optional, TYPE_CHECKING)

if TYPE_CHECKING:
    from harness_core.agent.types import AgentType
    from harness_core.agent.task_list import TaskList

from harness_core.model.provider import Provider

from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.session.session import Session
from harness_core.eventbus import generate_unique_id, EventPublisher, event_bus

from harness_core.tools.dispatcher import dispatch
from harness_core.tools.tool_result import ToolResult


class Agent(EventPublisher):
    """Owns the conversation state and handles a single user turn."""
    
    def __init__(self,
                 agent_type: "AgentType",
                 id: str,
                 tool_schemas: list[Dict] | None = None,
                 extra_tools: list[Dict] | None = None):
        """Initialize an Agent.

        Args:
            agent_type: The agent definition (model, system prompt, tools).
            id: Mandatory explicit identifier for this agent. The agent id
                becomes ``"Agent.{id}"``.
            tool_schemas: Optional list of tool schemas to filter against the
                agent type's allowed tools.
            extra_tools: Optional list of extra tool schemas to append (e.g.
                runtime-injected ones like submit_results).
        """
        self._agent_type = agent_type
        self._id = f"Agent.{id}"

        # Initialize the event publisher base so the agent can publish events.
        super().__init__(event_bus, self._id)

        self._provider: Optional[Provider] = None
        if hasattr(agent_type, 'provider_config') and agent_type.provider_config is not None:
            try:
                self._provider = Provider.get_or_create(agent_type.provider_config)
            except Exception as exc:
                print(f"Warning: Failed to resolve provider for '{agent_type.name}': {exc}")

        # Filter tool schemas based on AgentType.
        from harness_core.agent.utils import filter_tool_schemas
        if tool_schemas:
            self._tools = filter_tool_schemas(agent_type, tool_schemas)
        else:
            self._tools = []
        
        # Append any extra tools (e.g. runtime-injected ones like submit_results).
        if extra_tools:
            self._tools.extend(extra_tools)

        # Cache-friendly task state management — all dynamic state is injected
        # at the tail end of messages, never touching messages[0].
        from harness_core.agent.task_list import TaskList
        task_list_id = self._id[len("Agent."):] if self._id.startswith("Agent.") else self._id
        self._task_list: TaskList | None = TaskList(id=task_list_id, sender_id=self._id)

        # Conversation state is now owned by the Session object.
        self._session = Session(
            system_prompt=agent_type.system_prompt,
            task_list=self._task_list,
            provider=self._provider,
            model_name=self._agent_type.provider_model_name,
            agent_type_name=agent_type.name,
        )

        self._max_loops: int = 100  # Safety ceiling to prevent infinite loops

    # -- task list access --------------------------------------------------

    @property
    def id(self) -> str:
        """Unique identifier for this agent (prefixed with 'Agent.')."""
        return self._id

    @property
    def task_list(self) -> "Optional[TaskList]":
        """Public accessor for the agent's task list."""
        return self._task_list

    @property
    def provider(self):
        """Public accessor for the Provider instance."""
        return self._provider

    @property
    def context_length(self) -> int:
        """Public accessor for the model's context window size, derived from the agent type's model config."""
        return self._agent_type.context_length

    @property
    def session(self) -> "Session":
        """Public accessor for the underlying Session object."""
        return self._session

    @property
    def messages(self) -> list[dict]:
        """Public accessor for the session's message list."""
        return self._session.messages
    
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
        """Send *messages* to the provider and return a normalized response dict.

        Timing data (duration_ms) is injected by this method. All other normalization
        is handled inside :meth:`Provider._normalize_response`.
        """
        import time
        start_time = time.time()

        if self._provider is None:
            raise RuntimeError("No provider configured for this agent.")

        try:
            response = self._provider.chat_completion(
                messages=messages,
                model=self._agent_type.provider_model_name,
                tools=self._tools if self._tools else None,
            )
        except Exception as exc:
            raise RuntimeError(f"Provider chat request failed: {exc}") from exc

        # Inject agent-specific display name and timing. The provider already returns
        # the normalized shape with choices/usage/message/reasoning/pre_tool_content.
        response["model"] = self._agent_type.model_name
        end_time = time.time()
        response["duration_ms"] = (end_time - start_time) * 1000

        return response

    # -- public API ----------------------------------------------------------

    def handle_prompt(self, user_input: str) -> Generator[tuple[str, Any, Any, Optional[dict[str, Any]]], None, None]:
        """Process a single user prompt to completion.
        
        Yields tuples of ``(kind, ...)`` where ``kind`` is one of
        :data:`RESPONSE`, :data:`TOOL_CALL`, :data:`TOOL_RESULT` or
        :data:`ERROR`.  The agent dispatches and executes each tool internally;
        it never calls display functions itself.
        
        Yields::
        
            (RESPONSE,         content, openai_response)
            (TOOL_CALL,        func_name, args_str, response_data)
            (TOOL_RESULT,      func_name, result, response_data)
            (ERROR,            description)
        """
        # 1. Prepend any injected text to the user input, then clear queue
        injected = self._session.consume_injected_text()
        effective_input = (
            f"{injected}\n\n{user_input}" if injected is not None else user_input
        )

        # 2. Build message dict and prepare it (inject task state BEFORE adding to list)
        user_msg_dict = {"role": "user", "content": effective_input}
        prepared = self._session.prepare_message_for_injection(user_msg_dict)
        self._session.add_user_message(prepared["content"])
        
        # 3. Loop as before, but use session methods instead of self.messages.append() etc.
        loop_count = 0
        while True:
            if loop_count >= self._max_loops:
                yield (ERROR, f"Maximum loop count ({self._max_loops}) exceeded. Breaking out of handle_prompt.", None, None)
                break
            loop_count += 1

            messages_to_send = self._session.get_messages()
            response = self._chat(messages_to_send)

            # Provider-normalized shape: ``response["choices"][0]["message"]``.
            message = response["choices"][0]["message"]
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
                                     
                    continue
                    
                else:
                    content = message.get("content", "")
                    yield (RESPONSE, content, response, None)
                    break
            
            pending_parallel = []
            use_parallel = (
                len([tc for tc in message["tool_calls"] if tc["function"]["name"] == "run_subagent"]) > 1
            )

            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                raw_args = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
                
                # Attempt to parse JSON; if it fails, treat as an error and continue.
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError as exc:
                    description = f"Tool call argument parsing failed: {exc}"
                    error_result = ToolResult(
                        llm_text=description, display_text=description,
                        type_tag="text", title=f"Error: {func_name}", theme="error",
                    )
                    # Record the tool result (error) in the session.
                    self._session.add_tool_result(func_name, error_result.llm_text, tool_call["id"])
                    # Yield an error event and skip further processing of this tool call.
                    yield (ERROR, description, None, None)
                    # Continue to next tool call (or next loop iteration).
                    continue
                
                # Termination circuit breaker (Component 4): block submit_results if tasks remain.
                if func_name == "submit_results" and self._task_list and self._task_list.has_incomplete_tasks():
                    content = (
                        "[SYSTEM ERROR] Execution termination blocked. "
                        "You still have incomplete tasks in your state machine. "
                        "You must finish them or update their status to 'failed' "
                        "before you can invoke submit_results."
                    )
                    block_result = ToolResult(
                        llm_text=content, display_text=content,
                        type_tag="text", title=f"Error: submit_results", theme="error",
                    )
                    # This is a user-role message from the executor — also wrap with prepare_message_for_injection
                    inner_block_dict = {"role": "user", "content": content}
                    prepared_inner = self._session.prepare_message_for_injection(inner_block_dict)
                    self._session.add_user_message(prepared_inner["content"])
                    yield (TOOL_RESULT, func_name, block_result, response)
                    continue
                                
                yield (TOOL_CALL, func_name, raw_args, response)

                # Defer execution of multiple run_subagent calls to a single
                # concurrent batch after this loop (keeps them in parallel).
                if use_parallel and func_name == "run_subagent":
                    pending_parallel.append((tool_call, args))
                    continue

                # Execute the tool directly via dispatch and handle its result.
                try:
                    return_result = dispatch(func_name, args, self)
                except KeyError:
                    description = f"Unknown function '{func_name}'."
                    yield (ERROR, description, None, None)
                    continue
                except Exception as exc:
                    # Handle unexpected errors (e.g., wrong args to tool)
                    description = f"Error calling {func_name}: {exc}"
                    yield (ERROR, description, None, None)
                    continue

                assert isinstance(return_result, ToolResult), "dispatch() must return a ToolResult"

                # Use session.add_tool_result instead of self.messages.append({"role":"tool",...})
                self._session.add_tool_result(func_name, return_result.llm_text, tool_call_id)
                yield (TOOL_RESULT, func_name, return_result, response)

            # Run any deferred run_subagent calls concurrently and feed each
            # result back into the conversation for the next model round.
            if pending_parallel:
                from harness_core.tools.run_subagent import run_subagents_parallel

                parallel_calls = [
                    (args.get("sub_agent", ""), args.get("task", ""))
                    for _tc, args in pending_parallel
                ]
                parallel_results = run_subagents_parallel(parallel_calls)
                for (tool_call, _args), result in zip(pending_parallel, parallel_results):
                    self._session.add_tool_result(
                        "run_subagent", result.llm_text, tool_call["id"]
                    )
                    yield (TOOL_RESULT, "run_subagent", result, response)

    def user_loop(self, on_exit=None) -> None:
        """Run the interactive command loop for this agent.

        Delegates to the module-level ``user_loop`` driver in
        ``harness_core.agent.loop``, passing this agent instance as the
        target. This lets callers (e.g. the TUI) use a uniform interface
        without reaching into the agent internals.

        Args:
            on_exit: Optional callback invoked just before the loop exits.
                Receives ``(agent, messages)``.
        """
        from harness_core.agent.loop import user_loop

        user_loop(self, on_exit=on_exit)

    @classmethod
    def from_agent_name(cls, agent_name: str,
                        tool_schemas: list[Dict] | None = None,
                        extra_tools: list[Dict] | None = None) -> "Agent":
        """Build and return a configured ``Agent`` for the named agent.

        Pure factory — does **not** start any conversation or display anything.
        The returned agent can be driven however the caller wants (interactive
        loop, single prompt via :meth:`handle_prompt`, tool-based invocation, etc.).

        It builds a configured Agent by name: looks up the agent YAML via the
        discovery path (:func:`agent.discovery.get_agent_yaml`, which searches
        project and global config paths with project taking precedence), loads the
        agent type (which carries the model, provider, and context_length resolved
        from the model config), filters the tool schemas, and returns the agent.

        Args:
            agent_name: The YAML file stem (e.g. ``"analyst"`` or ``"main"``).
            tool_schemas: All available tool schemas passed through to
                          :meth:`filter_tool_schemas`. If ``None``, defaults to all
                          tools (equivalent to ``["*"]``).
            extra_tools: Additional function_def dicts added after filtering. Useful for
                         runtime-injected tools like ``submit_results`` without modifying
                         agent YAML files.

        Returns:
            A fully-constructed :class:`Agent` instance ready for prompting.

        Raises:
            FileNotFoundError: If no matching agent YAML is found in any configured discovery path.
        """
        from harness_core.agent.discovery import get_agent_yaml
        from harness_core.agent.types import AgentType
        from harness_core.tools import AGENT_TOOLS

        # Resolve the named agent YAML via project/global discovery paths.
        yaml_path_str, error_msg = get_agent_yaml(agent_name)
        if yaml_path_str is None:
            raise FileNotFoundError(error_msg)

        # Load the agent type — handles YAML parsing, provider resolution,
        # and system prompt template substitution (CWD, SKILLS, AGENTS, TOOLS).
        agent_type = AgentType.from_file(str(yaml_path_str))

        if tool_schemas is None:
            tool_schemas = AGENT_TOOLS

        return cls(
            agent_type=agent_type,
            id=agent_name,
            tool_schemas=tool_schemas,
            extra_tools=extra_tools,
        )


