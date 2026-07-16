---
name: "harness_core.memory.memory_section"
description: "Build the system-prompt section for *memory*."
source: "harness_core/memory.py"
---

Build the system-prompt section for *memory*.

Returns an empty string when *memory* is empty/``None`` so callers can append
it unconditionally without injecting a dangling header.

## Signature
```python
memory_section(memory: str | None) -> str
```

## References
- [Module: harness_core.memory](harness_core_memory) - Parent module
