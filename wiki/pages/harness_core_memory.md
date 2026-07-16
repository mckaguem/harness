---
name: "harness_core.memory"
description: "Persistent project memory (MEMORY.md)."
source: "harness_core/memory.py"
---

Persistent project memory (MEMORY.md).

The harness can maintain a durable ``MEMORY.md`` file at the project root. Its
contents are auto-injected into every agent's system prompt (so they survive
context compression and session reloads), and the :mod:`harness_core.tools.update_memory`
tool lets an agent append to or rewrite it while working.

This is the agentic "external memory" pattern: a small, self-maintained notes
file that outlives any single conversation and is orthogonal to (and complementary
with) the session-compression pipeline.

## References
- [get_memory_path](harness_core_memory_get_memory_path) - Return the path to ``MEMORY
- [read_memory](harness_core_memory_read_memory) - Read the contents of ``MEMORY
- [memory_section](harness_core_memory_memory_section) - Build the system-prompt section for *memory*
- [MEMORY_FILENAME](harness_core_memory_MEMORY_FILENAME) - Constant
- [Module Index](../index/harness_core.md) - Parent module index
