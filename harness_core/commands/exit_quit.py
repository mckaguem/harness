"""Handler for the /exit and /quit commands."""

import logging

from harness_core.event_types import AppControlPayload, PROCESS_CONTROL_QUIT
from harness_core.terminal_io.display import print_system


logger = logging.getLogger(__name__)


def cmd_exit(_rest, agent=None) -> bool:
    """Handle the /exit and /quit commands. Returns False to keep loop running - dialog appears first."""
    print_system("Goodbye!", "See you next time.")

    # Publish a quit request event (not confirm yet) so Manager can show confirmation dialog.
    if agent is not None:
        logger.debug("Publishing PROCESS_CONTROL_QUIT (action=quit_request)")
        try:
            agent.publish(
                PROCESS_CONTROL_QUIT,
                AppControlPayload(action="quit_request"),
            )
            logger.debug("PROCESS_CONTROL_QUIT publish succeeded")
        except Exception as e:
            logger.error("PROCESS_CONTROL_QUIT publish failed: %s: %s", type(e).__name__, e)
            raise  # Don't swallow!

    # Return False to keep the loop running — Manager will handle shutdown after user confirms.
    return False  # don't break; dialog path handles exit
