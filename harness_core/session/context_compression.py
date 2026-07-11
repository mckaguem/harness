"""
Context Compression Module
==========================
Implements context compression for the Agent Harness.

This module provides functionality to compress conversation history by:
- Compressing older messages while preserving recent ones
- Managing session filepaths for compressed conversations
- Supporting incremental compression with date/time tracking
- Automatic compression when context utilization exceeds thresholds
"""

from .session import Session  # Ensure proper import if needed elsewhere

def compress_messages(messages: list[dict], fraction: float) -> list[dict]:
    """Compress older messages in the list, preserving a portion at the end.

    Args:
        messages: List of message dictionaries to compress.
        fraction: The proportion (0-1) of messages at the END that should be 
                  left intact and unmodified. For example, with 100 messages 
                  and fraction=0.1, the last 10 messages are preserved as-is,
                  while the first 90 are compressed by halving their content length.

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

    # Messages whose content MUST be preserved verbatim. Truncating these
    # would corrupt the conversation: the `system` prompt defines agent
    # behaviour, while `tool` results and messages carrying `tool_calls`
    # participate in strict tool-call sequencing required by the LLM APIs.
    def _must_preserve(msg: dict) -> bool:
        if msg.get("role") == "system":
            return True
        if msg.get("role") == "tool":
            return True
        if msg.get("tool_calls"):
            return True
        return False

    # Compress the prefix by truncating long content (but never the
    # system/tool/tool_calls messages, which are preserved verbatim).
    compressed_prefix = []
    for msg in prefix_to_compress:
        if _must_preserve(msg):
            compressed_prefix.append(dict(msg))
            continue

        new_msg = dict(msg)  # shallow copy to preserve role
        content = new_msg.get("content")

        if isinstance(content, str) and len(content) > 100:
            # Halve the content but keep a truncation marker
            max_chars = int(len(content) * 0.5)
            new_msg["content"] = (
                content[:max_chars]
                + "\n...[truncated for context compression, original omitted to save space]"
            )

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
    import re
    COMPRESSED_PATTERN = r'-compressed-(\d{8}T\d{6}(?:Z|[+-]\d{2}:?\d{2}))\.'

    match = re.search(COMPRESSED_PATTERN, filepath)

    if match:
        # Already compressed - replace the timestamp with current time
        base_path = filepath[:match.start()]
        ext_start = match.end() - 1  # Position before '.' in '.json'
        ext = filepath[ext_start:]

        from datetime import datetime, timezone
        new_timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return f"{base_path}-compressed-{new_timestamp}{ext}", True

    else:
        # Not yet compressed - add the compression marker
        base, ext = filepath.rsplit('.', 1) if '.' in filepath else (filepath, 'json')
        from datetime import datetime, timezone
        new_timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return f"{base}-compressed-{new_timestamp}.{ext}", False


def compress_session(session: object, fraction: float = 0.1) -> str | None:
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

    # Always save before mutating
    session.save()

    # Compress messages
    new_messages = compress_messages(session.messages, fraction)

    # If nothing changed, return None
    had_changes = False
    for orig_msg, comp_msg in zip(session.messages, new_messages):
        if len(comp_msg.get("content", "")) < len(orig_msg.get("content", "")):
            had_changes = True
            break

    if not had_changes:
        return None

    # Update filepath with compression marker
    old_path = session.filepath
    new_filepath, _ = build_compressed_filepath(old_path)

    # Replace messages and save to new location
    session.messages[:] = new_messages
    session._save_impl(new_filepath, save_state=True)

    return new_filepath


__all__ = [
    "compress_messages",
    "should_auto_compress",
    "build_compressed_filepath",
    "compress_session",
]
