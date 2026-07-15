"""
Context Compression Module
==========================
Implements context compression for the Agent Harness.

This module provides functionality to compress conversation history by:
- Compressing older messages while preserving recent ones
- Dispatching tool-result truncation to specialized helpers (by tool name)
- Skipping messages already truncated by a previous compression pass
- Managing session filepaths for compressed conversations
- Supporting incremental compression with date/time tracking
- Automatic compression when context utilization exceeds thresholds
"""

import os, re
from datetime import datetime, timezone

from .session import Session  # Ensure proper import if needed elsewhere
from harness_core.terminal_io import print_system

TRUNCATED_PREFIX = "[SYSTEM: this tool result is outdated and has been removed.]"

# Tools that produce large, tree-style outputs; always truncate the entire message.
LIST_DIR_TOOL_NAMES = {"list_dir"}

# File-operating tools whose results should be truncated if the file has been
# modified since the message was created.
FILE_OPERATING_TOOLS = {"read_file", "write_file", "edit_file"}


def _already_truncated(msg: dict) -> bool:
    """Return True iff ``msg["content"]`` is a string starting with :data:`TRUNCATED_PREFIX`.

    Used to skip messages that were already truncated by an earlier compression pass.
    """
    content = msg.get("content")
    return isinstance(content, str) and content.startswith(TRUNCATED_PREFIX)


def compress_list_dir(msg: dict) -> dict:
    """Truncate the entire content of a ``list_dir`` tool-result message."""
    new_msg = dict(msg)
    new_msg["content"] = TRUNCATED_PREFIX
    return new_msg


def _extract_read_file_path(content: str | None) -> str | None:
    """Best-effort extraction of a file path from a read_file result's content.

    The read_file output wraps the body in ``<file path="...">...</file>``; this
    function parses that attribute out via regex and returns the path, or None
    if it cannot be found.
    """
    if not isinstance(content, str):
        return None
    match = re.search(r'<file\s+path="([^"]+)"', content)
    if match:
        return match.group(1)
    return None


def _parse_tool_arguments(arguments):
    """Return the arguments dict from ``function.arguments`` regardless of form.

    The LLM may pass arguments either as:
      - a parsed Python dict, or
      - a JSON-encoded string (which must be deserialized).

    Returns None if *arguments* is not usable.
    """
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str) and arguments.strip():
        import json as _json
        try:
            parsed = _json.loads(arguments)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, TypeError):
            pass
    return None


def _update_filename_mapping(tool_calls, file_operating_tools: set[str], filename_by_tool_id: dict[str, str]) -> None:
    """Populate *filename_by_tool_id* from a list of tool_call entries.
    
    For each entry whose function is in ``file_operating_tools``, extract the
    ``filename`` argument (preferring the ``filename`` key; falling back to
    positional argument 0) and record it keyed by the call id.
    """
    for tc in tool_calls:
        fn_def = tc.get("function", {}) or {}
        
        # Resolve function name — may be stored as dict or JSON-string.
        func_name = None
        raw_fn_name = fn_def.get("name") if isinstance(fn_def, dict) else None
        if isinstance(raw_fn_name, str):
            func_name = raw_fn_name.strip().lower()

        # Some providers put the call id in ``id``, others in ``name``.
        tool_call_id = tc.get("id") or tc.get("name") or ""
        if not tool_call_id:
            continue

        if func_name not in file_operating_tools:
            continue

        # Extract filename from arguments (dict or JSON-string).
        raw_args = fn_def.get("arguments", {})
        args_dict = _parse_tool_arguments(raw_args)
        filename = None
        if isinstance(args_dict, dict):
            filename = args_dict.get("filename")
            if not filename:
                positional = args_dict.get("args") or args_dict.get("positional") or []
                if isinstance(positional, list) and positional:
                    filename = positional[0]

        if isinstance(filename, str) and filename.strip():
            filename_by_tool_id[tool_call_id] = filename.strip()


