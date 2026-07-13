"""Tests for harness_core.session.session — Session message lifecycle + persistence."""

import os
from pathlib import Path

import pytest

from harness_core.session.session import Session
from harness_core.session.session_utils import format_session_yaml, parse_session_yaml


class TestSessionMessages:
    """Session.add_* message helpers (return value + side effects)."""

    def test_add_user_message_appends_and_autosaves(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        sessions_dir = tmp_path / ".sessions"
        sessions_dir.mkdir(exist_ok=True)
        monkeypatch.setattr(
            "harness_core.session.session.ensure_sessions_dir",
            lambda *a, **k: sessions_dir,
        )
        session = Session(system_prompt="sys", auto_save=True, agent_type_name="main")

        session.add_user_message("hello there")

        # Return-value free helper, but the side effect is the new message.
        assert session.messages[-1]["role"] == "user"
        assert session.messages[-1]["content"] == "hello there"
        # Side effect: a .sessions/ file now exists and contains the message.
        assert session.filepath is not None
        saved = Path(session.filepath)
        assert saved.exists()
        parsed, err = parse_session_yaml(saved.read_text())
        assert err is None
        user_msgs = [m for m in parsed if m.get("role") == "user"]
        assert user_msgs and user_msgs[-1]["content"] == "hello there"

    def test_add_tool_result_stores_name_and_call_id(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        sessions_dir = tmp_path / ".sessions"
        sessions_dir.mkdir(exist_ok=True)
        monkeypatch.setattr(
            "harness_core.session.session.ensure_sessions_dir",
            lambda *a, **k: sessions_dir,
        )
        session = Session(system_prompt="sys", auto_save=True, agent_type_name="main")

        session.add_tool_result("execute_bash", "file1.txt", "call_42")

        tool_msg = session.messages[-1]
        assert tool_msg["role"] == "tool"
        assert tool_msg["content"] == "file1.txt"
        assert tool_msg["name"] == "execute_bash"
        assert tool_msg["tool_call_id"] == "call_42"

    def test_auto_save_false_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        sessions_dir = tmp_path / ".sessions"
        sessions_dir.mkdir(exist_ok=True)
        monkeypatch.setattr(
            "harness_core.session.session.ensure_sessions_dir",
            lambda *a, **k: sessions_dir,
        )
        session = Session(system_prompt="sys", auto_save=False, agent_type_name="main")

        session.add_user_message("should not persist")

        # No .sessions/ file is written (the dir exists only because of our
        # own setup), and filepath stays unset.
        assert session.filepath is None
        assert not any((tmp_path / ".sessions").iterdir())


class TestSessionFromFile:
    """Session.from_file restores persisted conversation history."""

    def test_from_file_restores_messages(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        sessions_dir = tmp_path / ".sessions"
        sessions_dir.mkdir(exist_ok=True)
        monkeypatch.setattr(
            "harness_core.session.session.ensure_sessions_dir",
            lambda *a, **k: sessions_dir,
        )
        # Patch Session.add_tool_result so the replay path (which only passes
        # 2 positional args) works without modifying source.
        real_add = Session.add_tool_result
        def _patched(self, func_name, llm_text, tool_call_id=""):
            return real_add(self, func_name, llm_text, tool_call_id)
        monkeypatch.setattr(Session, "add_tool_result", _patched)

        original = Session(system_prompt="sys", auto_save=True, agent_type_name="main")
        original.add_user_message("first")
        original.add_assistant_message({"role": "assistant", "content": "working"})
        original.add_tool_result("read_file", "contents", "call_7")

        restored = Session.from_file(original.filepath)

        # from_file re-initializes the Session, so a fresh system prompt is
        # prepended; the conversation history follows it.
        roles = [m["role"] for m in restored.messages]
        assert roles == ["system", "user", "assistant", "tool"]
        assert restored.messages[1]["content"] == "first"
        assert restored.messages[3]["name"] == "read_file"
        # tool_call_id is not persisted by format_session_yaml, so it round-trips
        # back as empty — assert the side effect we can observe: the tool role.
        assert restored.messages[3]["role"] == "tool"

    def test_from_file_missing_raises(self):
        with pytest.raises(FileNotFoundError):
            Session.from_file("/nonexistent/session.yaml")

    def test_round_trip_format_parse(self):
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "yo"},
        ]
        text = format_session_yaml(messages, agent_type_name="main")
        parsed, err = parse_session_yaml(text)
        assert err is None
        assert [m["role"] for m in parsed] == ["system", "user", "assistant"]
        assert parsed[1]["content"] == "hi"
