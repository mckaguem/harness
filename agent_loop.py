"""Main conversation loop — drives chat with Ollama and dispatches tool calls."""

import json
from dataclasses import dataclass
from typing import Generator

import ollama

from terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_error,
    display_agent_response,
)
from commands import COMMANDS
from tools.dispatcher import dispatch


# ---------------------------------------------------------------------------
# Output kinds yielded by ``handle_prompt``.
# ---------------------------------------------------------------------------

RESPONSE = "response"        # Final text from the LLM (no more tool calls).
TOOL_CALL = "tool_call"      # A function call request from the LLM.
TOOL_RESULT = "tool_result"  # The result of executing a tool.
ERROR = "error"              # An error that is not tied to a specific tool result.


# ---------------------------------------------------------------------------
# Shared state bundle passed into the Agent / handle_prompt machinery.
# ---------------------------------------------------------------------------

@dataclass
class RunContext:
    """Runtime context shared across agent turns."""
    ollama_client: "ollama.Client"
    model_name: str
    agent_tools: list
    context_length: int


# ---------------------------------------------------------------------------
# Agent — owns the conversation and processes one user prompt to completion.
# ---------------------------------------------------------------------------

class Agent:
    """Owns the conversation state and handles a single user turn."""

    def __init__(self, system_prompt: str, ctx: RunContext):
        self._ctx = ctx
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

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
        self.messages.append({"role": "user", "content": user_input})

        while True:
            response = self._ctx.ollama_client.chat(
                model=self._ctx.model_name,
                messages=self.messages,
                tools=self._ctx.agent_tools,
                options={"num_ctx": self._ctx.context_length},
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

                self.messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name,
                })
                yield (TOOL_RESULT, func_name, result)


# ---------------------------------------------------------------------------
# Outer loop — runs outside the Agent class.
# ---------------------------------------------------------------------------

def run_loop(ollama_client: "ollama.Client", model_name: str,
             system_prompt: str, agent_tools: list, context_length: int) -> None:
    """Run the interactive chat loop.

    Args:
        ollama_client: An initialized Ollama client instance.
        model_name: The model identifier to use.
        system_prompt: System message prepended to every conversation.
        agent_tools: List of tool definitions (JSON-schema-like dicts).
        context_length: Model's context window size (0 if unknown).
    """
    ctx = RunContext(ollama_client=ollama_client, model_name=model_name,
                     agent_tools=agent_tools, context_length=context_length)
    agent = Agent(system_prompt, ctx)

    print_system(f"🚀 Agent Ready — {model_name}",
                 "Type a message to begin. Type /exit or /quit to stop.")

    while True:
        user_input = prompt_user()

        # Check for slash commands first.
        if user_input.startswith('/'):
            parts = user_input[1:].split(' ', 1)
            command_name = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ''

            handler = COMMANDS.get(command_name)
            if handler:
                result = handler(rest)
                if result is True:
                    break
                continue

        for output in agent.handle_prompt(user_input):
            kind = output[0]
            if kind == RESPONSE:
                _, content, ollama_response = output
                display_agent_response(content, ollama_response, ctx.context_length, None)
            elif kind == TOOL_CALL:
                _, func_name, args_str = output
                display_tool_call(func_name, args_str)
            elif kind == TOOL_RESULT:
                _, func_name, result = output
                display_tool_result(func_name, result)
            else:  # ERROR
                _, description = output
                display_error(description)
