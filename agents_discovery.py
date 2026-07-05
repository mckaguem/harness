"""Agents discovery — scans both config paths for available agent YAML files.

Supports two config paths (analogous to skills discovery):
- **Project path**: ``cwd/.harness_py/agents/``
- **Global path**: ``~/.harness_py/agents/``

When an agent name exists in both paths, the project version wins.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _merge_agent_discoveries(
    discoveries: list[tuple[Path, List[Tuple[str, Path]]]],
) -> list[Tuple[str, Path]]:
    """Merge multiple agent discovery results with precedence.

    Discoveries are processed in order — the first source that provides a
    given name wins. The caller is responsible for ordering sources from
    highest to lowest precedence (e.g. project before global).

    Returns:
        A deduplicated list of ``(agent_name, yaml_path)`` tuples.
    """
    seen: dict[str, Tuple[str, Path]] = {}
    for _source_dir, agents in discoveries:
        for name, path in agents:
            if name not in seen:
                seen[name] = (name, path)
    return list(seen.values())


def discover_agents(
    agents_dirs: Optional[List[Path]] = None,
) -> List[Tuple[str, Path]]:
    """Discover all agent YAML files across the specified directories.

    Args:
        agents_dirs: Ordered list of agent config directory paths to scan.
            The first entry has highest precedence — if an agent name exists
            in multiple directories, its YAML from the earlier directory wins.
            Defaults to ``[cwd/.harness_py/agents, ~/.harness_py/agents]``
            (project first).

    Returns:
        A list of ``(agent_name, yaml_path)`` tuples for valid agent files.
        Invalid or unreadable YAML files are skipped with warnings printed
        to stderr.
    """
    if agents_dirs is None:
        from config import get_harness_py_dir as _get_dirs
        project_dir, global_dir = _get_dirs()
        agents_dirs = [
            project_dir / "agents",
            global_dir / "agents",
        ]

    all_discoveries: list[tuple[Path, List[Tuple[str, Path]]]] = []

    for agents_path in agents_dirs:
        if not agents_path.is_dir():
            print(f"[agents] Warning: Agents directory not found: {agents_path}")
            all_discoveries.append((agents_path, []))
            continue

        valid_agents = []
        for yaml_file in sorted(agents_path.iterdir()):
            if not yaml_file.is_file():
                continue
            # Only pick up .yaml / .yml files at the top level of agents/
            if yaml_file.suffix not in (".yaml", ".yml"):
                continue

            agent_name = yaml_file.stem
            valid_agents.append((agent_name, yaml_file))

        all_discoveries.append((agents_path, valid_agents))

    return _merge_agent_discoveries(all_discoveries)


def get_agent_yaml(agent_name: str, agents_dirs: Optional[List[Path]] = None) -> Tuple[Optional[Path], str]:
    """Look up an agent YAML file by name.

    Searches the directories in order — the first match wins (project before
    global when using defaults).

    Args:
        agent_name: Name of the agent to look up.
        agents_dirs: Ordered list of agent config directory paths to search.

    Returns:
        A tuple of ``(yaml_path, error_message)``. If *error_message* is empty,
        ``yaml_path`` is the resolved Path; otherwise no matching agent was found.
    """
    if agents_dirs is None:
        from config import get_harness_py_dir as _get_dirs
        project_dir, global_dir = _get_dirs()
        agents_dirs = [
            project_dir / "agents",
            global_dir / "agents",
        ]

    for agents_path in agents_dirs:
        yaml_file = agents_path / f"{agent_name}.yaml"
        if not yaml_file.is_file():
            yaml_file = agents_path / f"{agent_name}.yml"
        if yaml_file.is_file():
            return yaml_file, ""

    return None, f"Agent '{agent_name}' not found in any configured path: {agents_dirs}"


def get_agent_yaml_paths() -> List[Path]:
    """Return the absolute paths to all available agents/ directories.

    Useful for injecting into tool descriptions or system prompts so models
    know where to look for agent definitions.
    """
    from config import get_harness_py_dir as _get_dirs
    project_dir, global_dir = _get_dirs()
    return [
        project_dir / "agents",
        global_dir / "agents",
    ]
