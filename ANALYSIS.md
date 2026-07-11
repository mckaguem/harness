# Harness Provider & Agent Creation Analysis

## 1. Current Flow: harness.py → Provider Creation → Agent Init

**File:** `/workspaces/harness/harness.py` (lines 60-106)

```python
# Line 62: Resolve agents/main.yaml path
main_agent_path = resolve_config_path("agents/main.yaml")

# Line 70: Build agent definition from YAML (resolves provider_config internally)
agent_type = AgentType.from_file(str(main_agent_path))

# Lines 72-76: Validate that provider_config was resolved
if not agent_type.provider_config:
    sys.stderr.write(...)
    sys.exit(1)

# Line 80: Create a Provider from the resolved ProviderConfig
from model.provider import Provider
provider = Provider.from_config(agent_type.provider_config)

# Lines 96-99: Detect context_length from provider, fallback to default (2^17)
try:
    context_length = provider.get_context_length(agent_type.model_name) or 2**17
except Exception:
    context_length = 2**17

# Lines 101-106: Instantiate Agent with all required parameters
agent = Agent(
    agent_type=agent_type,
    provider=provider,
    context_length=context_length,
    tool_schemas=AGENT_TOOLS,  # pass all schemas so filter_tool_schemas can work
)

# Line 108: Start interactive user loop
user_loop(agent)
```

**Key observations:**
- `harness.py` currently does **three separate steps** to create an Agent:
  1. Load YAML → `AgentType.from_file()` (which internally resolves provider_config via config.py)
  2. Convert ProviderConfig → Provider instance via `Provider.from_config()`
  3. Build context_length from the provider

- The **simplification opportunity**: `Agent.__init__` already accepts an `agent_type` with a `provider_config`. Since `Agent.__init__` can derive `_base_url` from the provider, and since sub-agent spawning has a fallback mechanism (`_build_subagent_provider`) that works when no explicit Provider is passed, there may be room to simplify harness.py by having it pass only what's needed.

---

## 2. Agent.__init__ Signature & Parameter Details

**File:** `/workspaces/harness/agent/core.py` (lines 51-90)

```python
def __init__(self, 
             agent_type: "AgentType", 
             provider: Provider,
             context_length: int,
             tool_schemas: Optional[List[Dict]] = None,
             extra_tools: Optional[List[Dict]] = None):
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_type` | `"AgentType"` | The agent definition containing model name, system prompt, tools config, and **provider_config** (ProviderConfig dataclass) |
| `provider` | `Provider` | An instantiated Provider object (OpenAIProvider or OllamaProvider) for LLM communication. Stored as `self._provider`. |
| `context_length` | `int` | Model's context window size in tokens. Used for context management. |
| `tool_schemas` | `Optional[List[Dict]]` | All available tool schema dicts (from tools). If provided, filters by `agent_type.agent_tools`. Defaults to empty list if None. |
| `extra_tools` | `Optional[List[Dict]]` | Additional function_def dicts injected at runtime (e.g., `submit_results`). Added after filtering. |

**What __init__ does internally:**
- Line 71: Stores agent_type as `self._agent_type`
- Line 72: Stores provider as `self._provider`
- Line 73: Stores context_length as `self._context_length`
- Lines 76-79: **Derives `_base_url` from the provider** via `provider.get_base_url().rstrip("/")`. Falls back to empty string on failure.
- Lines 82-84: Filters tool schemas based on agent_type's `agent_tools` config (or all if `"*"`).
- Line 90: Extends tools with extra_tools (runtime-injected)
- Line 93-94: Creates ToolExecutor for the agent's name
- Line 98-99: Initializes TaskList (dynamic state management)

**Critical insight:** The `agent_type` already contains a `provider_config` attribute. This is the `ProviderConfig` dataclass that holds provider type, base_url, api_key, and default_model — essentially **what's needed to construct a Provider**. But currently harness.py explicitly converts it to a Provider instance before passing it in.

---

## 3. spawn_subagent() Flow & _build_subagent_provider Helper

**File:** `/workspaces/harness/agent/core.py` (lines 17-45, then lines 338-409)

### `_build_subagent_provider()` — Lines 17-45

