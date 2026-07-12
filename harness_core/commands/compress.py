"""Handler for the /compress command."""

from harness_core.session.context_compression import compress_session
from harness_core.terminal_io import print_system, display_error


def compress_handler(rest: str, agent=None):
    """Handle the /compress command — trigger manual session compression.
    
    Args:
        rest: Optional fraction parameter as string (e.g., "0.2")
        agent: The Agent instance containing a session
        
    Returns:
        False to continue the loop
    """
    if agent is None:
        display_error("No agent provided. Cannot compress.")
        return False
    
    # Access the session through the agent's public property.
    session = agent.session
    
    if session is None:
        print_system("Compress", "No active session found. Cannot compress.")
        return False
    
    # Parse optional fraction from command argument (e.g., /compress 0.2)
    try:
        fraction = float(rest) if rest else 0.1
        if not (0 < fraction <= 1):
            display_error(f"Invalid fraction '{fraction}'. Must be between 0 and 1.")
            return False
    except ValueError:
        display_error(f"Invalid argument: '{rest}'. Please provide a number between 0 and 1.")
        return False
    
    # Log before/after stats for the user
    original_count = len(session.messages)
    try:
        result = compress_session(session, fraction=fraction)
        
        if result is None:
            print_system("Compress", "Compression complete. No messages were modified (all already short enough).")
        else:
            new_count = len(session.messages)
            print_system("Compress", "Session compressed successfully.")
            print_system("Compress", f"Original messages: {original_count}\nCompressed messages: {new_count}\nNew file: {result}\nPreserved tail fraction: {fraction*100:.0f}%")
        
    except Exception as e:
        display_error(f"Compression failed: {e}")
    
    return False