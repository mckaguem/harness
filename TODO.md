# Harness.py things to work on

## Context efficiency

- Context compression
- Relevance realisation system
- Some way of being able to view everything that goes to the LLM

## Skills

- a bunch of usefull skills.
- clean up the code so much!
    - Skill class

## Tools

- Look for more tools to add:
    - web search
    - web page
    - read function definition
- read_file and grep should truncate after 200(?) lines.  Probably need read_file to have a parameter for line number to read from


## Subagents 

- Agent brief description in YAML file.
- Inject list of available agent types to orchestrator only
- Template stuff for system prompts for $CWD, $AGENTS, $SKILLS etc.

## Infra

- Separate agent specification from model specification.  Use a model profile type thing in between.
- Providers other than Ollama (OpenAI compatible)
- Async everything and multiple agents running concurrently

## UI

- Streaming responses (including thinking)
- Textual TUI
- Fix task list written on single line.
- Remove the extra line printed by read_file tool.
- Change the tool result title to be like Result: Read File or something.  Probably don't need to say what the tool name is because it is in the box immediately above.

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)