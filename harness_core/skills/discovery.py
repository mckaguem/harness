"""Skills discovery module — scans for and validates agent skills.

Supports two config paths:
- **Project path**: ``cwd/.harness_py/skills/``
- **Global path**: ``~/.harness_py/skills/`` (overridable via ``HARNESS_PY_HOME``)

When a skill name exists in both paths, the project version wins.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml


def parse_skill_metadata(skill_dir: Path) -> Tuple[Dict, List[str]]:
    """Parse a skill directory's SKILL.md file and validate metadata.

    Args:
        skill_dir: Path to the skill directory containing SKILL.md

    Returns:
        A tuple of (metadata_dict, errors_list). If errors is non-empty,
        the skill should be skipped.
    """
    errors = []
    metadata = {}

    skill_md_path = skill_dir / "SKILL.md"

    if not skill_md_path.is_file():
        return {}, [f"Missing SKILL.md in {skill_dir}"]

    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {}, [f"Failed to read SKILL.md: {e}"]

    # Extract YAML frontmatter
    if not content.startswith('---'):
        return {}, ["SKILL.md missing YAML frontmatter delimiter (---)"]

    try:
        # Find the end of frontmatter
        end_idx = content.find('---', 3)
        if end_idx == -1:
            return {}, ["SKILL.md missing closing frontmatter delimiter (---)"]

        yaml_content = content[3:end_idx].strip()
        body = content[end_idx + 3:].strip()

        # Parse YAML
        try:
            metadata = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            return {}, [f"Invalid YAML in frontmatter: {e}"]

    except Exception as e:
        return {}, [f"Error parsing SKILL.md: {e}"]

    # Store the body in metadata so callers (e.g. skills_interceptor) can find it.
    metadata['body'] = body

    # Validate name field
    if 'name' not in metadata:
        errors.append("Missing required 'name' field")
    else:
        name = metadata['name']
        if not isinstance(name, str):
            errors.append("'name' must be a string")
        elif len(name) < 1 or len(name) > 64:
            errors.append(f"'name' must be 1-64 characters (got {len(name)})")
        elif not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            errors.append("'name' must contain only lowercase alphanumeric chars and hyphens, cannot start/end with hyphen")
        else:
            # Check if name matches directory name
            dir_name = skill_dir.name
            if name != dir_name:
                errors.append(f"'name' ({name!r}) does not match parent directory name ({dir_name!r})")

    # Validate description field
    if 'description' not in metadata:
        errors.append("Missing required 'description' field")
    else:
        desc = metadata['description']
        if not isinstance(desc, str):
            errors.append("'description' must be a string")
        elif len(desc) < 1 or len(desc) > 1024:
            errors.append(f"'description' must be 1-1024 characters (got {len(desc)})")

    return metadata, errors


def _merge_skill_discoveries(
    discoveries: list[tuple[Path, List[Tuple[str, Dict]]]],
) -> list[Tuple[str, Dict]]:
    """Merge multiple skill discovery results with precedence.

    Discoveries are processed in order — the first source that provides a
    given name wins. This means earlier entries in *discoveries* have higher
    priority than later ones. The caller is responsible for ordering sources
    from highest to lowest precedence (e.g. project before global).

    Returns:
        A deduplicated list of ``(skill_name, metadata)`` tuples.
    """
    seen: set[str] = set()
    result: list[Tuple[str, Dict]] = []
    for _source_dir, skills in discoveries:
        for name, meta in skills:
            if name not in seen:
                seen.add(name)
                result.append((name, meta))
    return result


def discover_skills(
    skills_dirs: Optional[List[Path]] = None,
    command_names: Optional[set] = None,
) -> List[Tuple[str, Dict]]:
    """Discover and validate all skills across the specified directories.

    Args:
        skills_dirs: Ordered list of skill directory paths to scan. The first
            entry has highest precedence — if a skill name exists in multiple
            directories, its metadata from the earlier directory wins.
            Defaults to ``[cwd/.harness_py/skills, ~/.harness_py/skills]``
            (project first).
        command_names: Optional set of command names to check for collisions.
            If provided and any skill names match command names, raises
            RuntimeError with collision details.

    Returns:
        A list of ``(skill_name, metadata)`` tuples for valid skills. Invalid
        skills are skipped with warnings printed to stderr.

    Raises:
        RuntimeError: If command_names is provided and there are name collisions
                      between commands and skills.
    """
    if skills_dirs is None:
        from harness_core.config import get_discovery_dirs
        skills_dirs = get_discovery_dirs("skills")

    all_discoveries: list[tuple[Path, List[Tuple[str, Dict]]]] = []

    for skills_path in skills_dirs:
        if not skills_path.is_dir():
            print(f"[skills] Warning: Skills directory not found: {skills_path}")
            all_discoveries.append([skills_path, []])  # empty list for missing dir
            continue

        valid_skills = []
        for skill_path in sorted(skills_path.iterdir()):
            if not skill_path.is_dir() or skill_path.name.startswith("."):
                continue

            metadata, errors = parse_skill_metadata(skill_path)

            if errors:
                print(f"[skills] Skipping invalid skill '{skill_path.name}':")
                for error in errors:
                    print(f"  - {error}")
                continue

            valid_skills.append((metadata["name"], metadata))

        all_discoveries.append([skills_path, valid_skills])

    merged = _merge_skill_discoveries(all_discoveries)
    
    # Check for command/skill collisions if command_names provided
    if command_names is not None:
        skill_names = {name for name, _ in merged}
        collisions = command_names & skill_names
        
        if collisions:
            collision_messages = []
            for name in sorted(collisions):
                collision_messages.append(
                    f"Command '/{name}' and skill '{name}' both exist. "
                    f"Cannot reliably route — aborting startup."
                )
            raise RuntimeError(
                "\n[skills] FATAL: Command/skill collision detected. Aborting startup.\n" +
                "  - " + "\n  - ".join(collision_messages)
            )
    
    return merged


def format_skill_catalog(skills: List[Tuple[str, Dict]]) -> str:
    """Format a list of skills into a concise catalog for system prompt injection.

    Args:
        skills: List of (skill_name, metadata) tuples from discover_skills()

    Returns:
        A formatted string suitable for inclusion in the agent's system prompt.
    """
    if not skills:
        return ""

    lines = ["\n## Available Skills\n"]

    for name, meta in skills:
        desc = meta.get('description', 'No description provided')
        # Truncate very long descriptions
        if len(desc) > 200:
            desc = desc[:197] + "..."
        lines.append(f"- **{name}**: {desc}")

    return "\n".join(lines)


def get_skill_by_name(skill_name: str, skills_dirs: Optional[List[Path]] = None) -> Tuple[Dict[str, object], str]:
    """Look up a skill by name and return its parsed metadata.

    Searches the directories in order — the first match wins (project before
    global when using defaults).

    Args:
        skill_name: Name of the skill to look up.
        skills_dirs: Ordered list of skill directory paths to search. Defaults
            to ``[cwd/.harness_py/skills, ~/.harness_py/skills]``.

    Returns:
        A tuple of (metadata_dict, error_message). If *error_message* is non-empty,
        no matching skill was found or validation failed.
    """
    if skills_dirs is None:
        from harness_core.config import get_discovery_dirs
        skills_dirs = get_discovery_dirs("skills")

    for skills_path in skills_dirs:
        skill_path = skills_path / skill_name
        if not skill_path.is_dir():
            continue

        metadata, errors = parse_skill_metadata(skill_path)
        if not errors:
            return metadata, ""

    return {}, f"Skill '{skill_name}' not found in any configured path"


def get_skill_body(skill_name: str, skills_dirs: Optional[List[Path]] = None) -> Tuple[str, str]:
    """Get the body content of a specific skill's SKILL.md file.

    Args:
        skill_name: Name of the skill to activate.
        skills_dirs: Ordered list of skill directory paths to search. Defaults
            to ``[cwd/.harness_py/skills, ~/.harness_py/skills]``.

    Returns:
        A tuple of (body_content, error_message). If *error_message* is non-empty,
        activation failed.
    """
    if skills_dirs is None:
        from harness_core.config import get_discovery_dirs
        skills_dirs = get_discovery_dirs("skills")

    for skills_path in skills_dirs:
        skill_path = skills_path / skill_name
        if not skill_path.is_dir():
            continue

        metadata, errors = parse_skill_metadata(skill_path)
        if not errors:
            body = metadata.get('body', '')
            return body, ""

    return "", f"Skill '{skill_name}' not found in any configured path"


def check_command_skill_collision(command_names: set) -> list:
    """Check for name collisions between provided command names and discovered skills.
    
    Args:
        command_names: Set of command names to check against discovered skills
        
    Returns:
        List of collision message strings (empty if no collisions)
    """
    # Discover all valid skills
    discovered_skills = discover_skills()
    skill_names = {name for name, _ in discovered_skills}
    
    # Find intersection - names that exist in both sets
    collisions = command_names & skill_names
    
    # Generate collision messages
    messages = []
    for name in sorted(collisions):
        messages.append(
            f"Command '/{name}' and skill '{name}' both exist. "
            f"Cannot reliably route — aborting startup."
        )
    return messages

__all__ = [
    "discover_skills",
    "get_skill_by_name",
    "get_skill_body",
    "format_skill_catalog",
    "check_command_skill_collision",
]
