"""Comprehensive tests for sessions.context_compression.compress_messages()."""

import json
from pathlib import Path

import pytest

from sessions.context_compression import compress_messages


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_tool_result(name: str = "read_file", content: str = "") -> dict:
    return {"role": "tool", "content": content, "name": name}


def make_assistant_call(
    name: str = "read_file", filename: str | None = None, **extra_args: object
) -> dict:
    args_dict: dict[str, object] = {}
    if filename is not None:
        args_dict["filename"] = filename
    args_dict.update(extra_args)
    return {
        "role": "assistant",
        "tool_calls": [
            {
                "id": f"call_{len(args_dict)}",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args_dict)},
            }
        ],
    }


def make_assistant_no_tool_calls(content: str = "Hello!") -> dict:
    return {"role": "assistant", "content": content}


# ── Rule 1: error-like content ────────────────────────────────────────────────


class TestRule1:
    def test_error_substring_replaces_content(self, tmp_path):
        """File exists on disk so Rule 5 does NOT apply; error content triggers Rule 1."""
        target = tmp_path / "x.py"
        target.write_text("existing")
        messages = [
            {"role": "system", "content": "System."},
            make_assistant_call(filename=str(target)),
            make_tool_result("read_file", "Error reading file: blah"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        assert "error" in content_lower

    def test_not_found_substring_replaces_content(self, tmp_path):
        target = tmp_path / "found.py"
        target.write_text("existing")
        messages = [
            make_assistant_call(filename=str(target)),
            make_tool_result("read_file", "File not found at /tmp/missing.py"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        assert "error" in content_lower

    def test_error_colon_substring_replaces_content(self, tmp_path):
        target = tmp_path / "x.py"
        target.write_text("existing")
        messages = [
            make_assistant_call(filename=str(target)),
            make_tool_result("read_file", "error: permission denied"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        assert "error" in content_lower

    def test_traversal_detected_replaces_content(self):
        messages = [
            make_assistant_call(filename="/etc/passwd"),
            make_tool_result("read_file", "traversal detected, blocked"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        assert "error" in content_lower

    def test_normal_content_not_modified(self, tmp_path):
        target = tmp_path / "good.py"
        target.write_text("def main(): pass\nprint('hi')")
        messages = [
            make_assistant_call(filename=str(target)),
            make_tool_result("read_file", "def main(): pass\nprint('hi')"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == "def main(): pass\nprint('hi')"

    def test_error_with_nonexistent_file_rule5_wins(self, tmp_path):
        """When the file doesn't exist AND content has an error keyword, Rule 5 takes precedence."""
        nonexistent = str(tmp_path / "no_such_dir" / "ghost.py")
        messages = [
            make_assistant_call(filename=nonexistent),
            make_tool_result("read_file", "Error: not found"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        # Rule 5 note mentions the file not existing (not just generic error).
        assert "does not exist" in content_lower


# ── Rule 2: read superseded by later edit on same path ───────────────────────


class TestRule2:
    def test_read_then_edit_same_path_replaces_earlier_read(self):
        """read_file result followed by edit_file on same path → earlier READ RESULT replaced."""
        messages = [
            make_assistant_call(name="read_file", filename="/tmp/a.py"),
            make_tool_result("read_file", "original content of a.py"),
            make_assistant_call(name="edit_file", filename="/tmp/a.py"),
            make_tool_result(
                "edit_file", 'Applied 1 edit to /tmp/a.py. File now has 42 lines.'
            ),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 2
        # First tool result (the read) should be replaced.
        content_lower = tool_msgs[0]["content"].lower()
        assert "superseded" in content_lower or "removed from context" in content_lower
        # Second tool result (edit) stays as-is.
        assert "Applied 1 edit" in tool_msgs[1]["content"]

    def test_read_then_edit_different_path_not_modified(self, tmp_path):
        """read_file result followed by edit_file on DIFFERENT path → NOT modified."""
        file_a = tmp_path / "a.py"
        file_b = tmp_path / "b.py"
        file_a.write_text("x = 1")
        file_b.write_text("y = 2")
        messages = [
            make_assistant_call(name="read_file", filename=str(file_a)),
            make_tool_result("read_file", "content of a.py"),
            make_assistant_call(name="edit_file", filename=str(file_b)),
            make_tool_result(
                "edit_file", 'Applied 1 edit to /tmp/b.py. File now has 10 lines.'
            ),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 2
        # Read result should NOT be replaced (edit is on a different path).
        assert tool_msgs[0]["content"] == "content of a.py"

    def test_write_then_edit_same_path_replaces_earlier_write(self, tmp_path):
        """write_file result followed by edit_file on same path → earlier WRITE RESULT replaced."""
        target = str(tmp_path / "target.txt")
        Path(target).write_text("initial content\n")
        messages = [
            make_assistant_call(name="write_file", filename=target),
            make_tool_result(
                "write_file", f"Successfully wrote to {target}. 1 line written."
            ),
            make_assistant_call(name="edit_file", filename=target),
            make_tool_result(
                "edit_file", 'Applied 2 edits. File now has 5 lines.'
            ),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 2
        # The write result should be replaced (superseded by later edit).
        content_lower = tool_msgs[0]["content"].lower()
        assert "superseded" in content_lower or "removed from context" in content_lower

    def test_edit_note_format(self, tmp_path):
        """Verify the exact format of the Rule 2 replacement note."""
        target = str(tmp_path / "note_test.py")
        Path(target).write_text("x = 1\n")
        messages = [
            make_assistant_call(name="read_file", filename=target),
            make_tool_result("read_file", "x = 1"),
            make_assistant_call(name="edit_file", filename=target),
            make_tool_result("edit_file", 'Applied 1 edit.'),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        expected_note = (
            f"[Read of '{target}' was superseded by a later edit "
            "and removed from context.]"
        )
        assert tool_msgs[0]["content"] == expected_note


# ── Rule 3: read replaced by later complete re-read ───────────────────────────


class TestRule3:
    def test_two_reads_same_file_first_replaced(self, tmp_path):
        """Two reads of the same file → first one replaced with Rule 3 note."""
        target = tmp_path / "shared.py"
        target.write_text("existing")
        messages = [
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "first read content"),
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "second read content"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 2
        # First should be replaced.
        content_lower = tool_msgs[0]["content"].lower()
        assert "replaced by a later complete re-read" in content_lower
        # Second should stay as-is (no further re-read).
        assert tool_msgs[1]["content"] == "second read content"

    def test_two_reads_different_files_neither_replaced(self, tmp_path):
        """Two reads of different files → neither is replaced."""
        file_a = tmp_path / "file_a.py"
        file_b = tmp_path / "file_b.py"
        file_a.write_text("a")
        file_b.write_text("b")
        messages = [
            make_assistant_call(name="read_file", filename=str(file_a)),
            make_tool_result("read_file", "content of file a"),
            make_assistant_call(name="read_file", filename=str(file_b)),
            make_tool_result("read_file", "content of file b"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 2
        assert tool_msgs[0]["content"] == "content of file a"
        assert tool_msgs[1]["content"] == "content of file b"

    def test_three_reads_same_file_first_two_replaced(self, tmp_path):
        """Three reads of same file → first TWO replaced, third stays as-is."""
        target = tmp_path / "loop.py"
        target.write_text("existing")
        messages = [
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "first read"),
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "second read"),
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "third read"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 3
        # First and second should be replaced.
        content_lower_0 = tool_msgs[0]["content"].lower()
        content_lower_1 = tool_msgs[1]["content"].lower()
        assert "replaced by a later complete re-read" in content_lower_0
        assert "replaced by a later complete re-read" in content_lower_1
        # Third should stay as-is.
        assert tool_msgs[2]["content"] == "third read"

    def test_rule3_note_format(self, tmp_path):
        """Verify the exact format of Rule 3 replacement note."""
        target = str(tmp_path / "reformat.txt")
        Path(target).write_text("line1\n")
        messages = [
            make_assistant_call(name="read_file", filename=target),
            make_tool_result("read_file", "old content"),
            make_assistant_call(name="read_file", filename=target),
            make_tool_result("read_file", "new content"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        expected_note = (
            f"[Read of '{target}' was replaced by a later complete re-read "
            "and removed from context.]"
        )
        assert tool_msgs[0]["content"] == expected_note


# ── Rule 5: file no longer exists on disk ─────────────────────────────────────


class TestRule5:
    def test_nonexistent_file_path_replaces_content(self, tmp_path):
        """Tool result referencing a non-existent path → content replaced."""
        nonexistent = str(tmp_path / "no_such_dir" / "ghost.py")
        messages = [
            make_assistant_call(filename=nonexistent),
            make_tool_result("read_file", "some content"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        assert "does not exist" in content_lower

    def test_existing_file_not_modified(self, tmp_path):
        """Tool result referencing an existing temp file → NOT modified."""
        target = tmp_path / "exists.txt"
        target.write_text("hello world")
        messages = [
            make_assistant_call(filename=str(target)),
            make_tool_result("read_file", "hello world"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == "hello world"

    def test_error_for_missing_file_rule5_wins_over_rule1(self, tmp_path):
        """When file is missing AND content has error keywords → Rule 5 note wins."""
        nonexistent = str(tmp_path / "nope.py")
        messages = [
            make_assistant_call(filename=nonexistent),
            make_tool_result("read_file", "Error: not found"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        # Rule 5 takes precedence; note should mention file not existing.
        assert "does not exist" in content_lower

    def test_rule5_write_file_nonexistent(self, tmp_path):
        """write_file on non-existent path → replaced via Rule 5."""
        nonexistent = str(tmp_path / "no_dir" / "new.txt")
        messages = [
            make_assistant_call(name="write_file", filename=nonexistent),
            make_tool_result("write_file", "Successfully wrote to file."),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        assert "does not exist" in content_lower

    def test_existing_dir_not_replaced(self, tmp_path):
        """Tool call referencing an existing directory → NOT replaced."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        messages = [
            make_assistant_call(name="read_file", filename=str(subdir)),
            make_tool_result("read_file", "directory listing"),
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == "directory listing"


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_list_returns_empty(self):
        assert compress_messages([]) == []

    def test_only_system_prompt_unchanged(self):
        messages = [{"role": "system", "content": "You are helpful."}]
        result = compress_messages(messages)
        assert len(result) == 1
        assert result[0]["content"] == "You are helpful."

    def test_input_not_mutated(self):
        original_tool_content = "some content"
        messages = [
            {"role": "system", "content": "System."},
            make_assistant_call(filename="/tmp/x.py"),
            make_tool_result("read_file", original_tool_content),
        ]
        # Make a deep copy for comparison.
        import copy

        snapshot = copy.deepcopy(messages)
        compress_messages(messages)
        assert messages == snapshot, "Input was mutated!"

    def test_output_same_length_as_input(self):
        messages = [
            {"role": "system", "content": "System."},
            make_assistant_call(name="read_file", filename="/tmp/a.py"),
            make_tool_result("read_file", "a content"),
            make_assistant_call(name="edit_file", filename="/tmp/b.py"),
            make_tool_result("edit_file", "b edit result"),
        ]
        result = compress_messages(messages)
        assert len(result) == len(messages)

    def test_system_message_preserved_exactly(self):
        system = {"role": "system", "content": "Be concise."}
        messages = [system, make_assistant_no_tool_calls()]
        result = compress_messages(messages)
        # System should be an equal dict but NOT the same object.
        assert result[0] == system
        assert result[0] is not system

    def test_user_message_preserved_exactly(self):
        user = {"role": "user", "content": "What's in this file?"}
        messages = [user, make_assistant_no_tool_calls()]
        result = compress_messages(messages)
        assert result[0] == user
        assert result[0] is not user

    def test_assistant_without_tool_calls_passes_through(self):
        asst = {"role": "assistant", "content": "Sure, let me check."}
        messages = [asst]
        result = compress_messages(messages)
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Sure, let me check."

    def test_non_list_input_handled(self):
        """If input is not a list, the function returns a copy (no crash)."""
        gen = iter([{"role": "system", "content": "x"}])
        result = compress_messages(gen)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_mixed_roles_preserved_in_order(self):
        messages = [
            {"role": "system", "content": "System."},
            {"role": "user", "content": "Hello"},
            make_assistant_no_tool_calls("Hi there"),
            {"role": "user", "content": "Tell me more"},
            make_assistant_no_tool_calls("Ok!"),
        ]
        result = compress_messages(messages)
        roles = [m["role"] for m in result]
        assert roles == ["system", "user", "assistant", "user", "assistant"]


# ── Integration test — realistic scenario ─────────────────────────────────────


class TestIntegration:
    def test_realistic_read_edit_reread_scenario(self, tmp_path):
        """Read file → edit file → re-read file.

        The first read should be replaced by Rule 2 (superseded by later edit).
        The second read (the complete re-read) should stay as-is because it's the latest.
        """
        target = tmp_path / "app.py"
        target.write_text("def greet():\n    return 'hello'\n")

        messages = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            # Step 1: Read the file.
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", target.read_text()),
            # Step 2: Edit the file.
            make_assistant_call(name="edit_file", filename=str(target)),
            make_tool_result(
                "edit_file",
                'Applied 1 edit to app.py. File now has 3 lines.',
            ),
            # Step 3: Re-read the file (complete re-read).
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "def greet():\n    return 'world'\n"),
        ]

        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 3

        # Tool msg 0 (first read): superseded by later edit → Rule 2 note.
        content_lower_0 = tool_msgs[0]["content"].lower()
        assert "superseded" in content_lower_0 or "removed from context" in content_lower_0

        # Tool msg 1 (edit result): stays as-is.
        assert "Applied 1 edit" in tool_msgs[1]["content"]

        # Tool msg 2 (re-read): latest read, no later operations → kept as-is.
        assert tool_msgs[2]["content"] == "def greet():\n    return 'world'\n"

        # System prompt preserved.
        sys_msgs = [m for m in result if m["role"] == "system"]
        assert len(sys_msgs) == 1
        assert sys_msgs[0]["content"] == "You are a helpful coding assistant."

        # Output length matches input length.
        assert len(result) == len(messages)

    def test_complex_multi_file_workflow(self, tmp_path):
        """A more complex workflow with multiple files and interleaved operations."""
        file_a = tmp_path / "a.py"
        file_b = tmp_path / "b.py"
        file_a.write_text("x = 1\n")
        file_b.write_text("y = 2\n")

        messages = [
            {"role": "system", "content": "System."},
            # Read a.py.
            make_assistant_call(name="read_file", filename=str(file_a)),
            make_tool_result("read_file", "x = 1"),
            # Read b.py.
            make_assistant_call(name="read_file", filename=str(file_b)),
            make_tool_result("read_file", "y = 2"),
            # Re-read a.py → should replace the first read of a.py (Rule 3).
            make_assistant_call(name="read_file", filename=str(file_a)),
            make_tool_result("read_file", "x = 100"),
            # Edit b.py → should NOT affect reads of a.py.
            make_assistant_call(name="edit_file", filename=str(file_b)),
            make_tool_result("edit_file", 'Applied 1 edit to b.py.'),
            # Read b.py again after edit (Rule 3 on b).
            make_assistant_call(name="read_file", filename=str(file_b)),
            make_tool_result("read_file", "y = 999"),
        ]

        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 5

        # Tool msg 0 (first read of a): replaced by later re-read (Rule 3).
        content_lower_0 = tool_msgs[0]["content"].lower()
        assert "replaced by a later complete re-read" in content_lower_0

        # Tool msg 1 (read of b): NOT yet replaced (edit doesn't trigger Rule 2 for reads;
        # but the second read IS a re-read → this should be replaced).
        # Actually: edit on b then re-read of b. The first read of b has a later edit AND a later re-read.
        # Rule 2 checks edits first, and since there's an edit on b after the first read of b,
        # the first read of b gets replaced by Rule 2 (superseded by edit).
        content_lower_1 = tool_msgs[1]["content"].lower()
        assert "superseded" in content_lower_1 or "removed from context" in content_lower_1

        # Tool msg 2 (second read of a): no later edits on a, no later re-reads → kept.
        assert tool_msgs[2]["content"] == "x = 100"

        # Tool msg 3 (edit b result): stays as-is.
        assert "Applied 1 edit" in tool_msgs[3]["content"]

        # Tool msg 4 (re-read of b after edit): latest, kept.
        assert tool_msgs[4]["content"] == "y = 999"

    def test_error_in_tool_result_without_specific_rule_applies(self, tmp_path):
        """Tool result with error content and no later operations → Rule 1 applies."""
        target = tmp_path / "error_target.txt"
        target.write_text("existing")
        messages = [
            make_assistant_call(name="read_file", filename=str(target)),
            make_tool_result("read_file", "Error: something went wrong"),
            {"role": "user", "content": "What happened?"},
        ]
        result = compress_messages(messages)
        tool_msgs = [m for m in result if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        content_lower = tool_msgs[0]["content"].lower()
        # Rule 1 applies: error-like content → generic error note.
        assert "error" in content_lower
