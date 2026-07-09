"""Handler for the /compress command."""

from session.context_compression import compress_session


def compress_handler(rest: str, agent=None):
    """Handle the /compress command — trigger manual session compression.
    
    Args:
        rest: Optional fraction parameter as string (e.g., "0.2")
        agent: The Agent instance containing a session
        
    Returns:
        False to continue the loop
    """
    if agent is None:
        print("❌ No agent provided. Cannot compress.")
        return False
    
    # Access the session through the agent's internal state
    session = getattr(agent, '_session', None) or getattr(agent, 'session', None)
    
    if session is None:
        print("⚠️  No active session found. Cannot compress.")
        return False
    
    # Parse optional fraction from command argument (e.g., /compress 0.2)
    try:
        fraction = float(rest) if rest else 0.1
        if not (0 < fraction <= 1):
            print(f"❌ Invalid fraction '{fraction}'. Must be between 0 and 1.")
            return False
    except ValueError:
        print(f"❌ Invalid argument: '{rest}'. Please provide a number between 0 and 1.")
        return False
    
    # Log before/after stats for the user
    original_count = len(session.messages)
    try:
        result = compress_session(session, fraction=fraction)
        
        if result is None:
            print(f"✅ Compression complete. No messages were modified (all already short enough).")
        else:
            new_count = len(session.messages)
            print(f"✅ Session compressed successfully.")
            print(f"   Original messages: {original_count}")
            print(f"   Compressed messages: {new_count}")
            print(f"   New file: {result}")
            print(f"   Preserved tail fraction: {fraction*100:.0f}%")
        
    except Exception as e:
        print(f"❌ Compression failed: {e}")
    
    return False