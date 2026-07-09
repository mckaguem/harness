#!/usr/bin/env python3
"""Update imports for refactoring."""

import re
import sys
from pathlib import Path

def update_file(filepath: Path):
    """Update imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Update skills_discovery imports
    content = re.sub(
        r'from skills_discovery import',
        'from skills.discovery import',
        content
    )
    content = re.sub(
        r'import skills_discovery',
        'from skills import discovery',
        content
    )
    
    # Update skills_interceptor imports
    content = re.sub(
        r'from skills_interceptor import',
        'from skills.interceptor import',
        content
    )
    content = re.sub(
        r'import skills_interceptor',
        'from skills import interceptor',
        content
    )
    
    # Update model_utils imports
    content = re.sub(
        r'from model_utils import',
        'from model.utils import',
        content
    )
    content = re.sub(
        r'import model_utils',
        'from model import utils',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return content

def main():
    """Update all files that need import updates."""
    files_to_update = [
        Path("agent/types.py"),
        Path("harness.py"),
        Path("skills/interceptor.py"),
        Path("tests/test_skills.py"),
        Path("tools/activate_skill.py"),
        Path("agent/loop.py"),
        Path("tests/test_terminal_io.py"),
    ]
    
    for filepath in files_to_update:
        if filepath.exists():
            print(f"Updating {filepath}...")
            update_file(filepath)
        else:
            print(f"Warning: {filepath} not found")
    
    print("\nAll imports updated successfully!")
    
    # Verify updates by checking if old imports still exist
    print("\nChecking for remaining old imports...")
    old_patterns = [
        r'from skills_discovery',
        r'import skills_discovery',
        r'from skills_interceptor',
        r'import skills_interceptor',
        r'from model_utils',
        r'import model_utils',
    ]
    
    for filepath in files_to_update:
        if filepath.exists():
            with open(filepath, 'r') as f:
                content = f.read()
                for pattern in old_patterns:
                    if re.search(pattern, content):
                        print(f"  Warning: {filepath} still contains {pattern}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()