---
name: "harness_core.agent.loop._count_approx_tokens"
description: "Approximate token count from a message list using character estimation."
source: "harness_core/agent/loop.py"
---

Approximate token count from a message list using character estimation.

Uses ~4 chars per token as a rough approximation. This is much faster than
calling the OpenAI tokenizer for every message loop iteration.

## Signature
```python
_count_approx_tokens(messages: list) -> int
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
