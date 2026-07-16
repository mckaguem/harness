---
name: "harness_core.tools.subagent_manager.launch"
description: "Start *sub_agent*/*task* in the background and return an identifier."
source: "harness_core/tools/subagent_manager.py"
---

Start *sub_agent*/*task* in the background and return an identifier.

Raises:
    RuntimeError: if the number of active background jobs has already
        reached ``MAX_CONCURRENT``.

## Signature
```python
launch(self, sub_agent: str, task: str) -> str
```

## References
- [Module: harness_core.tools.subagent_manager](harness_core_tools_subagent_manager) - Parent module
- [Class: SubagentManager](harness_core_tools_subagent_manager_SubagentManager) - Parent class
