We want to create a way of executing large plans autonomously and then test it out.

Problems:
- Current harness.py is interactive only, making it difficult to test autonomously
- Context will fill up for long tasks and the agent will lose track of what's going on

The plan is to fix this by:
- Adapting harness.py to run non-interactively from a prompt give on the command line
- Adjust harness.py to be able to call harness.py for testing
- Test out a loop of self-improvement for harness.py

Step 0:
- Check out a new branch
- Create a file called "progress.md" documenting what's been done on the plan to date

Each of the following steps should be done in a separate subagent of type main.  Instruct it to:
- Do what is necessary to achieve the goals of the step
- Use task lists to stay on track and subagents (subagents can run other subagents) for complex sub-tasks
- create and run tests to ensure that everything is running well
- commit changes
- summarise the changes in progress.md

Step 1:
- Modify harness.py to run in non-interactive mode when supplied with an initial message via a '--message' flag.  Use getopts

For remaining steps, prompt the subagent to run harness.py in non-interatvive mode as part of its testing.

Step 2:
- General clean up.  Make several passes of removing dead code.  
- Where comments indicate workarounds for backwards compatability, update the callers and remove backwards compatability.

Step 2:
- Investigate the current context compression code (currently non-functional).  Update it to work, both in automatic mode and with the command

Step 3:
- Rearrange the project directory structure to conform to standard python project standards.
- The goal is to be able to use uv to install and run the program as a CLI tool.  Structure the directory accordingly.
- Make changes to the code and tests necessary to adapt to the new directory structure

Step 4:
- Adapt OpenAIProvider to use responses interface instead of completions.
- Ollama support is not a priority and can be removed

Step 5:
- The goal is to support subagents running in parallel
- Make calls to the provider async, along with downstream code where appropriate
- Make run_subagent non-blocking so that the main agent and subagent run concurrently.
- When the subagent returns, insert the response to the calling agent in the next round of messages

