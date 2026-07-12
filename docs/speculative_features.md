# Speculative Features for the Harness Coding Agent

> Phase 3 research. Goal: enumerate 10 beneficial features a local, terminal-based
> coding agent could adopt, then pick the single best one that is straightforward
> to add to the current codebase.
>
> Research sources (2025–2026): Anthropic Claude Code docs/architecture write-ups,
> r/LocalLLaMA autonomy threads, agent-worktree / context-mode projects, and
> general agentic-coding best-practice articles.

## Research summary

Modern coding agents (Claude Code, Cursor, Qwen Code, etc.) converge on a small
set of capabilities that live *around* the core LLM loop:

- **Extensibility layers** — skills, subagents, hooks, and MCP are the four
  mechanisms that let users customise behaviour without touching core code.
- **Context management** — multi-layer compaction / compression pipelines keep
  long sessions within the token budget.
- **Isolation & parallelism** — git worktrees give each agent its own workspace so
  parallel agents don't clobber each other's files.
- **Safety/permissions** — declarative allow/deny lists for tools, plus
  PreToolUse/PostToolUse hooks for guardrails.
- **Memory** — persistent, append-only session storage and project memory files
  (`CLAUDE.md` / `AGENTS.md` style) that survive context resets.

The harness already has several of these: skills, subagents + background
execution, slash commands, session saving, and a manual + auto context
compression pipeline. The gaps below are the highest-leverage additions.

## The 10 candidate features

1. **`/sessions` browser command** — list, preview, and load previous run folders
   under `.sessions/` from inside the agent. (TODO.md already lists this.)
2. **Git worktree isolation for subagents** — spawn each background sub-agent in
   its own git worktree so parallel agents never overwrite each other's files,
   then merge on completion.
3. **Persistent project memory file** (`MEMORY.md`) — an agent-maintained notes
   file that is auto-injected into the system prompt, surviving compression and
   reloads (the agentic "external memory" pattern from the `researcher` role).
4. **PreToolUse / PostToolUse hooks** — user-supplied scripts that run before/after
   any tool call to enforce standards or guardrails.
5. **Tool permission allow/deny list** — a config-driven allowlist so e.g. the
   main agent can be denied `submit_results`, or `execute_bash` limited to safe
   commands (TODO.md: "prevent main agent from getting submit_results").
6. **`/goal` command (persistent objective)** — set a high-level goal the agent
   re-reads each turn so long-running autonomous runs stay on track (TODO.md).
7. **Auto-prune old session folders** — keep only the last N run folders / prune
   beyond M days (TODO.md).
8. **Streaming responses with collapsible thinking** — render the LLM token
   stream live, with a collapsible "thinking" region (TODO.md / UI section).
9. **Semantic search over past sessions** — embed and retrieve prior session
   snippets to answer "what did we decide about X?".
10. **Right-hand context sidebar** — live display of context usage %, tokens, and
    most-recent tool/second metrics (TODO.md UI section).

## Selection

**Chosen: Feature 3 — Persistent project memory file (`MEMORY.md`).**

Rationale:

- It is *the* most straightforward to add: the codebase already auto-augments the
  system prompt with the CWD listing + `AGENTS.md` (see `AGENTS.md` §3,
  `build_system_prompt`). Adding one more auto-injected file is a tiny,
  well-contained change.
- It directly addresses a weakness the harness already acknowledges: context
  compression (`/compress`, auto-compression at 50% utilisation) *destroys*
  conversational history. A durable `MEMORY.md` is the canonical remedy used by
  every mature agent (Claude Code's `CLAUDE.md`, the `researcher` agent's
  `research_notes.md` pattern) and is orthogonal to compression — it persists
  across compactions and reloads.
- It requires no new infra (no hooks engine, no worktree plumbing, no streaming
  TUI changes) and no new dependencies.
- It is easy to test: file presence check, prompt augmentation, and a write tool
  path can all be exercised offline in the existing pytest harness.

The remaining 9 features are documented above for future phases.
