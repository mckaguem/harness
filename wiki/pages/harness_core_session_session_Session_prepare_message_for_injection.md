---
name: "harness_core.session.session.prepare_message_for_injection"
description: "Take a single user message, inject task state if applicable, return modified copy."
source: "harness_core/session/session.py"
---

Take a single user message, inject task state if applicable, return modified copy.

This is the simplified version of the old _inject_task_state. It operates on
one message at a time BEFORE it gets added to self.messages.

If there is no task_list or the message is not a user-role message, returns
the original unchanged. Otherwise wraps the content with structural delimiters
so the LLM can distinguish injected state from new instructions.

The injected payload uses JSON format with explicit IDs for machine-readability:
    {
      "tasks": [
        {"id": 1, "description": "...", "status": "pending"},
        ...
      ]
    }
This is more reliable than markdown checkboxes because the LLM can parse JSON
deterministically and agents are less likely to reference a non-existent task ID.

Args:
    message: A single message dict (should have role='user').

Returns:
    Modified message dict with task state prepended to its content, or the
    original if no injection is needed.

## Signature
```python
prepare_message_for_injection(self, message: dict) -> dict
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
