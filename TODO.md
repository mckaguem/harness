# Harness.py things to work on

## Testing

- fix broken tests
- update tests for high test coverage
- integration tests in headless mode
- some kind of mock terminal for testing tui

## Session Saving

- [DONE] Group session files per app run into date-time folders under `.sessions/` (created at startup and on `/new` and `/load`), so the main agent and all subagents it spawns share one folder.
- [DONE] Fix subagent session filenames to include the agent type name (e.g. `..._analyst.yaml`) instead of always `..._main.yaml`.
- Idea: Add a `/sessions` command or list view to browse run folders.
- Idea: Auto-prune old run folders beyond N days / keep only the last M runs.

## Context efficiency

- Context compression
    - Print out when auto compression happens
    - Print out size of context before and after (% of max context)
- Relevance realisation system

## Commands

- /goal: what is it and implement

## Skills

- clean up the code so much!
    - Skill class

## Tools

- Some way of preventing the main agent from getting the submit_result tool

## Subagents 

## Infra

- Async everything and multiple agents running concurrently

## UI

- sidebar on right
    - context usage, most recent t/s
- textual sluggishness
- Streaming responses (including thinking)
- Collapsable thinking

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)

## Refactor

