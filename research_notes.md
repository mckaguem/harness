# Research Notes — LLM Context Compression in Multi-Agent Systems

## Session 1: Initial Harness Core Exploration (2026-05-17)

### Key Findings from Codebase Analysis

**harness_core Architecture:**
- `Session` class owns conversation state as list of message dicts with UTC timestamps
- `contextvars.ContextVar` provides thread-local CURRENT_AGENT binding for agent isolation
- Auto-save to `.sessions/` on every message mutation (was causing test file leak, now patched)
- Sub-agents get independent Agent + Session instances — no shared history

**Compression Module (`session/context_compression.py`):**
- Dispatch-by-tool-name with mtime-based staleness detection
- TRUNCATED_PREFIX = "[SYSTEM: this tool result is outdated and has been removed.]"
- list_dir results always truncated (large tree outputs)
- File operations only truncate if file mtime > message timestamp
- System messages & tool calls preserved verbatim
- Uses tiktoken for accurate token estimation

**Auto-compression Triggers:**
- Loop iteration: triggers at >80% utilization
- Manual /compress command: 50% threshold in should_auto_compress
- Compressed files saved with `-compressed-<timestamp>` suffix

**Sub-Agent Isolation Pattern (in `run_subagent._run_one()`):**
```python
saved_agent = _CURRENT_AGENT.get()  # Save parent binding
try:
    sub = Agent.spawn_subagent(sub_agent, extra_tools=[...])
    sub._agent_type.inject_extra_system_prompt(termination_prompt)
finally:
    _CURRENT_AGENT.set(saved_agent)  # Restore in finally block
```

**MEMORY.md Pattern:**
- Persistent file at project root auto-injected into every agent's system prompt
- Cross-session persistence (survives restarts)
- Simple mental model — just another file in the project

### Existing CONTEXT_COMPRESSION_REPORT.md (1357 lines)
A comprehensive report was already generated covering:
1. Current implementation analysis (sliding window + dispatch-by-tool-name)
2. External best practices research (importance-weighted, hierarchical summarization)
3. Performance considerations (token budget allocation, proactive vs reactive compression)
4. Implementation patterns (50% threshold monitoring, fallback behaviors, system prompt injection, thread-local state)
5. Actionable recommendations (immediate, medium-term, long-term)
6. Testing recommendations with code examples
7. Monitoring & observability metrics

## Session 2: External Research Augmentation — LLM Context Compression Best Practices

### Key Themes from Industry/Research Sources

#### A. Token Budget Allocation Strategy
- **Recommended split for a typical 128k window:**
  - System prompt: 5% (~6,400 tokens)
  - Recent conversation (last ~3 turns): 50% (~64,000 tokens)
  - Compressed history: 40% (~51,200 tokens)
  - Reserved for response: 5% (~6,400 tokens)
- Rationale: system prompt must be preserved verbatim; recent context has highest relevance; compressed history provides continuity without dominating

#### B. Sliding Window vs Importance-Weighted Retention
| Feature | Sliding Window | Importance-Weighted |
|---------|---------------|---------------------|
| Implementation complexity | Low | Medium-High |
| Latency overhead | ~50ms for 100 messages | ~200-500ms (scoring required) |
| Preserves important old info? | No | Yes |
| Best for | Short sessions (<20 turns) | Long-running (>50 turns), scattered critical context |

**Importance scoring heuristics from research:**
1. Recency decay: `score = exp(-λ * age_in_turns)` — recent messages weighted higher
2. Query matching: semantic similarity between message content and current user query
3. Self-informativeness: information gain from removing each token (LLMLingua approach)
4. Tool-call involvement: messages in execution chains scored higher

#### C. Hierarchical Summarization Techniques
- Group messages by conversation turns or topics, replace groups with summaries
- Two-pass approach: group_by_turns → llm_summarize older groups
- Achieves 5-10x compression with <5% performance drop (per LLMLingua research)
- Risk of "summary drift" over many iterations — needs periodic refresh

#### D. Multi-Agent Context Passing Patterns

