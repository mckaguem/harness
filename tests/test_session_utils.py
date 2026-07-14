"""Tests for harness_core.session.session_utils helpers."""

import pytest

from harness_core.session.session_utils import (
    format_session_yaml,
    parse_session_yaml,
    create_run_folder,
    ensure_sessions_dir,
)


class TestSessionYamlRoundTrip:
    """format_session_yaml <-> parse_session_yaml round-trip."""

    def test_round_trip_preserves_messages(self):
        messages = [
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "tool", "content": "result", "name": "read_file", "tool_call_id": "c1"},
        ]
        text = format_session_yaml(messages, agent_type_name="main")
        parsed, err = parse_session_yaml(text)
        assert err is None
        assert [m["role"] for m in parsed] == ["system", "user", "assistant", "tool"]
        assert parsed[1]["content"] == "hello"
        assert parsed[3]["content"] == "result"
        assert parsed[3]["name"] == "read_file"

    def test_parse_invalid_yaml_returns_error(self):
        parsed, err = parse_session_yaml("::: not valid yaml :::\n  - [")
        # Either empty messages or an error string — never raise.
        assert err is None or isinstance(err, str)

    def test_reasoning_round_trips(self):
        messages = [
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there", "reasoning": "I thought about it.\nStep two."},
        ]
        text = format_session_yaml(messages, agent_type_name="main")
        parsed, err = parse_session_yaml(text)
        assert err is None
        assistant = [m for m in parsed if m.get("role") == "assistant"][0]
        assert assistant["content"] == "hi there"
        assert assistant.get("reasoning") == "I thought about it.\nStep two."


class TestRunFolder:
    """create_run_folder / ensure_sessions_dir filesystem side effects."""

    def test_create_run_folder_creates_and_registers(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # create_run_folder relies on project_root(); patch it to the temp dir.
        monkeypatch.setattr(
            "harness_core.session.session_utils.project_root",
            lambda *a, **k: tmp_path,
        )
        from harness_core.session.session_utils import (
            set_current_run_folder,
            get_current_run_folder,
        )
        set_current_run_folder(None)

        folder = create_run_folder()

        assert folder.is_dir()
        assert str(tmp_path) in [str(p) for p in folder.parents]
        # The newly created folder is the active run folder.
        assert get_current_run_folder() == folder
        set_current_run_folder(None)

    def test_ensure_sessions_dir_creates_dot_sessions(self, tmp_path):
        sessions_dir = ensure_sessions_dir(base_path=str(tmp_path))
        assert sessions_dir == tmp_path / ".sessions"
        assert sessions_dir.is_dir()
