---
name: "harness_core.session.session.__init__"
description: "Initialize a Session."
source: "harness_core/session/session.py"
---

Initialize a Session.

Args:
    system_prompt: The system prompt that becomes messages[0].
    task_list: Optional TaskList instance for context injection.
    auto_save: If True, automatically saves to .sessions/ after every change.
    provider: Optional LLM Provider instance (needed for summarize()).
    model_name: Model name string (needed for summarize() calls).
    agent_type_name: The agent type name (e.g. 'analyst', 'coder') used
        in the auto-save filename. Captured at construction so the saved
        file always carries the correct agent type (even for subagents).

## Signature
```python
__init__(self, system_prompt: str, task_list, auto_save: bool, provider, model_name: str, agent_type_name: str)
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
