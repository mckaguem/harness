"""Slash-command handlers (/exit, /quit, /sub)."""

from terminal_io.display import print_system


def _cmd_exit(_rest, agent=None) -> bool:
    """Handle the /exit and /quit commands. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


def cmd_sub(rest: str, agent=None) -> bool | None:
    """Spawn an interactive sub-agent conversation.

    Args:
        rest: The sub-agent name (e.g. ``"analyst"`` from ``/sub analyst``).
        agent: The calling parent agent. Used to inject the summary back into 
               its message history when the user exits the sub-agent.

    Returns:
        False to continue the parent loop after returning from the sub-agent,
        or True if an error occurs and we want to break (currently never).
    """
    # Import here to avoid circular imports at module load time.
    from commands.sub import cmd_sub as _cmd_sub
    return _cmd_sub(rest, agent)


def cmd_tasks(rest: str, agent=None) -> bool | None:
    """Handle the /tasks command."""
    from commands.tasks import cmd_tasks as _cmd_tasks
    return _cmd_tasks(rest, agent)


def cmd_save_session(rest: str, agent=None) -> bool | None:
    """Save the current session to a YAML file in .sessions/.

    Usage:
        /save                    - auto-generated filename with timestamp + agent type
        /save my_custom_name     - uses 'my_custom_name.yaml' as filename

    Args:
        rest: Optional custom filename (without extension).
        agent: The current Agent instance.

    Returns:
        False to continue the loop after saving.
    """
    if agent is None:
        print_system("Error", "No active session to save.")
        return False

    # Determine filename from optional user input
    custom_name = rest.strip() if rest and rest.strip() else None
    if custom_name:
        # If user provides a name with .yaml extension, strip it; otherwise append it.
        if not custom_name.endswith(".yaml"):
            custom_name += ".yaml"
        filename = custom_name
    else:
        filename = None  # auto-generate via timestamp + agent type

    session = agent._session
    success, message = session.export_session(
        filename=filename,
        agent_type_name=agent._agent_type.name,
    )

    if success:
        print_system("Session Saved", f"Saved to: {message}")
    else:
        print_system("Save Failed", message)

    return False


def cmd_load_session(rest: str, agent=None) -> bool | None:
    """Load a session from a YAML file in .sessions/.

    Usage:
        /load <filename>         - load a specific session file (with or without .yaml)
        /load                    - list available sessions and prompt for selection

    Args:
        rest: Optional filename to load directly.
        agent: The current Agent instance (will be replaced with loaded one).

    Returns:
        True to break the loop (since the agent will be reinitialized),
        or False if loading fails.
    """
    from terminal_io.prompt import prompt_user

    sessions_dir = None  # default .sessions/ in cwd

    try:
        from pathlib import Path
        from session.session_utils import ensure_sessions_dir, parse_session_yaml
        
        sessions_dir = ensure_sessions_dir()
    except Exception as exc:
        print_system("Load Failed", f"Could not access .sessions/ directory: {exc}")
        return False

    if not rest or not rest.strip():
        # No filename provided — list available sessions and prompt user.
        session_files = sorted(sessions_dir.glob("*.yaml")) + sorted(sessions_dir.glob("*.yml"))
        
        if not session_files:
            print_system("No Sessions", f"No session files found in {sessions_dir}")
            return False

        print_system("Available Sessions", f"Found {len(session_files)} session file(s):")
        for i, sf in enumerate(session_files, 1):
            print(f"  [{i}] {sf.name}")

        while True:
            choice = prompt_user(f"Enter session number (1-{len(session_files)}) or filename: ")
            try:
                idx = int(choice.strip())
                if 1 <= idx <= len(session_files):
                    rest = str(session_files[idx - 1].name)
                    break
                else:
                    print(f"Please enter a number between 1 and {len(session_files)}.")
            except ValueError:
                # Treat as filename input
                if not choice.strip().endswith((".yaml", ".yml")):
                    choice += ".yaml"
                rest = choice.strip()
                break

    # Determine full path from relative filename or absolute/relative path.
    filepath_str = rest.strip()
    filepath = Path(filepath_str)

    if not filepath.is_absolute():
        filepath = sessions_dir / filepath

    if not filepath.is_file():
        print_system("Load Failed", f"Session file not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            yaml_content = f.read()

        messages, error = parse_session_yaml(yaml_content)
        if error:
            print_system("Load Failed", error)
            return False

        # Extract agent type name from file content (look for "Agent Type:" comment line).
        loaded_agent_type = None
        for line in yaml_content.split("\n"):
            if line.startswith("# Agent Type:"):
                loaded_agent_type = line.replace("# Agent Type:", "").strip()
                break

        # Validate the loaded agent type matches current agent.
        if agent is not None and loaded_agent_type is not None:
            if loaded_agent_type != agent._agent_type.name:
                print_system(
                    "Warning",
                    f"Session was created for agent '{loaded_agent_type}' but current "
                    f"agent is '{agent._agent_type.name}'. Loading anyway."
                )

        # Determine system prompt from loaded messages.
        if not messages:
            print_system("Load Failed", "Session file contains no messages.")
            return False

        system_prompt = messages[0].get("content", "")
        conversation_messages = messages[1:]

    except FileNotFoundError:
        print_system("Load Failed", f"Session file not found: {filepath}")
        return False
    except Exception as exc:
        print_system("Load Failed", f"Error reading session file: {exc}")
        return False

    # Re-initialize the agent with the loaded system prompt.
    if agent is None:
        print_system("Load Failed", "No active agent to load session into.")
        return False

    # Replace the agent's session and system prompt.
    from session.session import Session
    new_session = Session(system_prompt=system_prompt, task_list=agent._task_list)

    # Replay conversation messages.
    for msg in conversation_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            new_session.add_user_message(content)
        elif role == "assistant":
            new_session.add_assistant_message(msg)
        elif role == "tool":
            func_name = msg.get("name", "unknown_tool")
            new_session.add_tool_result(func_name, content)

    agent._session = new_session

    print_system("Session Loaded", f"Loaded from: {filepath}")
    return False


def cmd_new(rest: str, agent=None) -> bool | None:
    """Create a new session in the current agent.

    Resets both the task list and conversation history, keeping only the system prompt.
    A new session file is generated with a fresh timestamped filename.

    Usage:
        /new                 - create a brand-new session (resets everything)

    Args:
        rest: Unused (kept for consistency with other command handlers).
        agent: The current Agent instance.

    Returns:
        False to continue the loop after resetting.
    """
    if agent is None:
        print_system("Error", "No active session to reset.")
        return False

    # 1. Reset the task list (clear all tasks)
    if agent._task_list is not None:
        agent._task_list.reset()
    
    # 2. Create a brand new Session with only the system prompt and fresh session file.
    from session.session import Session
    new_session = Session(
        system_prompt=agent._agent_type.system_prompt,
        task_list=agent._task_list,
        auto_save=True,
    )
    # Preserve the current agent type name for filename consistency.
    new_session._agent_type_name = agent._agent_type.name
    
    # 3. Replace the agent's session.
    agent._session = new_session
    
    print_system(
        "New Session Created",
        f"Starting fresh — conversation history cleared, task list reset."
    )
    return False


COMMANDS = {
    'exit': _cmd_exit,
    'quit': _cmd_exit,  # Same function, different name in dict
    'sub': cmd_sub,
    'tasks': cmd_tasks,
    'save': cmd_save_session,
    'load': cmd_load_session,
    'new': cmd_new,
}


def compress_handler(rest: str, agent=None):
    """Handle the /compress command to trigger manual session compression.
    
    Args:
        rest: Optional string arguments (e.g., fraction value like '/compress 0.2')
        agent: The Agent instance containing a session
        
    Returns:
        False to continue the loop, True if exit is needed
    """
    from session.context_compression import compress_session
    
    # Get session from agent - try common attribute names
    if agent is None:
        print("❌ No agent provided. Cannot compress.")
        return False
    
    session = getattr(agent, 'session', None)
    
    if session is None:
        print("❌ No active session found. Cannot compress.")
        return False
    
    # Parse fraction from arguments (e.g., '/compress 0.2')
    fraction = 0.1  # default
    try:
        if rest and rest.strip():
            fraction = float(rest.strip())
            if not (0 < fraction <= 1):
                print(f"❌ Invalid fraction: {fraction}. Must be between 0 and 1.")
                return False
    except ValueError:
        print(f"❌ Invalid argument: '{rest}'. Please provide a number between 0 and 1.")
        return False
    
    # Validate session has required attributes
    if not hasattr(session, 'messages') or not hasattr(session, 'filepath'):
        print("❌ Session missing required attributes (messages/filepath). Cannot compress.")
        return False
    
    try:
        result = compress_session(session, fraction=fraction)
        
        if result is None:
            print(f"✅ Compression complete. No messages were modified (all already short enough).")
        else:
            print(f"✅ Session compressed successfully.")
            print(f"   Original file: {session.filepath}")
            print(f"   New file: {result}")
            print(f"   Preserved tail fraction: {fraction*100:.0f}%")
        
    except Exception as e:
        print(f"❌ Compression failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False


# ============================================================================
# Additional built-in slash commands (added by context compression feature)
# ============================================================================

def compress_handler(rest, agent=None):
    """Handle the /compress command — trigger manual session compression."""
    from session.context_compression import compress_session
    
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
    except ValueError:
        print(f"❌ Invalid fraction '{rest}'. Use a number between 0 and 1.")
        return False
    
    # Log before/after stats for the user
    original_count = len(session.messages)
    try:
        compress_session(session, fraction=fraction)
        new_count = len(session.messages)
        print(f"✅ Session compressed successfully.")
        print(f"   Original messages: {original_count}")
        print(f"   Compressed messages: {new_count}")
        print(f"   Filepath: {session.filepath}")
    except Exception as e:
        print(f"❌ Compression failed: {e}")
    
    return False

# Register the compress command
COMMANDS['compress'] = compress_handler
