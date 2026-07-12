# Harness.py things to work on

## Testing

- fix broken tests
- update tests for high test coverage
- integration tests in headless mode
- some kind of mock terminal for testing tui

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

- fix session filenames so they indicate subagent and type
- limit orchestrator tools so that it doesn't do too much by itself?
- update orchestrator prompt so that it uses task lists and subagents more

## Infra

- Async everything and multiple agents running concurrently

## UI

- sidebar on right
    - context usage, most recent t/s
    - task list
    - subagent info
- textual sluggishness
- Streaming responses (including thinking)
- Collapsable thinking
- title for tool calls is one-line summary
- tool call display text along with the raw json
- For subagents, give 1-line tool call summaries, prefix with agent name.

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)

## Refactor

- global code review