```python
def _build_subagent_provider(agent_type, parent_agent):
    """Build a Provider instance for a sub-agent.

    Uses the agent type's provider_config if available, otherwise falls back to
    constructing one from the parent agent's base URL and OpenAI API key.
    """
    # Try using provider config from agent type if it has one
    if hasattr(agent_type, 'provider_config') and agent_type.provider_config is not None:
        try:
            return Provider.from_config(agent_type.provider_config)  # Line 26
        except Exception as exc:
            print(f"Warning: Failed to create provider from config: {exc}")

    # Fall back to using OpenAI-compatible setup based on parent's base URL
    from openai import OpenAI as _OpenAIClient  # Line 31

    client = _OpenAIClient(
        base_url=parent_agent._base_url,
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    )

    # Create a minimal provider config and use it to build the provider
    class MinimalProviderConfig:  # Lines 39-45
        def __init__(self):
            self.provider_type = 'openai'
            self.base_url = parent_agent._base_url
            self.api_key = os.environ.get("OPENAI_API_KEY", "")

    return Provider.from_config(MinimalProviderConfig())
```

**Note:** The docstring says "otherwise falls back to constructing one from the parent agent's base URL and OpenAI API key" — but the actual code constructs a `MinimalProviderConfig` (an inline class with just 3 attributes) and passes it to `Provider.from_config()`. This is because `Provider.from_config()` only requires `provider_type`, `base_url`, and optional `api_key` — matching the ProviderConfig dataclass interface.

### `Agent.spawn_subagent()` — Lines 338-409

```python
def spawn_subagent(cls, sub_name: str, parent_agent: Optional["Agent"] = None,
                   tool_schemas: Optional[List[Dict]] = None,
                   extra_tools: Optional[List[Dict]] = None):
```

**What it receives:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `sub_name` | `str` | YAML file stem (e.g., "analyst") — used to locate agent YAML |
| `parent_agent` | `Optional[Agent]` | Calling agent for base URL/context length inheritance. If None, falls back to `CURRENT_AGENT.get()` from contextvars. |
| `tool_schemas` | `Optional[List[Dict]]` | Tool schemas passed through to filter_tool_schemas. Defaults to all AGENT_TOOLS if None. |
| `extra_tools` | `Optional[List[Dict]]` | Additional function_def dicts added after filtering (e.g., submit_results for sub-agent sessions). |

**What it does internally:**
1. **Lines 369-375**: Discovers agent YAML via `get_agent_yaml(sub_name)`. Raises FileNotFoundError if not found.
2. **Line 379**: Loads the agent definition: `agent_type = AgentType.from_file(str(yaml_path_str))` — this also builds system_prompt and resolves provider_config internally.
3. **Lines 381-395**: Resolves provider:
   - If parent has `_provider` set, reuse it (line 392-393)
   - Otherwise, call `_build_subagent_provider(agent_type, parent_agent)` (line 395)
4. **Lines 397**: Inherits context_length from parent
5. **Lines 399-401**: If no tool_schemas given, defaults to `AGENT_TOOLS` (all tools)
6. **Lines 403-409**: Returns a new Agent instance:
   ```python
   return cls(
       agent_type=agent_type,
       provider=new_provider,
       context_length=context_length,
       tool_schemas=tool_schemas,
       extra_tools=extra_tools,
   )
   ```

**Returns:** A fully-constructed `Agent` instance ready for prompting (does NOT start conversation).

---

## 4. AgentType.from_file() & ProviderConfig Resolution

**File:** `/workspaces/harness/agent/types.py` (lines 195-285)

### from_file classmethod — Lines 195-285

```python
@classmethod
def from_file(cls, path: str) -> "AgentType":
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Agent definition file not found: {path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    name = config.get("name", Path(path).stem)  # fall back to filename stem
    model_name = config.get("model_name")
    if not model_name:
        from config import get_default_model
        default_model = get_default_model()
        if default_model is None:
            raise ValueError(...)
        model_name = default_model

    # Resolve provider_config based on YAML 'provider' key or fallback. (Lines 216-225)
    from config import get_provider_config, get_default_provider
    yaml_provider = config.get("provider")
    if yaml_provider:
        resolved_provider = get_provider_config(yaml_provider)
        if resolved_provider is None:
            # Fall back to default provider if the specified one doesn't exist
            resolved_provider = get_default_provider()  # Line 223
    else:
        resolved_provider = get_default_provider()  # Line 225

    agent_tools = config.get("agent_tools", [])
    system_prompt_raw = config.get("system_prompt")
    # ... validation ...

    # Lines 271-277: Build augmented system prompt with discovered skills/agents/tools
    system_prompt = cls._build_system_prompt(
        raw_prompt=system_prompt_raw,
        skills=discovered_skills if discovered_skills else None,
        agents=agent_descriptions if agent_descriptions else None,
        tools=AGENT_TOOLS if AGENT_TOOLS else None,
    )

    # Line 279-285: Return the constructed AgentType with resolved_provider
    return cls(
        name=name,
        model_name=model_name,
        system_prompt=system_prompt,
        provider_config=resolved_provider,  # <-- This is a ProviderConfig instance
        agent_tools=agent_tools,
    )
```

