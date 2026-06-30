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
                 tool_schemas: Optional[List[Dict]] = None):
        """Initialize an Agent.
        
        Args:
            agent_type: The agent definition (model, system prompt, tools).
            ollama_client: An initialized Ollama client.
            context_length: Model's context window size.
            tool_schemas: All available tool schema dicts. If provided, the 
                         agent will only expose the schemas whose names are in 
                         ``agent_type.agent_tools`` (or all if ``"*"`` is used).
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

        self.messages: list[dict] = [{"role": "system", "content": agent_type.system_prompt}]
        self._injected_text: Optional[str] = None

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
        
        while True:
            response = self._client.chat(
                model=self._agent_type.model_name,
                messages=self.messages,
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
                
                try:
                    args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)
                
                yield (TOOL_CALL, func_name, args_str)
                
                try:
                    result = dispatch(func_name, args)
                except KeyError as exc:
                    description = f"Unknown function '{func_name}'."
                    yield (ERROR, description)
                    result = description
                except Exception as exc:
                    # Handle unexpected errors (e.g., wrong args to tool)
                    description = f"Error calling {func_name}: {exc}"
                    yield (ERROR, description)
                    result = description
                
                self.messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name,
                })
                yield (TOOL_RESULT, func_name, result)

    @classmethod
    def spawn_subagent(cls, sub_name: str, parent_agent: Optional["Agent"] = None,
                       tool_schemas: Optional[List[Dict]] = None):
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
        )

    def summarize(self) -> str:
        """Ask the LLM to summarise the conversation accumulated so far.

        Builds a temporary message list from recent history and appends a
        summary prompt.  The resulting turn is *not* persisted in ``self.messages``
        — the agent's own history remains untouched.

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
    
        messages= [
            {
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
