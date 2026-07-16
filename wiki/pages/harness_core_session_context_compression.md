---
name: "harness_core.session.context_compression"
description: "Context Compression Module"
source: "harness_core/session/context_compression.py"
---

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

## References
- [_already_truncated](harness_core_session_context_compression__already_truncated) - Return True iff ``msg["content"]`` is a string starting with :data:`TRUNCATED_PREFIX`
- [compress_list_dir](harness_core_session_context_compression_compress_list_dir) - Truncate the entire content of a ``list_dir`` tool-result message
- [_extract_read_file_path](harness_core_session_context_compression__extract_read_file_path) - Best-effort extraction of a file path from a read_file result's content
- [_parse_tool_arguments](harness_core_session_context_compression__parse_tool_arguments) - Return the arguments dict from ``function
- [_update_filename_mapping](harness_core_session_context_compression__update_filename_mapping) - Populate *filename_by_tool_id* from a list of tool_call entries
- [compress_file_operation](harness_core_session_context_compression_compress_file_operation) - Truncate a file-operating tool-result (read/write/edit) iff the underlying
file has been modified since the message was created
- [_must_preserve](harness_core_session_context_compression__must_preserve) - Return True for messages whose content MUST be preserved verbatim
- [compress_messages](harness_core_session_context_compression_compress_messages) - Compress older messages in the list, preserving a portion at the end
- [should_auto_compress](harness_core_session_context_compression_should_auto_compress) - Determine if auto-compression should be triggered based on context utilization
- [build_compressed_filepath](harness_core_session_context_compression_build_compressed_filepath) - Build a new filepath for a compressed session file
- [compress_session](harness_core_session_context_compression_compress_session) - Compress a session's messages and rotate its save file
- [TRUNCATED_PREFIX](harness_core_session_context_compression_TRUNCATED_PREFIX) - Constant
- [LIST_DIR_TOOL_NAMES](harness_core_session_context_compression_LIST_DIR_TOOL_NAMES) - Constant
- [FILE_OPERATING_TOOLS](harness_core_session_context_compression_FILE_OPERATING_TOOLS) - Constant
- [Module Index](../index/harness_core_session.md) - Parent module index
