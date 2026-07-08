"""Tests for agent/discovery.py — agents YAML discovery logic."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agent.discovery import (
    _merge_agent_discoveries,
    discover_agents,
    get_agent_yaml,
    get_agent_yaml_paths,
)


# ── _merge_agent_discoveries ────────────────────────────────────────────


class TestMergeAgentDiscoveries:
    """Tests for `_merge_agent_discoveries()` — precedence-based deduplication."""

    def test_empty_input_returns_empty_list(self):
        result = _merge_agent_discoveries([])
        assert result == []

    def test_single_source_passes_through(self, tmp_path):
        yaml_file = tmp_path / "helper.yaml"
        yaml_file.write_text("name: helper")
        discoveries = [(tmp_path, [("helper", yaml_file)])]
        result = _merge_agent_discoveries(discoveries)
        assert len(result) == 1
        assert result[0] == ("helper", yaml_file)

    def test_duplicate_names_first_wins(self, tmp_path):
        project_dir = tmp_path / "project"
        global_dir = tmp_path / "global"
        project_dir.mkdir()
        global_dir.mkdir()

        proj_yaml = project_dir / "test_agent.yaml"
        proj_yaml.write_text("name: project version")
        glob_yaml = global_dir / "test_agent.yaml"
        glob_yaml.write_text("name: global version")

        discoveries = [
            (project_dir, [("test_agent", proj_yaml)]),
            (global_dir, [("test_agent", glob_yaml)]),
        ]
        result = _merge_agent_discoveries(discoveries)

        assert len(result) == 1
        assert result[0][0] == "test_agent"
        assert result[0][1] == proj_yaml  # project wins

    def test_unique_names_all_kept(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        fa = dir_a / "alpha.yaml"
        fb = dir_b / "beta.yaml"
        fa.write_text("")
        fb.write_text("")

        discoveries = [
            (dir_a, [("alpha", fa)]),
            (dir_b, [("beta", fb)]),
        ]
        result = _merge_agent_discoveries(discoveries)
        assert len(result) == 2
        names = {r[0] for r in result}
        assert names == {"alpha", "beta"}

    def test_second_source_duplicate_filtered(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        fa = dir_a / "dup.yaml"
        fb = dir_b / "dup.yaml"
        fa.write_text("")
        fb.write_text("")

        discoveries = [
            (dir_a, [("dup", fa)]),
            (dir_b, [("dup", fb), ("extra", fb)]),
        ]
        result = _merge_agent_discoveries(discoveries)
        assert len(result) == 2
        # dup should resolve to dir_a's path
        dup_entry = [r for r in result if r[0] == "dup"][0]
        assert dup_entry[1] == fa

    def test_empty_agents_per_source_skipped(self, tmp_path):
        discoveries = [(tmp_path, [])]
        result = _merge_agent_discoveries(discoveries)
        assert result == []


# ── discover_agents ─────────────────────────────────────────────────────


class TestDiscoverAgents:
    """Tests for `discover_agents()` — scanning directories for YAML files."""

    def test_nonexistent_directory_returns_empty(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"
        result = discover_agents(agents_dirs=[nonexistent])
        assert result == []

    def test_discovers_yaml_and_yml_files(self, tmp_path):
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()
        (agent_dir / "helper.yaml").write_text("name: helper")
        (agent_dir / "runner.yml").write_text("name: runner")

        result = discover_agents(agents_dirs=[agent_dir])
        names = {r[0] for r in result}
        assert names == {"helper", "runner"}

    def test_skips_non_yaml_files(self, tmp_path):
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()
        (agent_dir / "notes.txt").write_text("not an agent")
        (agent_dir / "helper.yaml").write_text("name: helper")

        result = discover_agents(agents_dirs=[agent_dir])
        assert len(result) == 1
        assert result[0][0] == "helper"

    def test_skips_subdirectories(self, tmp_path):
        agent_dir = tmp_path / "agents"
        sub = agent_dir / "subdir"
        sub.mkdir(parents=True)
        (agent_dir / "real.yaml").write_text("")
        (sub / "fake.yaml").write_text("")

        result = discover_agents(agents_dirs=[agent_dir])
        assert len(result) == 1
        assert result[0][0] == "real"

    def test_multiple_directories_precedence(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        (dir_a / "agent1.yaml").write_text("")
        (dir_b / "agent1.yaml").write_text("")
        (dir_b / "agent2.yaml").write_text("")

        result = discover_agents(agents_dirs=[dir_a, dir_b])
        assert len(result) == 2
        # agent1 comes from dir_a (first in list)
        a1_path = [r for r in result if r[0] == "agent1"][0][1]
        assert str(a1_path).endswith(str(Path("a") / "agent1.yaml"))

    def test_sorted_within_directory(self, tmp_path):
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()
        (agent_dir / "z_last.yaml").write_text("")
        (agent_dir / "a_first.yaml").write_text("")

        result = discover_agents(agents_dirs=[agent_dir])
        names = [r[0] for r in result]
        assert names == ["a_first", "z_last"]


# ── get_agent_yaml ──────────────────────────────────────────────────────


class TestGetAgentYaml:
    """Tests for `get_agent_yaml()` — name-based lookup."""

    def test_found_in_first_directory(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "helper.yaml").write_text("name: helper")

        path, err = get_agent_yaml("helper", agents_dirs=[dir_a, dir_b])
        assert err == ""
        assert path == dir_a / "helper.yaml"

    def test_falls_back_to_yml(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        (dir_a / "runner.yml").write_text("name: runner")

        path, err = get_agent_yaml("runner", agents_dirs=[dir_a])
        assert err == ""
        assert path == dir_a / "runner.yml"

    def test_missing_agent_returns_none(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        (dir_a / "helper.yaml").write_text("")

        path, err = get_agent_yaml("ghost", agents_dirs=[dir_a])
        assert path is None
        assert "not found" in err.lower()

    def test_not_found_in_any_directory(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        path, err = get_agent_yaml("missing", agents_dirs=[dir_a, dir_b])
        assert path is None
        assert "not found" in err.lower()


# ── get_agent_yaml_paths ────────────────────────────────────────────────


class TestGetAgentYamlPaths:
    """Tests for `get_agent_yaml_paths()` — returns discovery directories."""

    def test_returns_list_of_paths(self, tmp_path):
        with patch("config.get_discovery_dirs") as mock_cfg:
            d1 = tmp_path / "project_agents"
            d2 = tmp_path / "global_agents"
            d1.mkdir()
            d2.mkdir()
            mock_cfg.return_value = [d1, d2]

            paths = get_agent_yaml_paths()
            assert paths == [d1, d2]

    def test_calls_config_once(self):
        with patch("config.get_discovery_dirs") as mock_cfg:
            mock_cfg.return_value = []
            get_agent_yaml_paths()
            get_agent_yaml_paths()
            # Each call should invoke the config lookup.
            assert mock_cfg.call_count == 2
