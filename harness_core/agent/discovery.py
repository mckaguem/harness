"""Agents discovery — scans both config paths for available agent YAML files.

Supports two config paths (analogous to skills discovery):
- **Project path**: ``cwd/.harness_py/agents/``
- **Global path**: ``~/.harness_py/agents/``

When an agent name exists in both paths, the project version wins.
"""

import logging
from pathlib import Path
from typing import Tuple

from harness_core.terminal_io import print_system

logger = logging.getLogger(__name__)

# Module-level cache so the (expensive) filesystem scan runs only once per
# unique set of discovery directories.
_AGENT_DISCOVERY_CACHE: dict[tuple, list] = {}


def _merge_agent_discoveries(
    discoveries: list[tuple[Path, list[Tuple[str, Path]]]],
) -> list[Tuple[str, Path]]:
    """Merge multiple agent discovery results with precedence.

    Discoveries are processed in order — the first source that provides a
    given name wins. The caller is responsible for ordering sources from
    highest to lowest precedence (e.g. project before global).

    Returns:
        A deduplicated list of ``(agent_name, yaml_path)`` tuples.
    """
    seen: set[str] = set()
    result: list[Tuple[str, Path]] = []
    for _source_dir, agents in discoveries:
        for name, path in agents:
            if name not in seen:
                seen.add(name)
                result.append((name, path))
    return result


def discover_agents(
    agents_dirs: list[Path] | None = None,
) -> list[Tuple[str, Path]]:
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
        from harness_core.config import get_discovery_dirs
        agents_dirs = get_discovery_dirs("agents")

    cache_key = tuple(str(p) for p in agents_dirs)
    merged = _AGENT_DISCOVERY_CACHE.get(cache_key)
    if merged is None:
        all_discoveries: list[tuple[Path, list[Tuple[str, Path]]]] = []
        missing_dirs: list[Path] = []

        for agents_path in agents_dirs:
            if not agents_path.is_dir():
                missing_dirs.append(agents_path)
                all_discoveries.append((agents_path, []))
                continue

            valid_agents = []
            for yaml_file in sorted(agents_path.iterdir()):
                if not yaml_file.is_file():
                    continue
                # Only pick up .yaml / .yml files at the top level of agents/
                if yaml_file.suffix not in (".yaml", ".yml"):
                    continue

                # Safety guard: ensure the resolved path stays within agents_path.
                # This prevents directory-traversal tricks via symlinks or ".."
                # entries that could expose arbitrary files outside the intended
                # agents directory.
                try:
                    yaml_file.resolve().is_relative_to(agents_path.resolve())
                except OSError:
                    continue

                agent_name = yaml_file.stem

                # Sanitize agent_name: reject names containing path separators
                # or starting with a dash (which could be confused with CLI
                # flags when used as identifiers).
                if "/" in agent_name or "\\" in agent_name or agent_name.startswith("-"):
                    continue

                valid_agents.append((agent_name, yaml_file))

            all_discoveries.append((agents_path, valid_agents))

        # Only warn when NONE of the configured agents directories exist — a single
        # missing directory is expected (e.g. project has agents but global doesn't).
        if missing_dirs and len(missing_dirs) == len(agents_dirs):
            print_system(
                "Agents",
                "Agents directory not found in any configured path: "
                + ", ".join(str(p) for p in missing_dirs),
            )

        merged = _merge_agent_discoveries(all_discoveries)
        _AGENT_DISCOVERY_CACHE[cache_key] = merged

    return merged


def get_agent_yaml(agent_name: str, agents_dirs: list[Path] | None = None) -> Tuple[Path | None, str]:
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
        from harness_core.config import get_discovery_dirs
        agents_dirs = get_discovery_dirs("agents")

    for agents_path in agents_dirs:
        yaml_file = agents_path / f"{agent_name}.yaml"
        if not yaml_file.is_file():
            yaml_file = agents_path / f"{agent_name}.yml"
        if yaml_file.is_file():
            return yaml_file, ""

    dir_names = ", ".join(sorted({p.name for p in agents_dirs}))
    return None, f"Agent '{agent_name}' not found in any configured path: {dir_names}"


def get_agent_yaml_paths() -> list[Path]:
    """Return the absolute paths to all available agents/ directories.

    Useful for injecting into tool descriptions or system prompts so models
    know where to look for agent definitions.
    """
    from harness_core.config import get_discovery_dirs
    return get_discovery_dirs("agents")
