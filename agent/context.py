"""Context variable management for tracking the current agent."""
import contextvars

CURRENT_AGENT: contextvars.ContextVar = contextvars.ContextVar("current_agent", default=None)


def get_current_agent():
    """Return the current agent from the thread-local context, or None."""
    return CURRENT_AGENT.get()