**Pattern 1: Isolated Sessions** (Current harness_core default)
- Each sub-agent receives only a task description string — no access to parent's history
- Pros: Clean isolation, predictable budgets, thread-safe
- Cons: No shared understanding, verbose prompts needed

**Pattern 2: Shared Memory File (MEMORY.md)** (Current harness_core pattern)
- Persistent file at project root serves as shared state
- Cross-session persistence, simple mental model
- Missing: versioning, conflict resolution, unbounded growth without compression

**Pattern 3: Progressive Context Building** (Recommended Enhancement)
- Parent maintains running summary of sub-agent work — each new sub-agent receives context + previous summaries
- Balances isolation with continuity
- Requires careful summary management

**Pattern 4: Thread-Local State** (Current harness_core implementation)
- `contextvars.ContextVar` provides thread-local CURRENT_AGENT binding
- Zero overhead for reads, thread-safe by design
- Single-process only, requires careful save/restore logic

#### E. Compression Timing: Reactive vs Proactive
| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| Reactive (>80%) | Lower latency per turn | Risk of context wall if compression fails | Current default — acceptable but conservative |
| Proactive (70%) + reactive (90% hard limit) | Better resource management, predictable overhead | Adds periodic latency even when not needed | **Hybrid recommended** |

#### F. Auto-Compression Trigger Chain with Fallbacks
1. Primary: Standard compression with LLM-generated summaries (if available)
2. Secondary: Truncation-based compression (current implementation)
3. Tertiary: Hard-truncate to safety margin (prevents context wall errors)
4. Quaternary: Maintain full context and risk hitting limit (last resort)

#### G. System Prompt Injection Techniques Observed in Codebase
- ✅ Uses structural delimiters (`[SYSTEM STATE]`, `[USER NEW INSTRUCTION]`) for LLM clarity
- ✅ JSON format for machine-readability
- ✅ Injects BEFORE adding to messages — doesn't pollute history with injection boilerplate
- Enhancement opportunities: prioritized order, conditional injection (only if tasks are incomplete), compression-aware injection

#### H. Thread-Local State Management Best Practices
- `contextvars.ContextVar` is thread-safe by design — each worker thread gets its own copy
- Worker threads via `asyncio.to_thread()` ensure sub-agents run in isolated contexts
- Save/restore in try/finally block prevents "agent state leak" on early returns or exceptions

**Common pitfalls to avoid:**
- ❌ Forgetting the finally block — subsequent tool calls would see sub-agent's empty task list
- ❌ Using global variables instead of ContextVars — not thread-safe, causes cross-thread pollution
- ❌ Modifying CURRENT_AGENT without saving/restoring — corrupts parent state

#### I. Performance Considerations Summary
| Approach | Compression Time | Impact on Next Turn | Notes |
|----------|-----------------|---------------------|-------|
| Sliding Window (current) | ~50ms for 100 messages | None | Fastest option, no LLM calls needed |
| Importance-Weighted | ~200-500ms | Potentially better quality | Adds latency but improves retention |
| Hierarchical Summarization | ~1-3s per cycle | Better semantic fidelity | Highest upfront cost, best long-term ROI for deep sessions |

#### J. Cost Optimization Through Efficient Context Usage
**Already implemented in harness_core:**
1. Tool result compression (list_dir always truncated, file ops conditional on mtime)
2. Skip already-truncated messages to prevent double-processing
3. Preserve tool call structure, compress only results

**Additional optimization opportunities:**
4. Importance-weighted retention (~1 LLM call per compression cycle for quality gain)
5. Hierarchical summarization after 30+ turns (5-10x compression achievable)
6. Memory compaction for MEMORY.md — periodically merge/summarize old entries

#### K. Context Monitoring Pattern (50% threshold)
```python
def should_auto_compress(context_utilization: float, threshold: float = 0.5) -> bool:
    return context_utilization > threshold
```

**Enhanced adaptive monitoring:**
- Track utilization history over time
- If trend is rapidly increasing AND average >60%, lower threshold to compress sooner (e.g., 60% instead of 80%)
- Maintains predictable behavior for stable conversations
