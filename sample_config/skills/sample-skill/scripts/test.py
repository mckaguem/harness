#!/usr/bin/env python3
"""Test script for the sample skill."""

import sys
from pathlib import Path


def main():
    """Verify the sample skill structure is intact."""
    skill_root = Path(__file__).resolve().parent.parent
    
    print(f"✓ Skill root: {skill_root}")
    
    # Check SKILL.md exists
    skill_md = skill_root / "SKILL.md"
    if skill_md.exists():
        print(f"✓ SKILL.md found ({skill_md.stat().st_size} bytes)")
    else:
        print("✗ SKILL.md missing!")
        sys.exit(1)
    
    # Check scripts directory
    scripts_dir = skill_root / "scripts"
    if scripts_dir.is_dir():
        script_count = len(list(scripts_dir.glob("*.py")))
        print(f"✓ scripts/ contains {script_count} Python files")
    else:
        print("✗ scripts/ directory missing!")
    
    # Check references directory
    refs_dir = skill_root / "references"
    if refs_dir.is_dir():
        ref_count = len(list(refs_dir.iterdir()))
        print(f"✓ references/ contains {ref_count} files")
    else:
        print("✗ references/ directory missing!")
    
    print("\n✅ Sample skill validation complete!")


if __name__ == "__main__":
    main()
