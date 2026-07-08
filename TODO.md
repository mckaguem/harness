# Harness.py things to work on

## Context efficiency

- Context compression
    - Mark and truncate:
        - tool calls with errors
        - read call results if they have been invalidated by later edits
        - read call results if there is a complete read later
        - write call if contents invalidated by later edits
        - read or write call if file doesn't exist anymore (moved, deleted, etc.)
    - 
- Relevance realisation system

## Commands

- /new  - new session


## Skills

- a bunch of usefull skills.
- clean up the code so much!
    - Skill class

## Tools

- Some way of preventing the main agent from getting the submit_result tool
- Look for more tools to add:
    - read function definition
- read_file and grep should truncate after 200(?) lines.  Probably need read_file to have a parameter for line number to read from

## Subagents 

## Infra

- Separate agent specification from model specification.  Use a model profile type thing in between.
- Async everything and multiple agents running concurrently

## UI

- Change theme for some things back to info (were changed to status)
- Streaming responses (including thinking)
- Textual TUI
- Remove the extra line printed by read_file tool.
- Change the tool result title to be like Result: Read File or something.  Probably don't need to say what the tool name is because it is in the box immediately above.
- Context usage after tool calls.

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)
- Inject task list every so often while in the tool-use loop

## Refactor

- summarize() into session
- 