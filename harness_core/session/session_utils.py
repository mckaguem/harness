import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml

# Import project_root from harness_core.utils
from harness_core.utils import project_root


def format_session_yaml(messages: list[dict], agent_type_name: str = "main") -> str:
    """Format session messages as YAML with human-readable comment lines.

    Uses multiple YAML documents separated by ``---`` so each message is a clean,
    independent mapping.  Human-readable comment markers are placed on their own
    line between document separators — the YAML parser ignores them but humans
    see them clearly in the file.

    Args:
        messages: List of message dicts with role and content keys.
        agent_type_name: The name of the agent type (e.g., 'analyst', 'coder').

    Returns:
        A string containing the formatted YAML session data.
    """
    yaml_lines = []

    # Header comment block (all comments before first --- are ignored by parser).
    yaml_lines.append("# Session Export")
    yaml_lines.append(f"# Agent Type: {agent_type_name}")
    yaml_lines.append(f"# Generated: {datetime.now().isoformat()}")
    yaml_lines.append("")

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Insert human-readable separators before non-system messages.
        if role == "user":
            yaml_lines.append("########### USER MESSAGE ###########")

        # Start a new YAML document for each message.
        yaml_lines.append("---")
        yaml_lines.append(f"role: {role}")

        if role == "system":
            yaml_lines.append("content: |-" )
            for line in content.split("\n"):
                yaml_lines.append(f"    {line}")

        elif role == "user":
            yaml_lines.append("content: |-" )
            for line in content.split("\n"):
                yaml_lines.append(f"    {line}")

        elif role == "assistant":
            if msg.get("tool_calls"):
                yaml_lines.append("tool_calls:")
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    yaml_lines.append("  - function:")
                    yaml_lines.append(f"      name: {func.get('name', '')}")
                    args_val = func.get("arguments", "")
                    if isinstance(args_val, str):
                        yaml_lines.append("      arguments: |-" )
                        for a_line in args_val.split("\n"):
                            yaml_lines.append(f"        {a_line}")
                    else:
                        yaml_lines.append(f'      arguments: "{args_val}"')
            if content:
                yaml_lines.append("content: |-" )
                for line in content.split("\n"):
                    yaml_lines.append(f"    {line}")

        elif role == "tool":
            yaml_lines.append(f"name: {msg.get('name', '')}")
            yaml_lines.append("content: |-" )
            for line in content.split("\n"):
                yaml_lines.append(f"    {line}")

        # Place tool result separator at the BOTTOM of the block (after content).
        if role == "tool":
            yaml_lines.append("")
            yaml_lines.append("# -----------------------------")

        yaml_lines.append("")  # blank line between documents.

    return "\n".join(yaml_lines)


def parse_session_yaml(yaml_content: str) -> tuple[list[dict], Optional[str]]:
    """Parse YAML session data back into a list of message dicts.

    Expects the format produced by :func:`format_session_yaml`, which uses
    ``---`` document separators so each message is an independent YAML mapping.

    Returns:
        A tuple of ``(messages_list, error_string)``. If *error* is ``None``,
        parsing succeeded.
    """
    try:
        import yaml as _yaml

        documents = list(_yaml.safe_load_all(yaml_content))

        messages: list[dict] = []
        for doc in documents:
            if not isinstance(doc, dict):
                continue  # skip None (blank docs) and comments-only sections.

            role = doc.get("role")
            if not role:
                continue

            content = doc.get("content", "")

            if role == "system":
                messages.append({"role": "system", "content": content})

            elif role == "user":
                messages.append({"role": "user", "content": content})

            elif role == "assistant":
                msg_dict: dict = {"role": "assistant"}
                if doc.get("tool_calls"):
                    parsed_tool_calls = []
                    for tc in doc["tool_calls"]:
                        func = tc.get("function", {})
                        args_val = func.get("arguments", "")
                        if isinstance(args_val, str):
                            try:
                                args_val = _yaml.safe_load(args_val)
                            except Exception:
                                pass
                        parsed_tool_calls.append({
                            "id": f"call_{len(parsed_tool_calls)}",
                            "type": "function",
                            "function": {
                                "name": func.get("name", ""),
                                "arguments": str(args_val) if not isinstance(args_val, str) else args_val,
                            },
                        })
                    msg_dict["tool_calls"] = parsed_tool_calls
                if content:
                    msg_dict["content"] = content
                messages.append(msg_dict)

            elif role == "tool":
                messages.append({
                    "role": "tool",
                    "name": doc.get("name", ""),
                    "content": content,
                })

        return messages, None

    except Exception as exc:
        return [], f"Error parsing session YAML: {str(exc)}"


def create_session_filename(agent_type_name: str = "main", extension: str = ".yaml") -> str:
    """Create a unique filename for session export based on timestamp and agent type.

    Args:
        agent_type_name: The agent type name (e.g., 'analyst', 'coder').
        extension: File extension (default '.yaml').

    Returns:
        A filename string in the format YYYYMMDD_HHMMSS_μs_agenttype.ext
        Uses nanosecond precision to ensure uniqueness even for rapid successive saves.
    """
    import time
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    frac_seconds = f"{now.microsecond:06d}"
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in agent_type_name)
    return f"{timestamp}_{frac_seconds}_{safe_name}{extension}"


def ensure_sessions_dir(base_path: Optional[str] = None) -> Path:
    """Ensure the .sessions/ directory (or current run folder) exists.

    Args:
        base_path: Base path to create .sessions/ under.
            Defaults to project root (detected via project_root()).

    Returns:
        The Path object for the .sessions/ directory (or the current run folder
        when one is active).
    """
    if base_path is None:
        # Prefer the active run folder so a main agent and all of its subagents
        # are organised together.  Falls back to the flat .sessions/ root.
        run_folder = get_current_run_folder()
        if run_folder is not None:
            sessions_dir = run_folder
        else:
            root = project_root()
            sessions_dir = root / ".sessions"
    else:
        sessions_dir = Path(base_path) / ".sessions"

    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def create_run_folder() -> Path:
    """Create a new date-time stamped run folder under .sessions/.

    Returns:
        The Path to the newly created run folder.
    """
    root = project_root()
    sessions_root = root / ".sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    frac_seconds = f"{datetime.now().microsecond:06d}"
    folder_name = f"{timestamp}_{frac_seconds}"
    run_folder = sessions_root / folder_name
    run_folder.mkdir(parents=True, exist_ok=True)
    set_current_run_folder(run_folder)
    return run_folder


# Module-level holder for the currently active run folder.  ``None`` means
# "no active run" — callers fall back to the flat .sessions/ directory.
_CURRENT_RUN_FOLDER: Optional[Path] = None


def get_current_run_folder() -> Optional[Path]:
    """Return the currently active run folder, or ``None`` if none is set."""
    return _CURRENT_RUN_FOLDER


def set_current_run_folder(folder: Optional[Path]) -> None:
    """Set (or clear with ``None``) the currently active run folder."""
    global _CURRENT_RUN_FOLDER
    _CURRENT_RUN_FOLDER = folder
