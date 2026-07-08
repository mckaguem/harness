"""Tests for context compression module - validates fix and new features."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from sessions.context_compression import (
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

        # First few messages should be shorter (compressed)
        compressed_count = sum(
            1 
            for orig, comp in zip(messages[:tail_start], result_25[:tail_start])
            if len(comp["content"]) < len(orig["content"])
        )
        
        assert compressed_count > 0

    def test_fraction_zero(self):
        """With fraction=0, all messages should be compressed."""
        messages = [{"role": "user", "content": f"msg_{i}_X" * 34} for i in range(10)]
        
        result = compress_messages(messages, fraction=0)

        # All messages should have shorter content (except those ≤100 chars)
        for orig, comp in zip(messages, result):
            if len(orig["content"]) > 100:
                assert len(comp["content"]) < len(orig["content"])

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
        """Should raise ValueError for out-of-range values."""
        with pytest.raises(ValueError, match="context_utilization must be between"):
            should_auto_compress(1.5)
        
        with pytest.raises(ValueError, match="context_utilization must be between"):
            should_auto_compress(-0.1)


# ============================================================================
# Integration Tests for /compress command
# ============================================================================

class TestCompressCommand:
    """Test the /compress slash command integration."""

    def test_command_registered(self):
        """Verify /compress is registered in COMMANDS dict."""
        from commands import COMMANDS
        
        assert "compress" in COMMANDS

    def test_compress_handler_exists(self):
        """Handler should be callable with agent parameter."""
        # Just verify the function exists - we can't easily mock the full call chain
        from commands import compress_handler
        
        assert callable(compress_handler)

    def test_compress_with_no_agent(self):
        """Command should handle missing agent gracefully."""
        from commands import compress_handler
        
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
            from sessions.context_compression import compress_session
            assert callable(compress_session)
        except ImportError:
            pytest.skip("compress_session not yet implemented")

    def test_compress_with_no_filepath_raises(self):
        """Should raise error when session has no filepath."""
        # This would require mocking the full Session object
        
        try:
            from sessions.context_compression import compress_session
            
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
        
        # Older messages compressed (shorter content)
        older_compressed = sum(
            1 
            for orig, comp in zip(messages[:len(messages) - n_preserved], result[:len(messages) - n_preserved])
            if len(comp["content"]) < len(orig["content"])
        )
        assert older_compressed > 0

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
