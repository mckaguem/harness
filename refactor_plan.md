# Refactoring Plan: Separate Message Management into Session Class

## Overview
This refactor addresses three goals:
1. Reduce `agent/core.py` size by moving message management into a dedicated `Session` class
2. Remove all Ollama-related code (no longer used)
3. Simplify `_inject_task_state` to operate on individual messages

---

## Current State Analysis

### agent/core.py Structure (~449 lines)
- **Init method** (~80 lines): Creates OpenAI client, resolves base URL, sets up tools, initializes `self.messages`, creates TaskList
- **Properties**: `ollama_host` (line 91), `client`, `context_length`
- **`_inject_task_state`** (~50 lines): Takes full message list, copies it, modifies last user message with task state
- **`_chat` method** (~60 lines): Sends messages to OpenAI, has Ollama fallback that raises NotImplementedError
- **`handle_prompt`** (~80 lines): Main processing loop — appends user message, calls `_inject_task_state`, sends to LLM, processes tool calls
- **`summarize` method** (~60 lines): Builds temporary message list for summarization
- **`spawn_subagent` classmethod** (~50 lines): Factory method

### Ollama References to Remove
1. **Line 47**: `os.environ.get("OLLAMA_HOST", "http://qut-l1953034068.qut.edu.au:11434")` — hardcoded fallback URL
2. **Line 91-93**: `ollama_host` property (deprecated accessor for `_base_url`)

---

## Step-by-Step Plan

### Step 1: Create agent/session.py with Session Class

**File**: `agent/session.py`

Create a new `Session` class that owns all message management:

```python
class Session:
    """Manages conversation history and context injection."""
    
    def __init__(self, system_prompt: str, task_list=None):
        self.messages = [{"role": "system", "content": system_prompt}]
        self._task_list = task_list
        self._injected_text: Optional[str] = None
    
    # -- message manipulation -----------------------------------------------
    
    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation."""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: dict) -> None:
        """Append an assistant/tool-call response to the conversation."""
        self.messages.append(content)
    
    def add_tool_result(self, func_name: str, llm_text: str) -> None:
        """Append a tool result message to the conversation."""
        self.messages.append({
            "role": "tool",
            "content": llm_text,
            "name": func_name,
        })
    
    def get_messages(self) -> list[dict]:
        """Return the full message list (for sending to LLM)."""
        return self.messages
    
    # -- injection API -------------------------------------------------------
    
    def inject_text(self, s: str) -> None:
        """Queue text to be prepended to the next user input."""
        self._injected_text = f"<<INJECTED>>\n{s}\n<<END_INJECTED>>"
    
    # -- context injection ---------------------------------------------------
    
    def prepare_message_for_injection(self, message: dict) -> dict:
        """Take a single message, inject task state if applicable, return modified copy.
        
        This is the simplified version of the old _inject_task_state.
        Called on individual messages BEFORE they're added to self.messages.
        
        Args:
            message: A single message dict (must be user role).
            
        Returns:
            Modified message dict with task state prepended, or original if no injection needed.
        """
        if not self._task_list or message.get("role") != "user":
            return message
        
        content = message["content"]
        task_state_md = self._task_list.to_markdown()
        
        wrapped_content = f"""
[SYSTEM STATE]
The current state of your task execution list is:
{task_state_md}

Execute the next logical step based on this state.

[USER NEW INSTRUCTION]
{content}
"""
        
        return {**message, "content": wrapped_content}
```

---

### Step 2: Refactor agent/core.py to Use Session

**Changes to `Agent.__init__`**:
- Create `self._session = Session(agent_type.system_prompt, self._task_list)`
- Remove direct `self.messages` initialization
- Remove `_injected_text` attribute (now in Session)
- Keep `_base_url`, `_client`, `_tools`, `_executor`, `_max_loops`

**Remove**:
- `ollama_host` property (line 91-93)
- Direct message management methods moved to Session
- The old `_inject_task_state` method entirely

