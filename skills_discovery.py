"""Skills discovery module — scans for and validates agent skills."""

import re
from pathlib import Path
from typing import Dict, List, Tuple
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
    
    # Store the body for later use by activate_skill
    if metadata.get('body') is None and 'body' not in str(metadata):
        try:
            end_idx = content.find('---', 3)
            if end_idx != -1:
                body_start = end_idx + 3
                # Skip the delimiter line itself
                while body_start < len(content) and content[body_start] in '\n\r':
                    body_start += 1
                metadata['body'] = content[body_start:].strip()
        except Exception:
            pass
    
    return metadata, errors


def discover_skills(skills_dir: Path = None) -> List[Tuple[str, Dict]]:
    """Discover and validate all skills in the specified directory.
    
    Args:
        skills_dir: Path to skills directory. Defaults to 'skills/' relative to CWD.
        
    Returns:
        A list of (skill_name, metadata) tuples for valid skills. Invalid skills 
        are skipped with warnings printed to stderr.
    """
    if skills_dir is None:
        skills_dir = Path.cwd() / "skills"
    
    if not skills_dir.is_dir():
        print(f"[skills] Warning: Skills directory not found: {skills_dir}")
        return []
    
    valid_skills = []
    
    for skill_path in sorted(skills_dir.iterdir()):
        if not skill_path.is_dir() or skill_path.name.startswith('.'):
            continue
        
        metadata, errors = parse_skill_metadata(skill_path)
        
        if errors:
            print(f"[skills] Skipping invalid skill '{skill_path.name}':")
            for error in errors:
                print(f"  - {error}")
            continue
        
        valid_skills.append((metadata['name'], metadata))
    
    return valid_skills


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


def get_skill_body(skill_name: str, skills_dir: Path = None) -> Tuple[str, str]:
    """Get the body content of a specific skill's SKILL.md file.
    
    Args:
        skill_name: Name of the skill to activate
        skills_dir: Path to skills directory. Defaults to 'skills/' relative to CWD.
        
    Returns:
        A tuple of (body_content, error_message). If error_message is non-empty, 
        activation failed.
    """
    if skills_dir is None:
        skills_dir = Path.cwd() / "skills"
    
    skill_path = skills_dir / skill_name
    
    if not skill_path.is_dir():
        return "", f"Skill directory '{skill_name}' not found at {skill_path}"
    
    metadata, errors = parse_skill_metadata(skill_path)
    
    if errors:
        error_msg = "; ".join(errors)
        return "", f"Failed to validate skill '{skill_name}': {error_msg}"
    
    body = metadata.get('body', '')
    return body, ""