**What from_file returns after resolving:**
- An `AgentType` instance with:
  - `name`: Agent name (from YAML or filename stem)
  - `model_name`: Model to use (from YAML or default_model config)
  - `system_prompt`: Augmented system prompt with skills/agents/tools context
  - **`provider_config`**: A `ProviderConfig` dataclass instance (or None if not resolvable — but currently the code always sets it via fallback)
  - `agent_tools`: List of allowed tool names

**Key insight:** The `AgentType.from_file()` method **always resolves provider_config to a ProviderConfig instance**. It never leaves it as None in normal flow. This means the parent's `_build_subagent_provider` will almost always hit the first branch (line 24-26) and successfully create a Provider from config.

---

## 5. ProviderConfig Dataclass Definition

**File:** `/workspaces/harness/model/types.py` (lines 17-23)

```python
@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str  # unique identifier for the provider
    provider_type: str  # "openai", "ollama", etc.
    base_url: str
    api_key: Optional[str] = None
    default_model: Optional[str] = None
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Unique identifier for the provider (used as key in config dict) |
| `provider_type` | `str` | Yes | Type discriminator: "openai", "ollama", etc. |
| `base_url` | `str` | Yes | API base URL for the provider |
| `api_key` | `Optional[str]` | No | API key (optional — some providers like Ollama don't need one) |
| `default_model` | `Optional[str]` | No | Default model name if not specified in agent YAML |

---

## 6. tools/run_subagent.py — How It Calls spawn_subagent

**File:** `/workspaces/harness/tools/run_subagent.py` (lines 130-152)

```python
def run_subagent(sub_agent: str, task: str) -> ToolResult:
    from agent.context import CURRENT_AGENT as _CURRENT_AGENT
    
    # Save the parent's CURRENT_AGENT so we can restore it after spawning.
    saved_agent = _CURRENT_AGENT.get()  # Line 133

    try:
        from agent import Agent, RESPONSE, TOOL_CALL
        
        termination_prompt = TERMINATION_PROMPT

        # No explicit parent needed — spawn_subagent falls back to the current
        # contextvar bound by handle_prompt(). (Lines 140-145)
        sub = Agent.spawn_subagent(
            sub_agent,
            extra_tools=[_get_submit_results_def()],  # inject submit_results at runtime
        )

        # Append termination protocol to sub-agent's existing system prompt.
        sub._agent_type.inject_extra_system_prompt(termination_prompt)  # Line 148

        result_text = ""
        for kind, *args in sub.handle_prompt(task):  # Line 151
            if kind == TOOL_CALL and args[0] == "submit_results":
                # Dispatch the submit_results call directly and capture its return value.
                func_name = args[0]
                args_data = json.loads(args[1])
                from tools.dispatcher import dispatch
                result = dispatch(func_name, args_data)
                return ToolResult(...)

            elif kind == RESPONSE:
                result_text = args[0]

        return ToolResult(
            llm_text=_strip_ansi(result_text if result_text.strip() else "(sub-agent produced no output)"),
            ...
        )

    except FileNotFoundError as exc:
        return make_error_result(f"Error: {exc}")
    except Exception as exc:
        return make_error_result(f"Error running sub-agent '{sub_agent}': {exc}")
    finally:
        # Always restore the parent's CURRENT_AGENT, even on early returns
        _CURRENT_AGENT.set(saved_agent)  # Line 196
```

**What run_subagent passes to spawn_subagent:**
- `sub_agent`: The YAML stem name (e.g., "analyst")
- `parent_agent`: **Not passed explicitly!** Falls back to `CURRENT_AGENT.get()` inside spawn_subagent
- `tool_schemas`: **Not passed** — defaults to all AGENT_TOOLS inside spawn_subagent
- `extra_tools`: `[<submit_results function_def>]` — injects submit_results at runtime

**Key observations:**
1. The tool call receives only 2 positional args: `(sub_agent, task)` from the LLM's perspective.
2. It does NOT pass explicit parent_agent or tool_schemas to spawn_subagent.
3. The CURRENT_AGENT contextvar is carefully saved/restored to prevent leakage between parent and sub-agent.

---

## 7. _build_subagent_provider Callers

**File:** `/workspaces/harness/agent/core.py` (lines 17, 395)

```python
# Definition: line 17
def _build_subagent_provider(agent_type, parent_agent):

