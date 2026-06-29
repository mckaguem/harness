"""Agent class and AgentType definition."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Dict, Optional

import ollama
import yaml


# ---------------------------------------------------------------------------
# Output kinds yielded by ``handle_prompt``.
# ---------------------------------------------------------------------------

RESPONSE = "response"        # Final text from the LLM (no more tool calls).
TOOL_CALL = "tool_call"      # A function call request from the LLM.
TOOL_RESULT = "tool_result"  # The result of executing a tool.
ERROR = "error"              # An error that is not tied to a specific tool result.


# ---------------------------------------------------------------------------
# AgentType — definition of an agent (model, tools, system prompt).
# ---------------------------------------------------------------------------

@dataclass
class AgentType:
    """Definition of an agent — its model, tools, and system prompt."""
    
    model_name: str
    system_prompt: str
    agent_tools: List[str]  # List of tool names, or ["*"] for all
    
    @classmethod
    def from_file(cls, path: str) -> "AgentType":
        """Load agent definition from a YAML file.
        
        Expected format::
        
            model_name: "model/identifier"
            system_prompt_path: "system_prompt.txt"  # or use inline system_prompt
            agent_tools: [execute_bash, write_file]   # or ["*"] for all
        
        Args:
            path: Path to the YAML file.
            
        Returns:
            An AgentType instance.
        """
        yaml_path = Path(path)
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Agent definition file not found: {path}")
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        model_name = config.get("model_name")
        if not model_name:
            raise ValueError("YAML must contain 'model_name'")
        
        # Load system prompt from file or use inline text
        system_prompt_path = config.get("system_prompt_path", "system_prompt.txt")
        agent_tools = config.get("agent_tools", [])
        
        if not isinstance(agent_tools, list):
            raise ValueError("'agent_tools' must be a list of strings")
        
        # Load system prompt from file
        sys_prompt_file = Path(system_prompt_path)
        if sys_prompt_file.is_file():
            system_prompt = sys_prompt_file.read_text(encoding="utf-8").strip()
        else:
            # Use inline system_prompt if provided
            system_prompt = config.get("system_prompt", "")
        
        return cls(
            model_name=model_name,
            system_prompt=system_prompt,
            agent_tools=agent_tools
        )


# ---------------------------------------------------------------------------
# Tool schema filtering.
# ---------------------------------------------------------------------------

def filter_tool_schemas(agent_type: AgentType, all_schemas: List[Dict]) -> List[Dict]:
    """Filter tool schemas to include only those named in ``agent_type.agent_tools``.
    
    If ``agent_type.agent_tools`` contains ``"*"``, all schemas are returned.
    Otherwise, only schemas whose ``function.name`` is in the list are kept.
    
    Args:
        agent_type: The agent definition specifying which tools to use.
        all_schemas: All available tool schema dicts (each must have a 
                     ``"function"`` key with a ``"name"`` field).
                     
    Returns:
        Filtered list of tool schemas.
        
    Raises:
        ValueError: If any name in ``agent_type.agent_tools`` is not in the 
                    available schemas (and the name is not ``"*"``).
    """
    if "*" in agent_type.agent_tools:
        return all_schemas
    
    # Build a lookup of name -> schema for fast matching.
    name_to_schema = {schema["function"]["name"]: schema for schema in all_schemas}
    
    requested_names = set(agent_type.agent_tools)
    
    missing = requested_names - name_to_schema.keys()
    if missing:
        raise ValueError(
            f"AgentType '{agent_type.model_name}' requests tools "
            f"{sorted(missing)} that are not available."
        )
    
    return [name_to_schema[name] for name in agent_type.agent_tools]


# ---------------------------------------------------------------------------
# Agent — owns the conversation and processes one user prompt to completion.
# ---------------------------------------------------------------------------

class Agent:
    """Owns the conversation state and handles a single user turn."""
    
    def __init__(self, 
                 agent_type: AgentType, 
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
        
        # Filter tool schemas based on AgentType.
        if tool_schemas:
            self._tools = filter_tool_schemas(agent_type, tool_schemas)
        else:
            self._tools = []
        
        self.messages: list[dict] = [{"role": "system", "content": agent_type.system_prompt}]
    
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
        
        self.messages.append({"role": "user", "content": user_input})
        
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
