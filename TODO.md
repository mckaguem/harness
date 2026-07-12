# Harness.py things to work on

## Testing

- fix: testing creates multiple session files that need to be deleted after testing

## Session Saving

- [DONE] Group session files per app run into date-time folders under `.sessions/` (created at startup and on `/new` and `/load`), so the main agent and all subagents it spawns share one folder.
- [DONE] Fix subagent session filenames to include the agent type name (e.g. `..._analyst.yaml`) instead of always `..._main.yaml`.
- Idea: Add a `/sessions` command or list view to browse run folders.
- Idea: Auto-prune old run folders beyond N days / keep only the last M runs.

## Context efficiency

- Context compression
    - auto compression not happening?
    - Print out when auto compression happens
    - Print out size of context before and after (% of max context)
- Relevance realisation system

## Commands

- /goal: what is it and implement

## Skills

- remove error about missing skills directory every time a skill is used
- clean up the code so much!
    - Skill class

## Tools

- Some way of preventing the main agent from getting the submit_result tool

## Subagents

- collapsed subagent session visible?

## Infra

- Async everything and multiple agents running concurrently

## UI

- sidebar on right
    - format usage stats better
- turn time under agent response
- textual sluggishness
- Streaming responses (including thinking)
- Collapsable thinking

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)


## Refactor

