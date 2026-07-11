"""Top-level session package exposing Session management and compression utilities."""

from .session import Session
from .session_utils import (
    format_session_yaml,
    parse_session_yaml,
    create_session_filename,
    ensure_sessions_dir,
)
from .context_compression import compress_session, compress_messages, should_auto_compress, build_compressed_filepath

__all__ = [
    "Session",
    "format_session_yaml",
    "parse_session_yaml",
    "create_session_filename",
    "ensure_sessions_dir",
    "compress_session",
    "compress_messages",
    "should_auto_compress",
    "build_compressed_filepath",
]
