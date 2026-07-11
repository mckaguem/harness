"""Utility functions for harnessing project management."""

import os
from pathlib import Path
from typing import Optional


def project_root(start_path: Optional[str] = None) -> Path:
    """Detect the project root directory by looking for common project markers.
    
    This function searches upwards from the starting path for common project
    markers (.git directory, pyproject.toml file, .harness_py directory) and
    returns the Path object for the project root.
    
    Args:
        start_path: The starting path for the search. If None, uses the
            current working directory. Can be a string path or a Path object.
    
    Returns:
        Path: The project root directory.
        
    Raises:
        FileNotFoundError: If no project markers can be found after reaching
            the filesystem root.
    
    Examples:
        >>> # From within a module:
        >>> root = project_root()
        >>> # From a specific location:
        >>> root = project_root("/some/path/to/start/from")
    """
    if start_path is None:
        # Use current working directory as default
        start_path = Path.cwd()
    
    # Convert to Path if it's a string
    current = Path(start_path).resolve()
    
    # If it's a file, start from its directory
    if current.is_file():
        current = current.parent
    
    # Common project markers to look for
    markers = ['.git', 'pyproject.toml', '.harness_py']
    
    # Keep moving up until we find a marker or reach root
    original_current = current
    while True:
        # Check for any marker
        for marker in markers:
            marker_path = current / marker
            if marker_path.exists():
                return current
        
        # If we've reached the filesystem root, stop
        if current.parent == current:
            raise FileNotFoundError(
                f"No project markers ({', '.join(markers)}) found "
                f"starting from {original_current}"
            )
        
        # Move up one directory
        current = current.parent


if __name__ == "__main__":
    # Simple test when run directly
    try:
        root = project_root()
        print(f"Project root found: {root}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Current directory: {Path.cwd()}")
        print(f"Markers checked: .git, pyproject.toml, .harness_py")