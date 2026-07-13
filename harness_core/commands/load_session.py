"""Handler for the /load command."""

from harness_core.terminal_io.display import print_system
from harness_core.terminal_io.prompt import prompt_user
from pathlib import Path
from harness_core.session.session_utils import ensure_sessions_dir, parse_session_yaml
from harness_core.session.session import Session


def cmd_load_session(rest: str, agent=None) -> bool | None:
    """Load a session from a YAML file in .sessions/.

    Usage:
        /load <filename>         - load a specific session file (with or without .yaml)
        /load                    - list available sessions and prompt for selection

    Args:
        rest: Optional filename to load directly.
        agent: The current Agent instance (will be replaced with loaded one).

    Returns:
        False to continue the loop (session is loaded into current agent).
    """
    sessions_dir = None  # default .sessions/ in cwd

    try:
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

        system_prompt = messages[0].get("content") or ""
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

    # Replace the agent's session and system prompt. Preserve the loaded agent
    # type so the re-saved file keeps the correct name, and start a fresh run
    # folder so the loaded conversation is grouped on disk.
    from harness_core.session.session_utils import create_run_folder
    create_run_folder()
    new_session = Session(
        system_prompt=system_prompt,
        task_list=agent._task_list,
        agent_type_name=loaded_agent_type or "main",
    )

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
            tool_call_id = msg.get("tool_call_id", f"call_{func_name}")
            new_session.add_tool_result(func_name, content, tool_call_id)

    agent._session = new_session

    print_system("Session Loaded", f"Loaded from: {filepath}")
    return False