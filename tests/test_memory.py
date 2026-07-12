"""Tests for the persistent project memory feature (MEMORY.md).

Offline and fast: these tests use ``tmp_path`` + ``monkeypatch.chdir`` so that
``project_root()`` resolves to a controlled directory, and never touch the real
project MEMORY.md.
"""

import os

import pytest

from harness_core.memory import read_memory, memory_section
from harness_core.tools.update_memory import update_memory
from harness_core.agent.types import AgentType


def _mark_project(tmp_path):
    """Create a project marker so ``project_root()`` resolves to tmp_path."""
    (tmp_path / ".harness_py").mkdir()


def test_read_memory_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no project markers -> project_root falls back to cwd
    assert read_memory() is None


def test_read_memory_returns_content(tmp_path, monkeypatch):
    _mark_project(tmp_path)
    (tmp_path / "MEMORY.md").write_text("remember X\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert read_memory() == "remember X"


def test_memory_section_empty_when_none():
    assert memory_section(None) == ""
    assert memory_section("") == ""


def test_memory_section_builds_block():
    block = memory_section("remember X")
    assert "remember X" in block
    assert "Persistent Project Memory" in block


def test_update_memory_replace_writes_file(tmp_path, monkeypatch):
    _mark_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = update_memory("hello memory", mode="replace")
    assert result.theme != "error"
    content = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
    assert "hello memory" in content


def test_update_memory_append(tmp_path, monkeypatch):
    _mark_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    update_memory("first section", mode="replace")
    update_memory("second section", mode="append")
    content = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
    assert "first section" in content
    assert "second section" in content


def test_update_memory_invalid_mode(tmp_path, monkeypatch):
    _mark_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = update_memory("x", mode="bogus")
    assert result.theme == "error"


def test_system_prompt_includes_memory(tmp_path, monkeypatch):
    _mark_project(tmp_path)
    (tmp_path / "MEMORY.md").write_text("remember X", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    prompt = AgentType._build_system_prompt("base prompt", cwd=tmp_path)
    assert "remember X" in prompt
    assert "Persistent Project Memory" in prompt


def test_update_memory_tool_auto_discovered():
    from harness_core.tools import DISPATCH_REGISTRY
    assert "update_memory" in DISPATCH_REGISTRY
