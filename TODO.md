# Harness.py things to work on

## Context efficiency

- Context compression
- Relevance realisation system
- Some way of being able to view everything that goes to the LLM

## Skills

- a bunch of usefull skills.
- clean up the code so much!
    - Skill class

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

## Misc

- On start, ask to copy sample config to ~/.harness_py if not found (and if not in project directory)