**Update `handle_prompt`**:
```python
def handle_prompt(self, user_input):
    # Prepend injected text
    effective_input = user_input
    if self._session._injected_text is not None:
        effective_input = f"{self._session._injected_text}\n\n{user_input}"
        self._session._injected_text = None
    
    # Prepare message (inject task state) BEFORE adding to session
    user_message = {"role": "user", "content": effective_input}
    prepared_message = self._session.prepare_message_for_injection(user_message)
    
    # Add to session messages
    self._session.add_user_message(prepared_message["content"])  # or pass full dict
    
    while True:
        # Safety ceiling
        if loop_count >= self._max_loops:
            yield (ERROR, "...")
            break
        
        messages_to_send = self._session.get_messages()
        response = self._chat(messages_to_send)
        
        message = response["message"]
        self._session.add_assistant_message(message)
        
        if not message.get("tool_calls"):
            # ... handle completion
            content = message.get("content", "")
            yield (RESPONSE, content, response)
            break
        
        for tool_call in message["tool_calls"]:
            func_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])
            
            # Termination circuit breaker
            if func_name == "submit_results" and ...:
                block_info = self._executor.make_submit_results_block(True)
                if block_info:
                    self._session.add_user_message(block_info["content"])  # or add_tool_result equivalent
                    yield (TOOL_RESULT, ...)
                    loop_count += 1
                    continue
            
            # ... execute tool and add result
            return_result = self._executor.execute(func_name, args)
            self._session.add_tool_result(func_name, return_result.llm_text)
```

**Update `summarize`**:
- Use `self._session.get_messages()` instead of `self.messages`

**Update `spawn_subagent`**:
- Pass system prompt and task_list to new Session constructor

---

### Step 3: Remove Ollama Code

1. **Delete line 47 fallback**: Replace the complex base URL resolution with a simpler version that only uses OpenAI-compatible URLs:
   ```python
   raw_host = getattr(openai_client, "base_url", None) or os.environ.get("OPENAI_BASE_URL")
   self._base_url = str(raw_host).rstrip("/") if raw_host else ""
   ```

2. **Delete `ollama_host` property** (lines 91-93) — no longer needed since `_client` is the public accessor anyway

---

### Step 4: Update Imports and References

**Files to check for broken imports**:
- `agent/__init__.py` — verify nothing exports removed symbols
- `commands/tasks.py` — uses `CURRENT_AGENT.get()` (still valid, just access `.task_list`)
- `tools/` directory — verify no direct references to `ollama_host`

**Verify these still work after refactor**:
```python
from agent.core import Agent
agent = Agent(...)
agent.task_list  # still accessible via property
agent.client     # still accessible
agent.context_length  # still accessible
```

---

### Step 5: Verification Steps

1. **Syntax check**: Run `python -c "import agent.session; import agent.core"` to verify imports work
2. **Import test**: Verify all dependent files can still import Agent
3. **Run existing tests** (if any): Check for regressions
4. **Manual inspection**: Trace through `handle_prompt` flow to ensure message lifecycle is correct

---

## Code Organization After Refactor

### agent/core.py (~250 lines, down from 449)
- Agent class with: init, properties, handle_prompt, summarize, spawn_subagent, _chat
- No direct message management (delegated to Session)

### agent/session.py (~100 lines, new file)
- Session class with: message list, injection API, context preparation

### Benefits
1. **Separation of concerns**: Message lifecycle isolated from orchestration logic
2. **Extensibility**: Easy to add session save/load later (just persist `self.messages` + `_injected_text`)
3. **Testability**: Session can be unit-tested independently
4. **Simplified injection**: Single-message transform is easier to reason about than list manipulation

---

## Future Extensibility Notes

The Session class design supports future features:
- **Save/Load**: Add `session.save(path)` and `Session.load(path, task_list)` classmethod that serialize/deserialize messages + injected_text
- **Multiple sessions**: Agent could have multiple named sessions (e.g., "default", "debug")
- **Message history limits**: Add `_max_messages` to truncate old messages while preserving system prompt