# Caller: line 395 (inside Agent.spawn_subagent)
if hasattr(parent_agent, '_provider') and parent_agent._provider is not None:
    new_provider = parent_agent._provider
else:
    new_provider = _build_subagent_provider(agent_type, parent_agent)
```

**Only caller:** `Agent.spawn_subagent()` at line 395. No other code in the project calls this function directly.

---

## 8. Direct Provider Instantiation & Passing Patterns

### All places where Provider is created or passed:

| Location | Line(s) | Action |
|----------|---------|--------|
| `model/provider.py` | 11 | `Provider(ABC)` — Abstract base class definition |
| `model/provider.py` | 223-233 | `create_provider()` factory function (returns OpenAIProvider or OllamaProvider) |
| `model/provider.py` | 68-79 | `Provider.from_config(config)` — Creates Provider from ProviderConfig dataclass |
| **`harness.py`** | **80** | **`provider = Provider.from_config(agent_type.provider_config)`** — Harness creates Provider for main agent |
| `agent/core.py` | 26 | `return Provider.from_config(agent_type.provider_config)` — Inside `_build_subagent_provider` (first branch) |
| `agent/core.py` | 45 | `return Provider.from_config(MinimalProviderConfig())` — Inside `_build_subagent_provider` (fallback branch) |

### Where Providers are stored/passed:

| Location | Line(s) | Action |
|----------|---------|--------|
| `agent/core.py` | 72 | `self._provider = provider` — Stored in Agent.__init__ |
| `agent/core.py` | 392-395 | Reuse parent's `_provider` or build new one for sub-agent |
| `harness.py` | 103 | Passed as `provider=provider` to Agent() constructor |

---

## Summary: The Provider Creation Chain

```
┌─────────────────────────────────────────────────────────────┐
│                    harness.py (entry point)                 │
│                                                             │
│  62: resolve_config_path("agents/main.yaml")                │
│  70: AgentType.from_file(path)                              │
│      └──> Resolves provider_config from config.yaml         │
│          (via get_provider_config() or get_default_provider())│
│                                                             │
│  80: Provider.from_config(agent_type.provider_config)       │
│      └──> Creates OpenAIProvider/OllamaProvider             │
│                                                             │
│  96-99: context_length = provider.get_context_length(...)   │
│                                                             │
│ 101-106: Agent(                                             │
│            agent_type=agent_type,                           │
│            provider=provider,                               │
│            context_length=context_length,                   │
│            tool_schemas=AGENT_TOOLS                         │
│          )                                                  │
└─────────────────────────────────────────────────────────────┘

        ↓ Sub-agent spawning (via run_subagent tool) ↓

┌─────────────────────────────────────────────────────────────┐
│              agent/core.py — spawn_subagent()               │
│                                                             │
│ 379: AgentType.from_file(str(yaml_path_str))                │
│      └──> Resolves provider_config from YAML config.yaml    │
│                                                             │
│ 392-395: Provider resolution logic:                         │
│   if parent has _provider:                                  │
│       new_provider = parent._provider                       │
│   else:                                                     │
│       new_provider = _build_subagent_provider(              │
│           agent_type, parent_agent)                         │
│       └──> Uses agent_type.provider_config                  │
│          OR falls back to MinimalProviderConfig             │
│                                                             │
│ 403-409: return cls(                                        │
│            agent_type=agent_type,                           │
│            provider=new_provider,                           │
│            context_length=context_length,                   │
│            tool_schemas=tool_schemas,                       │
│            extra_tools=extra_tools                          │
│          )                                                  │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight for Simplification:** The `AgentType.from_file()` method always resolves a `provider_config` (ProviderConfig dataclass). Both harness.py and `_build_subagent_provider` immediately convert this to a Provider instance via `Provider.from_config()`. Since the Provider interface is essentially: openai client + provider_type dispatch, one could potentially:

1. Have Agent accept either a ProviderConfig or a Provider
2. Defer Provider construction until first use (lazy initialization)
3. Or have Agent.__init__ call `Provider.from_config(agent_type.provider_config)` internally if only a config is provided

This would let harness.py skip the explicit `from model.provider import Provider` and `provider = Provider.from_config(...)` steps, reducing boilerplate. However, this depends on whether there are legitimate cases where one wants to pass an already-instantiated Provider (e.g., for testing with mocks) vs always constructing from config.
