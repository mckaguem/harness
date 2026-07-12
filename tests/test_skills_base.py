"""Tests for harness_core.skills.base — Skill / YamlSkill basics."""

import pytest

from harness_core.skills.base import Skill, YamlSkill


class TestSkillBasics:
    """Skill is an abstract base; YamlSkill loads scripts + activates."""

    def test_yaml_skill_loads_metadata(self):
        skill = YamlSkill("demo", {"description": "does a demo", "scripts": {"main": "/x/run.py"}})
        assert skill.name == "demo"
        assert skill.description == "does a demo"
        assert skill.scripts == {"main": "/x/run.py"}
        # No instructions defined by default.
        assert skill.get_instructions() is None

    def test_yaml_skill_activate_missing_script_returns_error(self):
        skill = YamlSkill("demo", {"description": "d", "scripts": {}})
        outcome = skill.activate(script_name="main")
        assert outcome["success"] is False
        assert "not found" in outcome["error"]

    def test_abstract_skill_cannot_instantiate(self):
        # Skill is abstract (activate is abstractmethod), so it can't be built directly.
        with pytest.raises(TypeError):
            Skill("x", "y")

    def test_yaml_skill_activate_runs_script(self, tmp_path):
        # Create a trivial script that prints JSON so activate() can parse stdout.
        script = tmp_path / "run.py"
        script.write_text("import json,sys\nprint(json.dumps({'ok': True}))\n")
        skill = YamlSkill("demo", {"description": "d", "scripts": {"main": str(script)}})
        outcome = skill.activate(script_name="main")
        assert outcome["success"] is True
        assert outcome["output"] == {"ok": True}
