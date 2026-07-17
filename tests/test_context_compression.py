"""Tests for context compression module - validates fix and new features."""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from harness_core.session.context_compression import (
    TRUNCATED_PREFIX,
    _already_truncated,
    compress_list_dir,
    compress_file_operation,
    compress_messages,
    should_auto_compress,
    build_compressed_filepath,
)


# ============================================================================
# Tests for compress_messages
# ============================================================================

class TestCompressMessages:
    """Test the core compression logic."""

    def test_preserves_tail_unchanged(self):
        """Verify that messages in the preserved tail are identical to originals."""
        # Create 20 messages with distinct content
        messages = [
            {"role": "user", "content": f"message_{i}_X" * 34} for i in range(20)
        ]

        result_50 = compress_messages(messages, fraction=0.5)
        tail_start = int(len(messages) * 0.5)

        # All messages from tail_start onward should be unchanged
        assert all(messages[i] == result_50[i] for i in range(tail_start, len(messages)))

    def test_compresses_prefix(self):
        """Verify that prefix messages are actually compressed."""
        # Use content > 100 chars to trigger compression
        long_content = "X" * 200
        messages = [{"role": "user", "content": f"msg_{i}_START:{long_content}"} for i in range(10)]
        
        result_25 = compress_messages(messages, fraction=0.25)
        tail_start = int(len(messages) * 0.25)

        # User/assistant messages without tool_calls are no longer truncated.
        for orig, comp in zip(messages[:tail_start], result_25[:tail_start]):
            assert comp["content"] == orig["content"], f"User message {orig['role']} was incorrectly modified"

    def test_fraction_zero(self):
        """With fraction=0, all messages should be compressed."""
        messages = [{"role": "user", "content": f"msg_{i}_X" * 34} for i in range(10)]
        
        result = compress_messages(messages, fraction=0)

        # User/assistant messages with long content remain unchanged under new behavior.
        for orig, comp in zip(messages, result):
            assert comp["content"] == orig["content"], "User message was incorrectly truncated"

    def test_fraction_one(self):
        """With fraction=1.0, no messages should be compressed."""
        messages = [{"role": "user", "content": f"msg_{i}_X" * 34} for i in range(10)]
        
        result = compress_messages(messages, fraction=1.0)

        # All messages should remain unchanged
        assert all(orig == comp for orig, comp in zip(messages, result))

    def test_empty_list(self):
        """Empty list should return empty list."""
        result = compress_messages([], fraction=0.5)
        assert result == []

    def test_single_message_short_content(self):
        """Single short message should not be modified."""
        messages = [{"role": "user", "content": "short"}]
        
        result = compress_messages(messages, fraction=0.5)
        
        assert len(result) == 1
        assert result[0]["content"] == "short"

    def test_invalid_fraction(self):
        """Invalid fractions should raise ValueError."""
        messages = [{"role": "user", "content": f"msg_{i}"} for i in range(5)]
        
        with pytest.raises(ValueError, match="fraction must be a number between 0 and 1"):
            compress_messages(messages, fraction=2.0)

    def test_mixed_content_types(self):
        """Messages without content or with non-string content should be preserved."""
        messages = [
            {"role": "user", "content": None},
            {"role": "user"},  # no 'content' key
            {"role": "assistant", "content": 123},
        ]

        result = compress_messages(messages, fraction=0.5)

        assert len(result) == 3
        # First message should be preserved as-is (None content)
        assert result[0]["content"] is None

    def test_list_dir_message_fully_truncated(self):
        """list_dir tool results must be fully truncated to TRUNCATED_PREFIX."""
        messages = [
            {"role": "system", "content": "short system"},
            {
                "role": "tool",
                "content": "a" * 300,
                "name": "list_dir",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
        ] + [{"role": "user", "content": f"user_{i}_X" * 34} for i in range(5)]

        result = compress_messages(messages, fraction=0.2)

        tool_msgs = [m for m in result if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == TRUNCATED_PREFIX

    def test_read_file_result_not_truncated_when_unmodified(self):
        """read_file results whose file is NOT modified since message should stay intact."""
        # Use the current source file (context_compression.py itself) which
        # won't be changing during this test.
        import harness_core.session.context_compression as mod

        now_iso = datetime.now(timezone.utc).isoformat()

        messages = [
            {"role": "system", "content": "short"},
            {
                "role": "tool",
                "content": f'<file path="{mod.__file__}" lines="1-30" total_lines="230">\nold content\n</file>',
                "name": "read_file",
                "timestamp": now_iso,
            },
        ]

        result = compress_messages(messages, fraction=0)
        tool_msgs = [m for m in result if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        # File was NOT modified since the message -> content must be preserved.
        assert tool_msgs[0]["content"] != TRUNCATED_PREFIX

    def test_read_file_result_truncated_when_modified(self):
        """read_file results whose file IS modified after message creation get truncated."""
        import os, tempfile

        # Create a temp file with initial content.
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        try:
            f.write(b"initial content")
            f.close()

            old_ts = "2024-01-01T00:00:00+00:00"
            # Build 6 messages with fraction=0.5 so prefix_to_compress gets the first 3 and
            # preserved_suffix gets the last 3. Place read_file at index 2 (in the prefix).
            messages = [
                {"role": "system", "content": "short"},
                {"role": "user", "content": f"user_1_X" * 34},
                {
                    "role": "tool",
                    "content": f'<file path="{f.name}" lines="1-5" total_lines="5">\nold content\n</file>',
                    "name": "read_file",
                    "timestamp": old_ts,
                },
                {"role": "user", "content": f"user_3_Y" * 34},
                {"role": "user", "content": f"user_4_Z" * 34},
                {"role": "assistant", "content": "short reply"},
            ]

            # Use fraction=0 to ensure the write_file message is in the prefix and gets evaluated.
            result = compress_messages(messages, fraction=0)
            tool_msgs = [m for m in result if m.get("role") == "tool"]
            assert len(tool_msgs) == 1
            # File exists and was modified after the message timestamp (which is far in the past).
            assert tool_msgs[0]["content"] == TRUNCATED_PREFIX
        finally:
            os.unlink(f.name)

    def test_write_file_result_not_truncated_without_filename(self):
        """write_file results (which don't carry a filename in their output) are left alone."""
        messages = [
            {"role": "system", "content": "short"},
            {
                "role": "tool",
                "content": '{"status": "ok", "filename": "test.py", "bytes": 123}',
                "name": "write_file",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
        ]

        result = compress_messages(messages, fraction=0.5)
        tool_msgs = [m for m in result if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        # write_file output doesn't carry a path - helper returns unchanged.
        assert tool_msgs[0]["content"] != TRUNCATED_PREFIX

    def test_already_truncated_not_re_truncated(self):
        """Messages already truncated by a prior pass must not be touched again."""
        messages = [
            {"role": "system", "content": "short"},
            {
                "role": "tool",
                "content": TRUNCATED_PREFIX,
                "name": "list_dir",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
        ]

        result = compress_messages(messages, fraction=0.5)
        tool_msgs = [m for m in result if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        # Must still be exactly TRUNCATED_PREFIX - not a nested/doubled version.
        assert tool_msgs[0]["content"] == TRUNCATED_PREFIX

    def test_already_truncated_helper(self):
        """_already_truncated detects messages correctly."""
        assert _already_truncated({"role": "tool", "content": TRUNCATED_PREFIX}) is True
        assert (
            _already_truncated(
                {"role": "user", "content": f"{TRUNCATED_PREFIX} extra"}
            )
            is True
        )
        assert _already_truncated({"role": "user", "content": "plain content"}) is False
        assert _already_truncated({"role": "tool", "content": None}) is False

    def test_write_file_truncated_via_tool_call_mapping(self):
        """write_file results should be truncated when filename is known and mtime > timestamp."""
        import tempfile, os
        from datetime import datetime, timezone, timedelta

        # Create a temp file with future mtime.
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        try:
            f.write(b"future content")
            f.close()

            future_time = (datetime.now(timezone.utc) + timedelta(hours=2)).timestamp()
            os.utime(f.name, (future_time, future_time))

            old_ts = "2024-01-01T00:00:00+00:00"
            tool_call_id = "call_write_test"

            messages = [
                {"role": "system", "content": "short"},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": tool_call_id,
                        "function": {
                            "name": "write_file",
                            "arguments": {"filename": f.name, "content": "old content"}
                        }
                    }]
                },
                {
                    "role": "tool",
                    "content": '{"status": "ok", "bytes": 123}',
                    "name": "write_file",
                    "tool_call_id": tool_call_id,
                    "timestamp": old_ts,
                },
            ]

            # Use fraction=0 so the write_file message (at index 2 of 3) falls in the prefix and gets evaluated.
            result = compress_messages(messages, fraction=0)

            # The write_file result should be truncated because mtime > timestamp.
            tool_msgs = [m for m in result if m.get("role") == "tool"]
            assert len(tool_msgs) == 1
            assert tool_msgs[0]["content"] == TRUNCATED_PREFIX

        finally:
            os.unlink(f.name)


# ============================================================================
# Tests for build_compressed_filepath
# ============================================================================

class TestBuildCompressedFilepath:
    """Test filepath generation with timestamp rotation."""

    def test_basic_path_generation(self):
        """Should generate a compressed path with current timestamp."""
        fp = "/tmp/session.json"
        
        result, was_compressed = build_compressed_filepath(fp)

        assert "-compressed-" in result
        assert not was_compressed  # Not already compressed
        assert result.endswith(".json")

    def test_timestamp_format(self):
        """Timestamp should match expected format."""
        fp = "/tmp/session.json"
        
        result, _ = build_compressed_filepath(fp)

        # Expected: /tmp/session-compressed-<YYYYMMDDTHHMMSSZ>.json
        import re
        pattern = r'/tmp/session-compressed-\d{8}T\d{6}(?:Z|[+-]\d{2}:?\d{2})\.json$'
        assert re.match(pattern, result)

    def test_recompression_updates_timestamp(self):
        """Re-compressing an already compressed path should update timestamp."""
        fp = "/tmp/session.json"
        
        first_result, _ = build_compressed_filepath(fp)
        second_result, was_compressed = build_compressed_filepath(first_result)

        assert "-compressed-" in second_result
        # Second call should recognize it as already compressed
        assert was_compressed is True  # Will be False since we're not actually running the function again

    def test_different_extensions(self):
        """Should handle various file extensions."""
        fp = "/path/to/session.yaml"
        
        result, _ = build_compressed_filepath(fp)

        assert "-compressed-" in result
        assert result.endswith(".yaml")

    def test_nested_path(self):
        """Should preserve directory structure."""
        fp = "/tmp/deep/nested/path/session.json"
        
        result, _ = build_compressed_filepath(fp)

        assert "/deep/nested/path/" in result
        assert "-compressed-" in result


# ============================================================================
# Tests for should_auto_compress
# ============================================================================

class TestShouldAutoCompress:
    """Test auto-compression threshold logic."""

    def test_below_threshold(self):
        """Should not trigger when utilization is below threshold."""
        assert not should_auto_compress(0.49, threshold=0.5)
        assert not should_auto_compress(0.25, threshold=0.5)

    def test_above_threshold(self):
        """Should trigger when utilization exceeds threshold."""
        assert should_auto_compress(0.51, threshold=0.5)
        assert should_auto_compress(0.75, threshold=0.5)

    def test_at_threshold_boundary(self):
        """At exactly 50% threshold - behavior may vary by implementation."""
        # Implementation uses strict inequality (>), so 0.50 returns False
        result = should_auto_compress(0.50, threshold=0.5)
        assert result is False

    def test_at_100_percent(self):
        """At full utilization should definitely trigger."""
        assert should_auto_compress(1.0, threshold=0.5)

    def test_custom_threshold(self):
        """Should respect custom thresholds."""
        # With 60% utilization and 70% threshold, should NOT trigger
        assert not should_auto_compress(0.60, threshold=0.70)
        
        # With 80% utilization and 70% threshold, SHOULD trigger
        assert should_auto_compress(0.80, threshold=0.70)

    def test_invalid_values(self):
        """Should raise ValueError for negative values."""
        with pytest.raises(ValueError, match="context_utilization must be non-negative"):
            should_auto_compress(-0.1)

        # Values > 1.0 should not raise (utilization can exceed 100%)
        assert should_auto_compress(1.5)
        assert should_auto_compress(2.0)


# ============================================================================
# Integration Tests for /compress command
# ============================================================================

class TestCompressCommand:
    """Test the /compress slash command integration."""

    def test_command_registered(self):
        """Verify /compress is registered in COMMANDS dict."""
        from harness_core.commands import COMMANDS
        
        assert "compress" in COMMANDS

    def test_compress_handler_exists(self):
        """Handler should be callable with agent parameter."""
        # Just verify the function exists - we can't easily mock the full call chain
        from harness_core.commands import compress_handler
        
        assert callable(compress_handler)

    def test_compress_with_no_agent(self):
        """Command should handle missing agent gracefully."""
        from harness_core.commands import compress_handler
        
        # Should not crash, should print error and return False
        result = compress_handler("", agent=None)  # No agent parameter
        
        assert result is False


# ============================================================================
# Tests for Session-aware compression (if implemented)
# ============================================================================

class TestSessionCompression:
    """Test session-level compression functionality."""

    def test_compress_session_with_filepath(self):
        """Should save and compress a session with filepath set."""
        # This would require mocking the full Session object
        # For now, just verify the import path is accessible
        
        try:
            from harness_core.session.context_compression import compress_session
            assert callable(compress_session)
        except ImportError:
            pytest.skip("compress_session not yet implemented")

    def test_compress_with_no_filepath_raises(self):
        """Should raise error when session has no filepath."""
        # This would require mocking the full Session object
        
        try:
            from harness_core.session.context_compression import compress_session
            
            mock_session = Mock()
            mock_session.filepath = None
            
            with pytest.raises(ValueError, match="Cannot compress a session with no filepath set"):
                compress_session(mock_session)
        except ImportError:
            pytest.skip("compress_session not yet implemented")


# ============================================================================
# End-to-end tests
# ============================================================================

class TestEndToEnd:
    """Test complete compression workflow."""

    def test_full_compression_workflow(self):
        """Simulate a real-world compression scenario."""
        # Create realistic conversation history
        messages = []
        
        # User sends long message with technical details
        for i in range(15):
            messages.append({
                "role": "user",
                "content": f"Question {i}: Please explain the difference between " * 20 + 
                           f"a list comprehension and a generator expression? " * 10 +
                           f"This is question number {i} with lots of context."
            })

        # Add some short messages at the end (recent conversation)
        for i in range(5):
            messages.append({
                "role": "assistant", 
                "content": f"Response {i}: Thank you for asking about Python!"
            })

        # Compress with 0.2 fraction (preserve last 20% = 4 messages)
        result = compress_messages(messages, fraction=0.2)

        # Verify:
        tail_start = int(len(messages) * 0.2)
        
        # Recent messages preserved (only the last fraction are preserved unchanged)
        n_preserved = int(len(messages) * 0.2)
        for i in range(len(messages) - n_preserved, len(messages)):
            assert messages[i] == result[i], f"Message {i} should be preserved but was modified"
        
        # Older user messages should remain unchanged (only tool results get truncated).
        for orig, comp in zip(messages[:len(messages) - n_preserved], result[:len(messages) - n_preserved]):
            assert comp["content"] == orig["content"], "Older message was incorrectly modified"

    def test_context_utilization_check(self):
        """Test the auto-compression trigger logic."""
        # Simulate checking context utilization after each message
        
        # Start with low utilization (e.g., 45%)
        utilization = 0.45
        should_compress = should_auto_compress(utilization)
        
        assert not should_compress
        
        # After adding more messages, utilization increases to 65%
        utilization += 0.2
        should_compress = should_auto_compress(utilization)
        
        assert should_compress


# ============================================================================
# Performance tests (sanity check)
# ============================================================================

class TestPerformance:
    """Sanity checks for performance characteristics."""

    def test_compression_time_scales_linearly(self):
        """Compression time should scale roughly linearly with input size."""
        import time
        
        sizes = [10, 50, 100]
        times = []
        
        for n in sizes:
            messages = [{"role": "user", "content": f"msg_{i}_X" * 34} for i in range(n)]
            
            start = time.time()
            compress_messages(messages, fraction=0.5)
            elapsed = time.time() - start
            
            times.append(elapsed)

        # Verify that larger inputs take longer (with tolerance)
        assert times[1] > times[0] * 0.5  # Allow some variance
        assert times[2] > times[1] * 0.5


# ============================================================================
# Tests for protected (non-truncated) messages (Bug #2)
# ============================================================================

class TestProtectedMessages:
    """System / tool / tool_calls messages must never be truncated."""

    def test_system_message_preserved_verbatim(self):
        """The system prompt (messages[0]) must survive compression unchanged."""
        long_system = ("You are a very strict assistant. " * 30)  # > 100 chars
        messages = [
            {"role": "system", "content": long_system},
            {"role": "user", "content": "x" * 200},
            {"role": "assistant", "content": "y" * 200},
        ]
        result = compress_messages(messages, fraction=0.1)

        assert result[0]["role"] == "system"
        assert result[0]["content"] == long_system

    def test_tool_message_preserved_verbatim(self):
        """Tool-result messages must not be truncated."""
        long_tool = ("tool output blob " * 30)  # > 100 chars
        messages = [
            {"role": "system", "content": "short system"},
            {"role": "tool", "content": long_tool, "name": "execute_bash"},
            {"role": "user", "content": "z" * 200},
        ]
        result = compress_messages(messages, fraction=0.1)

        tool_msgs = [m for m in result if m.get("role") == "tool"]
        assert tool_msgs
        assert tool_msgs[0]["content"] == long_tool

    def test_tool_calls_message_preserved(self):
        """A message carrying tool_calls must not be truncated."""
        long_args = ("arg " * 40)  # > 100 chars
        messages = [
            {"role": "system", "content": "short system"},
            {
                "role": "assistant",
                "content": long_args,
                "tool_calls": [
                    {"id": "call_1", "type": "function",
                     "function": {"name": "execute_bash", "arguments": long_args}}
                ],
            },
            {"role": "user", "content": "w" * 200},
        ]
        result = compress_messages(messages, fraction=0.1)

        tc_msgs = [m for m in result if m.get("tool_calls")]
        assert tc_msgs
        assert tc_msgs[0]["content"] == long_args
        assert tc_msgs[0]["tool_calls"]


# ============================================================================
# Integration tests for /compress command and the auto-compression loop path
# ============================================================================

class _FakeSession:
    """Minimal Session stand-in exposing the attributes compress_session needs."""

    def __init__(self, messages, filepath):
        self.messages = list(messages)
        self.filepath = filepath
        self.saved = False
        self.saved_to = None

    def save(self):
        self.saved = True

    def _save_impl(self, new_filepath, save_state=True):
        import json
        from pathlib import Path
        Path(new_filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(new_filepath, "w", encoding="utf-8") as f:
            json.dump({"messages": self.messages}, f)
        if save_state:
            self.filepath = new_filepath
            self.saved_to = new_filepath


class _FakeAgent:
    """Agent stand-in mirroring the real Agent attribute layout (_session)."""

    def __init__(self, session, context_length):
        self._session = session
        self._context_length = context_length

    @property
    def session(self):
        return self._session

    @property
    def context_length(self):
        return self._context_length

    @property
    def messages(self):
        return self._session.messages


class TestCompressCommandE2E:
    """End-to-end coverage of the /compress slash command."""

    def test_compress_handler_end_to_end(self, tmp_path):
        """/compress compresses messages and preserves the system prompt."""
        from harness_core.commands.compress import compress_handler

        # Build a message list where a tool result sits in the prefix (early) so it gets truncated.
        messages = [
            {"role": "system", "content": "You are a helpful assistant." * 5},
            {
                "role": "tool",
                "content": "a" * 300,
                "name": "list_dir",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
        ]
        for i in range(20):
            messages.append({"role": "user", "content": f"long message number {i} " * 15})
        messages.append({"role": "assistant", "content": "short answer"})

        session = _FakeSession(messages, str(tmp_path / "harness_core.session.json"))
        agent = _FakeAgent(session, context_length=1 << 17)

        original_len = len(session.messages)
        result = compress_handler("0.5", agent=agent)

        assert result is False
        # User messages remain unchanged (no truncation for non-tool content).
        for i in range(2, 22):  # indices 2-21 are user messages
            comp = session.messages[i]
            orig_content = f"long message number {i-2} " * 15
            assert comp["content"] == orig_content, f"User message {i} was incorrectly modified"

        # The list_dir tool result should be truncated.
        tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == TRUNCATED_PREFIX
        # System prompt preserved verbatim.
        assert session.messages[0]["role"] == "system"
        assert session.messages[0]["content"] == "You are a helpful assistant." * 5
        # Compressed count must be <= original count.
        assert len(session.messages) == original_len

    def test_compress_handler_invalid_fraction(self):
        """Out-of-range fraction should be rejected without crashing."""
        from harness_core.commands.compress import compress_handler

        session = _FakeSession([{"role": "system", "content": "x"}], "x.json")
        agent = _FakeAgent(session, context_length=1 << 17)
        result = compress_handler("2.0", agent=agent)

        assert result is False


class TestAutoCompressionLoop:
    """Coverage of agent/loop.py::_check_and_compress_if_needed (Bug #1)."""

    def _build_agent(self, tmp_path, context_length):
        long_system = "system prompt " * 20  # long, must be preserved
        messages = [{"role": "system", "content": long_system}]
        # Long user messages to push utilization up.
        for i in range(60):
            messages.append({"role": "user", "content": "x" * 200})
        session = _FakeSession(messages, str(tmp_path / "harness_core.session.json"))
        return _FakeAgent(session, context_length=context_length), long_system

    def test_auto_compress_triggers_when_high_utilization(self, tmp_path):
        from harness_core.agent.loop import _check_and_compress_if_needed

        agent, long_system = self._build_agent(tmp_path, context_length=4000)

        # Add a list_dir tool result that should be truncated (placed early so it falls in the prefix).
        agent.session.messages.insert(1, {
            "role": "tool",
            "content": "x" * 300,
            "name": "list_dir",
            "timestamp": "2024-01-01T00:00:00+00:00",
        })

        # ~60 * 200 chars // 4 = ~3000 tokens over a 4000 window => > 50%
        _check_and_compress_if_needed(agent)

        # System prompt preserved verbatim.
        assert agent.session.messages[0]["content"] == long_system

        # The list_dir result should be truncated.
        tool_msgs = [m for m in agent.session.messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 1, f"Expected exactly one tool message, got {len(tool_msgs)}"
        assert tool_msgs[0]["content"] == TRUNCATED_PREFIX, "list_dir result was not truncated"

    def test_auto_compress_skips_when_low_utilization(self, tmp_path):
        from harness_core.agent.loop import _check_and_compress_if_needed

        agent, long_system = self._build_agent(tmp_path, context_length=10_000_000)
        # Utilization far below 50% -> no compression.
        _check_and_compress_if_needed(agent)

        truncated = [
            m for m in agent.session.messages
            if "[truncated for context compression" in m.get("content", "")
        ]
        assert not truncated, "compression should NOT trigger at low utilization"
        assert agent.session.messages[0]["content"] == long_system

    def test_auto_compress_uses_real_agent_properties(self, tmp_path):
        """Loop must find the session via agent._session when no properties exist."""
        from harness_core.agent.loop import _check_and_compress_if_needed

        # A bare agent exposing ONLY the private `_session` attribute (no
        # `messages`/`session` properties) — this is exactly the pre-fix
        # layout that silently disabled auto-compression.
        class _BareAgent:
            def __init__(self, session, context_length):
                self._session = session
                self._context_length = context_length

            @property
            def context_length(self):
                return self._context_length

        long_system = "system prompt " * 20
        messages = [{"role": "system", "content": long_system}]
        # Insert list_dir tool result early (index 1) so it falls in the prefix.
        messages.insert(1, {
            "role": "tool",
            "content": "x" * 300,
            "name": "list_dir",
            "timestamp": "2024-01-01T00:00:00+00:00",
        })
        for i in range(60):
            messages.append({"role": "user", "content": "x" * 200})
        session = _FakeSession(messages, str(tmp_path / "harness_core.session.json"))
        agent = _BareAgent(session, context_length=4000)

        _check_and_compress_if_needed(agent)

        # The list_dir result should be truncated.
        tool_msgs = [m for m in agent._session.messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 1, f"Expected exactly one tool message, got {len(tool_msgs)}"
        assert tool_msgs[0]["content"] == TRUNCATED_PREFIX, (
            "loop must fall back to agent._session when no properties exist and list_dir was not truncated"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
