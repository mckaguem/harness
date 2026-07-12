# The plan

To begin, create a git branch to work in.

Execute the following phases of the plan.
- Use separate subagents for each phase.  Hint: you can use the `main` subagent type to act as a sub-orchestrator for really complex tasks.
- After each phase, run tests, fix bugs, and commit changes
- Keep track of progress and changes made in a markdown file for the user to review later.  
- Use tasks lists to keep yourself on track
- Keep working without stopping until you are done.  The user won't be able to respond.

## Phase 1 - Fix existing tests 

- Check current tests.  
- If any are not passing, check whether the tests need to be updated or if there is a genuine bug.
- Fix the tests or codes as required.

## Phase 2 - Improve test coverage

- Take advantage of the non-interactive mode to create end-to-end tests for all main funcionalities:
    - all tools
    - skill mechanisms
    - subagents

- Run in non-interactive mode in the cwd to make use of the existing configuration.

This may require extending the timeout on the execute_bash tool to allow for enough time for the program to respond.  Keep this time out less than 2 minutes, and use easy tasks that won't take very much time.

## Phase 2 - Parallel subagents

- Modify `run_subagent` so that it returns immediately with a subagent identifier
- Have subagent run in parallel (using async, or threads)
- Agent calls a new tool called `await` which blocks until any running subagent completes, or when an optional subagent identifier is given, until that specific subagent completes.  Then the response is returned as the result of the `await` tool call.
- Implement a maximum number of concurrent subagents.  When this limit is reached, further calls to `run_subagent` return an error, indicating that the Agent must `await` now as the maximum number of concurrent subagents has been reached.
- Write tests for this behaviour by running in the non-interactive mode.  Check that agents actually run in parallel.

## Phase 3 - Speculative features

- Create a list of 10 features that would be beneficial for this coding agent.  Use the `researcher` subagent to find ideas online.  Document these in a markdown file.
- Choose the best, most beneficial feature that can be added to the current project in a straightforward manner.
- Implement the feature, with testing etc.


