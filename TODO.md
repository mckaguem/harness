# Harness.py things to work on

## Misc
- scripts for making docker image and running in a directory
- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)
- Git worktrees?

## Project:
- Coding standards
- Update AGENTS.md with pointer to coding standards

## Skills:
- Modify prompts to tell agents to invoke skills when they will be useful
- Auto inject 
- clean up the code so much!
    - Skill class

## Better error handling / reporting:
- Find all except blocks that silently catch error and continue.  Log them.
- Change logging level with command line switch.  Default to error.
- Review logging levels for all current logging statements
- Uniform standard for formatting logging statements.  Document in coding standards.

## TUI:
- copy/paste in places other than text input
- Refactor with custom widget classes for stuff.
- Collapsable thinking
- Put TUI on a separate thread for responsiveness (still blocks sometimes on agent turn)
- turn time under agent response
- Streaming responses (including thinking)
- for long things in message window, have a separate panel with scrollbar (eg. file_read, thinking)
- collapsed subagent session visible?

## Agents
- Injected prompts: keep them in the last message only, scrub them from the session so past status doesn't take up context and get confusing.
- Inject goal every N tool calls
- Non-interactive mode

## Sessions
- move .sessions/ into .harness_py
- Idea: Add a `/sessions` command or list view to browse run folders.
- Idea: Auto-prune old run folders beyond N days / keep only the last M runs.

## Tools
- Something about discovering tools in standard locations (.harness_py/tools) and adding them.  Refactor existing tools to work similarly (maybe?).

## Infrastructure
- Subagents running in parallel, async
- fallback providers, deal with errors
- Use Manager class to launch subagents.

## Testing
- Testing at module boundaries

## Context efficiency

- Context compression (test the following)
    - auto compression not happening?
    - Print out when auto compression happens
    - Print out size of context before and after (% of max context)
    - Save to file in nicer format (use same mechanism as uncompressed)
    - Context usage stats seem to be using old numbers, not updated

- Relevance realisation system
