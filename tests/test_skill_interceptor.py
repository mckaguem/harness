"""Tests for harness_core.skills.interceptor — slash-command routing."""

import pytest

from harness_core.skills.interceptor import (
    intercept_message,
    InterceptorKind,
    InterceptorOutcome,
    matches_slash_pattern,
    extract_command_name,
)


class TestInterceptorBehavior:
    """intercept_message routes slash commands per InterceptorKind."""

    def test_non_slash_input_is_skipped(self):
        out = intercept_message("just some text")
        assert out.kind == InterceptorKind.SKIP
        assert out.payload is None

    def test_unknown_command_falls_through(self, tmp_path):
        # A skills_dir with no matching skill -> UNKNOWN (forwarded to LLM).
        (tmp_path / "other").mkdir()
        out = intercept_message("/nonexistent-cmd", skills_dir=tmp_path)
        assert out.kind == InterceptorKind.UNKNOWN

    def test_known_skill_gets_activated(self, tmp_path):
        # Build a minimal skill directory with a SKILL.md body.
        skill_dir = tmp_path / "demo"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\nuser-invocable: true\n---\nDo the demo thing.\n"
        )
        out = intercept_message("/demo", skills_dir=tmp_path)
        assert out.kind == InterceptorKind.ACTIVATED
        assert out.payload is not None and "demo" in out.payload
        assert out.stripped_message == ""

    def test_stripped_message_returns_remainder(self, tmp_path):
        skill_dir = tmp_path / "demo"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo skill\nuser-invocable: true\n---\nbody\n"
        )
        out = intercept_message("/demo please do X", skills_dir=tmp_path)
        assert out.kind == InterceptorKind.ACTIVATED
        assert out.stripped_message == "please do X"

    def test_restricted_skill_is_not_activated(self, tmp_path):
        skill_dir = tmp_path / "internal"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: internal\ndescription: internal skill\nuser-invocable: false\n---\nsecret\n"
        )
        out = intercept_message("/internal", skills_dir=tmp_path)
        assert out.kind == InterceptorKind.RESTRICTED
        assert out.payload is not None


class TestInterceptorHelpers:
    """Convenience regex helpers."""

    def test_matches_slash_pattern(self):
        assert matches_slash_pattern("/demo")
        assert not matches_slash_pattern("no slash")

    def test_extract_command_name(self):
        assert extract_command_name("/demo") == "demo"
        assert extract_command_name("plain") is None
