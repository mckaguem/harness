"""Handler for the /goal command.

Sets the active agent's goal text. The Agent's mixin wiring is responsible for
forwarding the goal to the model; this command only stores the text on the
agent and reports confirmation.
"""

from harness_core.terminal_io.display import print_system


def cmd_goal(rest: str, agent=None) -> bool | tuple[str, bool]:
    """Set the active agent's goal.

    Usage:
        /goal <your goal description>   - set the agent's current goal

    The command stores the goal text on ``agent.goal`` and prints a
    confirmation. To forward the goal text to the model, it returns a
    ``(text, False)`` tuple which the mixin wiring forwards as user input.

    Args:
        rest: The goal description text supplied after the command.
        agent: The current Agent instance.

    Returns:
        A ``(goal_text, False)`` tuple to forward the goal to the model, or
        ``False`` on error / no-op.
    """
    if agent is None:
        print_system("Error", "No active agent.")
        return False

    if not rest.strip():
        print_system("Goal", "Usage: /goal <your goal description>")
        return False

    goal_text = rest.strip()
    agent.goal = goal_text
    print_system(
        "🎯 Goal Set",
        f"Goal set: {goal_text}\n\nWork toward this goal. When complete, call the `goal_met` tool to clear it."
    )
    return (goal_text, False)
