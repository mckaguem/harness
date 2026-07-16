---
name: "harness_core.agent.core.handle_prompt"
description: "Process a single user prompt to completion."
source: "harness_core/agent/core.py"
---

Process a single user prompt to completion.

Yields tuples of ``(kind, ...)`` where ``kind`` is one of
:data:`RESPONSE`, :data:`TOOL_CALL`, :data:`TOOL_RESULT` or
:data:`ERROR`.  The agent dispatches and executes each tool internally;
it never calls display functions itself.

Yields::

    (RESPONSE,         content, openai_response)
    (TOOL_CALL,        func_name, args_str, response_data)
    (TOOL_RESULT,      func_name, result, response_data)
    (ERROR,            description)

## Signature
```python
handle_prompt(self, user_input: str) -> Generator[tuple[str, Any, Any, Optional[dict[str, Any]]], None, None]
```

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [Class: Agent](harness_core_agent_core_Agent) - Parent class
