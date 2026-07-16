---
name: "harness_core.tools.submit_results"
description: "submit_results — sub-agent termination signal."
source: "harness_core/tools/submit_results.py"
---

submit_results — sub-agent termination signal.

When a sub-agent has finished executing its assigned task, it must invoke this
tool exactly once to return structured findings back to the calling (parent)
agent.  This is the *final* action of the sub-agent's lifecycle — no further
text response should be issued after invoking it.

The ``json_payload`` argument is a JSON object with three required fields:

- ``summary_of_actions`` — concise high-level summary of what was accomplished.
- ``actionable_data``  — exhaustive technical data (file paths, line numbers,
                         verbatim code snippets or error logs).
- ``unresolved_issues`` — detailed explanation of any errors encountered or
                          data that could not be found; ``null`` if everything
                          succeeded.

The function itself just parses the payload and echoes a confirmation string so
the parent agent can see it in its tool-result display before reading the JSON.

## References
- [submit_results](harness_core_tools_submit_results_submit_results) - Signal task completion and return structured findings to the parent agent
- [summary](harness_core_tools_submit_results_summary) - Return a one-line summary of the submit_results call
- [Module Index](../index/harness_core_tools.md) - Parent module index
