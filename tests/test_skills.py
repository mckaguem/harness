"""Comprehensive tests for Agent Skills implementation."""

import os
import sys
from pathlib import Path
import tempfile
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSkillsDiscovery:
    """Test Phase 1: Discovery and validation logic."""
    
    def setup_method(self):
        """Create temporary skill directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a valid skill
        self.valid_skill = Path(self.temp_dir) / "test-skill"
        self.valid_skill.mkdir(parents=True, exist_ok=True)
        
        valid_skil_md_content = """---
name: test-skill
description: A valid test skill for unit testing.
license: MIT
metadata:
  version: "1.0"
---

# Test Skill Instructions

This is a minimal instruction set for testing."""
        
        (self.valid_skill / "SKILL.md").write_text(valid_skil_md_content)
        
        # Create an invalid skill (name doesn't match directory)
        self.invalid_skill = Path(self.temp_dir) / "wrong-name"
        self.invalid_skill.mkdir(parents=True, exist_ok=True)
        
        invalid_skil_md_content = """---
name: different-name
description: This should fail validation.
---

# Invalid Skill"""
        
        (self.invalid_skill / "SKILL.md").write_text(invalid_skil_md_content)
    
    def test_discover_valid_skills(self):
        """Test that valid skills are discovered correctly."""
        from skills_discovery import discover_skills
        
        skills = discover_skills(Path(self.temp_dir))
        
        assert len(skills) == 1, f"Expected 1 skill, got {len(skills)}"
        name, metadata = skills[0]
        
        assert name == "test-skill"
        assert metadata['description'] == "A valid test skill for unit testing."
        assert 'body' in metadata
    
    def test_skip_invalid_name_mismatch(self):
        """Test that skills with mismatched names are skipped."""
        from skills_discovery import discover_skills
        
        skills = discover_skills(Path(self.temp_dir))
        
        # Invalid skill should be skipped
        invalid_names = [name for name, _ in skills if name == "different-name"]
        assert len(invalid_names) == 0, "Invalid skill was not skipped"
    
    def test_format_skill_catalog(self):
        """Test catalog formatting for system prompt injection."""
        from skills_discovery import discover_skills, format_skill_catalog
        
        skills = discover_skills(Path(self.temp_dir))
        catalog = format_skill_catalog(skills)
        
        assert "## Available Skills" in catalog
        assert "**test-skill**" in catalog
        assert "A valid test skill for unit testing." in catalog
    
    def test_missing_skil_md(self):
        """Test handling of missing SKILL.md."""
        from skills_discovery import parse_skill_metadata
        
        bad_dir = Path(self.temp_dir) / "no-skil-md"
        bad_dir.mkdir(parents=True, exist_ok=True)
        
        metadata, errors = parse_skill_metadata(bad_dir)
        
        assert len(errors) > 0
        assert any("Missing SKILL.md" in e for e in errors)


class TestActivateSkill:
    """Test Phase 2: Skill activation tool."""
    
    def setup_method(self):
        """Create a temporary skill structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.skills_root = Path(self.temp_dir) / "skills"
        self.skills_root.mkdir(parents=True, exist_ok=True)
        
        # Create a test skill
        skill_dir = self.skills_root / "test-activation"
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        skil_md_content = """---
name: test-activation
description: Skill for testing activation.
---

# Activation Test Instructions

Step 1: Read this file
Step 2: Run the script in scripts/"""
        
        (skill_dir / "SKILL.md").write_text(skil_md_content)
        
        # Change to temp directory so Path.cwd() works correctly
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Restore original working directory."""
        os.chdir(self.original_cwd)
    
    def test_activate_valid_skill(self):
        """Test activating a valid skill."""
        from tools.activate_skill import activate_skill
        
        result_type, result_text = activate_skill("test-activation")
        
        assert result_type == "text", f"Expected 'text', got '{result_type}'"
        assert "SKILL ACTIVATED: test-activation" in result_text
        assert "Step 1:" in result_text
        assert "scripts/" in result_text
    
    def test_activate_nonexistent_skill(self):
        """Test activating a skill that doesn't exist."""
        from tools.activate_skill import activate_skill
        
        result_type, result_text = activate_skill("nonexistent")
        
        assert result_type == "_error_"
        assert "not found" in result_text.lower()


class TestIntegration:
    """End-to-end integration tests."""
    
    def setup_method(self):
        """Create complete skill structure."""
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        
        # Create skills directory
        skills_root = Path.cwd() / "skills"
        skills_root.mkdir(parents=True, exist_ok=True)
        
        # Create a complete skill with scripts and references
        skill_dir = skills_root / "integration-test"
        (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (skill_dir / "references").mkdir(parents=True, exist_ok=True)
        
        skil_md_content = """---
name: integration-test
description: Full integration test skill with scripts and references.
---

# Integration Test Skill

## Instructions

1. Read the reference documentation
2. Run the test script
3. Verify output"""
        
        (skill_dir / "SKILL.md").write_text(skil_md_content)
        
        # Create a test script
        (skill_dir / "scripts" / "run_test.py").write_text(
            "#!/usr/bin/env python3\nprint('Test passed!')\n"
        )
    
    def test_full_workflow(self):
        """Test complete discovery → activation workflow."""
        from skills_discovery import discover_skills, format_skill_catalog
        from tools.activate_skill import activate_skill
        
        # Phase 1: Discovery
        discovered = discover_skills()
        assert len(discovered) == 1, f"Expected 1 skill, found {len(discovered)}"
        
        name, metadata = discovered[0]
        assert name == "integration-test"
        
        # Inject into system prompt (simulating harness.py behavior)
        catalog = format_skill_catalog(discovered)
        assert "**integration-test**" in catalog
        
        # Phase 2: Activation
        result_type, result_text = activate_skill("integration-test")
        assert result_type == "text"
        assert "SKILL ACTIVATED: integration-test" in result_text
        assert str(Path.cwd() / "skills" / "integration-test") in result_text
        
        # Phase 3: Execution context (simulated)
        assert "scripts/run.sh" in result_text or "references/README.md" in result_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
