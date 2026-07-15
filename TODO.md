# Harness.py things to work on

## Broken things

- tool call and result messages
- Usage scoll bar dragging

## Testing


## Session Saving

- [DONE] Group session files per app run into date-time folders under `.sessions/` (created at startup and on `/new` and `/load`), so the main agent and all subagents it spawns share one folder.
- [DONE] Fix subagent session filenames to include the agent type name (e.g. `..._analyst.yaml`) instead of always `..._main.yaml`.
- Idea: Add a `/sessions` command or list view to browse run folders.
- Idea: Auto-prune old run folders beyond N days / keep only the last M runs.
- Move .sessions/ folder to ./.harness_py/sessions

## Context efficiency

- Context compression (test the following)
    - auto compression not happening?
    - Print out when auto compression happens
    - Print out size of context before and after (% of max context)
    - Save to file in nicer format (use same mechanism as uncompressed)
    - Context usage stats seem to be using old numbers, not updated
    - Truncate listdir tool outputs

- Relevance realisation system

## Commands

- /goal: what is it and implement

## Skills

- clean up the code so much!
    - Skill class

## Tools

- Some way of preventing the main agent from getting the submit_result tool

## Subagents

- collapsed subagent session visible?

## Infra

- Async everything and multiple agents running concurrently

## UI

- code review and refactor
- sidebar on right
    - format usage stats better
- modle name in sidebar
- 
- turn time under agent response
- Streaming responses (including thinking)
- Collapsable thinking
- for long things in message window, have a separate panel with scrollbar (eg. file_read, thinking)

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)


## Refactor