def compress_file_operation(
    msg: dict, filename_by_tool_id: dict[str, str] | None = None
) -> dict:
    """Truncate a file-operating tool-result (read/write/edit) iff the underlying
    file has been modified since the message was created.

    Steps:
      1. Shallow-copy ``msg`` and attempt to locate the relevant filename.
      2. Parse the message timestamp (treating naive datetimes as UTC).
         On parse failure, treat the timestamp as "old" so truncation is
         conservative.
      3. If the file exists and its mtime exceeds the parsed timestamp, it has
         been modified since this result was produced → return a copy whose
         content is replaced with :data:`TRUNCATED_PREFIX`.
      4. Otherwise return ``new_msg`` unchanged (content left alone).

    If no filename can be located reliably (e.g. for write_file / edit_file
    results that don't carry the path in their output), the message is returned
    unchanged — it's safer not to truncate a fresh write/edit result based on
    stale or nonexistent filenames.
    """
    new_msg = dict(msg)
    content = msg.get("content")

    # --- locate filename -----------------------------------------------
    if isinstance(content, str):
        path_from_content = _extract_read_file_path(content)
        if path_from_content:
            filename = path_from_content
        else:
            # For write_file / edit_file the result is a short JSON/diff and
            # does not carry the target path; try looking up via the matching
            # assistant tool_call entry.
            tool_call_id = msg.get("tool_call_id") or ""
            if filename_by_tool_id and isinstance(tool_call_id, str):
                filename = filename_by_tool_id.get(tool_call_id)
            else:
                return new_msg
    else:
        # No usable content → cannot locate filename → leave content alone.
        return new_msg

    # --- parse timestamp -----------------------------------------------
    raw_ts = msg.get("timestamp", "") or ""
    try:
        dt = datetime.fromisoformat(raw_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        # Conservative: treat as "old" → truncate.
        new_msg["content"] = TRUNCATED_PREFIX
        return new_msg

    # --- stat and compare mtime ----------------------------------------
    try:
        st_mtime = os.stat(filename).st_mtime
    except (OSError, FileNotFoundError):
        # File does not exist on disk — content is stale → truncate.
        new_msg["content"] = TRUNCATED_PREFIX
        return new_msg

    if st_mtime > dt.timestamp():
        # File was modified after this result was produced → truncate.
        new_msg["content"] = TRUNCATED_PREFIX

    return new_msg


def _must_preserve(msg: dict) -> bool:
    """Return True for messages whose content MUST be preserved verbatim.

    System messages and tool_calls-carrying messages are preserved as-is so the
    agent's behaviour definition and strict tool-call sequencing remain intact.
    Tool-result messages are no longer in this list — they are dispatched to
    name-specific helpers (``compress_list_dir``, ``compress_file_operation``)
    or left alone for unknown tools.
    """
    if msg.get("role") == "system":
        return True
    if msg.get("tool_calls"):
        return True
    return False


def compress_messages(messages: list[dict], fraction: float) -> list[dict]:
    """Compress older messages in the list, preserving a portion at the end.

    Args:
        messages: List of message dictionaries to compress.
        fraction: The proportion (0-1) of messages at the END that should be
                  left intact and unmodified. For example, with 100 messages
                  and fraction=0.1, the last 10 messages are preserved as-is,
                  while the first 90 are compressed by dispatching to
                  specialized helpers or halving long content.

    Returns:
        A new list where older messages have been truncated (compressed) but
        recent messages remain unchanged. The order is preserved - compressed
        messages come first, followed by preserved messages.

    Raises:
        ValueError: If fraction is not between 0 and 1 inclusive.
    """
    if not isinstance(fraction, (int, float)) or fraction < 0 or fraction > 1:
        raise ValueError(
            f"fraction must be a number between 0 and 1, got {fraction!r}"
        )

    # Calculate where the preserved portion begins
    tail_start_index = int(len(messages) * fraction)

    if tail_start_index == 0:
        # fraction=0: compress everything (no preservation)
        prefix_to_compress = messages[:]
        preserved_suffix = []
    elif tail_start_index >= len(messages):
        # fraction>=1.0 or larger than list: preserve everything
        return list(messages)
    else:
        # Normal case: compress first N-tail messages, preserve last tail messages
        prefix_to_compress = messages[:len(messages) - tail_start_index]
        preserved_suffix = messages[len(messages) - tail_start_index:]

    if not prefix_to_compress:
        return list(messages)

    # Incrementally build a mapping from tool_call_id → filename for file-operating tools.
    # Since tool calls always precede their results in conversation order, we can populate
    # this dict as we iterate through messages and use it when processing tool-result messages.
    filename_by_tool_id = {}

    compressed_prefix = []
    for msg in prefix_to_compress:
        # Skip messages already truncated by a prior compression pass.
        if _already_truncated(msg):
            compressed_prefix.append(dict(msg))
            continue

        # Messages whose content MUST be preserved verbatim (system prompt, tool_calls).
        if _must_preserve(msg):
            # Extract filename from assistant tool_calls for file-operating tools so that
            # subsequent tool-result messages can look it up. This avoids needing to parse
            # the result's output for write/edit results that don't carry a path.
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                _update_filename_mapping(msg["tool_calls"], FILE_OPERATING_TOOLS, filename_by_tool_id)

            compressed_prefix.append(dict(msg))
            continue

        new_msg = dict(msg)  # shallow copy to preserve role and other keys
        content = new_msg.get("content")

        # Tool-result messages: dispatch by name.
        if msg.get("role") == "tool":
            tool_name = msg.get("name", "")
            if tool_name in LIST_DIR_TOOL_NAMES:
                new_msg = compress_list_dir(new_msg)
            elif tool_name in FILE_OPERATING_TOOLS:
                new_msg = compress_file_operation(
                    new_msg, filename_by_tool_id=filename_by_tool_id
                )
            # Unknown tool names → leave content alone (conservative).
            compressed_prefix.append(new_msg)
            continue

        # Leave other messages alone to avoid confusing the agent
        compressed_prefix.append(new_msg)

    return compressed_prefix + preserved_suffix


def should_auto_compress(context_utilization: float, threshold: float = 0.5) -> bool:
    """Determine if auto-compression should be triggered based on context utilization.

    Args:
        context_utilization: The current fraction of context used (0-1).
        threshold: The upper limit above which compression should trigger.
                  Defaults to 0.5 (50%).

    Returns:
        True if the context utilization exceeds the threshold, False otherwise.

    Raises:
        ValueError: If context_utilization is not between 0 and 1 inclusive.
    """
    if not (0 <= context_utilization <= 1):
        raise ValueError(
            f"context_utilization must be between 0 and 1, got {context_utilization}"
        )

    return context_utilization > threshold


def build_compressed_filepath(filepath: str) -> tuple[str, bool]:
    """Build a new filepath for a compressed session file.

    Args:
        filepath: The original session filepath (e.g., '/tmp/session.json').

    Returns:
        A tuple containing:
            - New filepath with '-compressed-<timestamp>' inserted before the extension
            - Boolean indicating if the input was already a compressed filepath
    """
    COMPRESSED_PATTERN = r'-compressed-(\d{8}T\d{6}(?:Z|[+-]\d{2}:?\d{2}))\.'

    match = re.search(COMPRESSED_PATTERN, filepath)

    if match:
        # Already compressed - replace the timestamp with current time
        base_path = filepath[:match.start()]
        ext_start = match.end() - 1  # Position before '.' in '.json'
        ext = filepath[ext_start:]

        new_timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return f"{base_path}-compressed-{new_timestamp}{ext}", True

    else:
        # Not yet compressed - add the compression marker
        base, ext = filepath.rsplit('.', 1) if '.' in filepath else (filepath, 'json')
        new_timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return f"{base}-compressed-{new_timestamp}.{ext}", False


def compress_session(session: Session, fraction: float = 0.1) -> str | None:
    """Compress a session's messages and rotate its save file.

    Args:
        session: An object with .messages (list) and .filepath (str) attributes.
        fraction: The proportion of the tail to preserve (passed to compress_messages).

    Returns:
        The new filepath string, or None if compression made no changes.
    """
    # Validate that the session has a valid filepath set.
    if not getattr(session, "filepath", None):
        raise ValueError("Cannot compress a session with no filepath set")

    # Ensure the session has a messages attribute that is iterable.
    if not hasattr(session, "messages"):
        raise ValueError("Session object must have a 'messages' attribute")

    messages = getattr(session, "messages", None)
    if messages is None:
        print_system("Compress", "Session has no messages. Cannot compress.")
        return None

    # Always save before mutating
    session.save()

    # Compress messages (dispatches by tool name; truncates entire messages for
    # list_dir / file-operating tools, halves long user/assistant content).
    new_messages = compress_messages(session.messages, fraction)

    # If nothing changed, return None.  Truncation always shortens at least one
    # message's ``content`` string (full replacement with the prefix or a shorter
    # halved tail), so length comparison still detects changes correctly.
    had_changes = False
    for orig_msg, comp_msg in zip(session.messages, new_messages):
        orig_content = orig_msg.get("content") or ""
        comp_content = comp_msg.get("content") or ""
        if len(comp_content) < len(orig_content):
            had_changes = True
            break

    if not had_changes:
        return None

    # Update filepath with compression marker
    old_path = session.filepath
    assert old_path is not None
    new_filepath, _ = build_compressed_filepath(old_path)

    # Replace messages and save to new location
    session.messages[:] = new_messages
    session._save_impl(new_filepath, save_state=True)

    return new_filepath


__all__ = [
    "compress_messages",
    "compress_list_dir",
    "compress_file_operation",
    "should_auto_compress",
    "build_compressed_filepath",
    "compress_session",
    "TRUNCATED_PREFIX",
]
