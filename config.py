"""Configuration resolution — project and global .harness_py paths."""

import os
from pathlib import Path

# Import project_root from utils
from utils import project_root
import yaml
from model.types import ProviderConfig, ModelConfig

# ---------------------------------------------------------------------------
# Centralized constants for the harness codebase.
# ---------------------------------------------------------------------------

#: Valid task lifecycle statuses (must remain immutable).
VALID_TASK_STATUSES = ("pending", "in_progress", "completed", "failed")

#: Default model context length used when runtime detection is unavailable.
DEFAULT_CONTEXT_LENGTH = 8192

#: Subdirectories within .harness_py for component discovery.
_SKILLS_DIR = "skills"
_AGENTS_DIR = "agents"


def get_project_dir() -> Path:
    """Return the project config directory ``project_root/.harness_py/``."""
    # Find the project root directory using common markers
    root = project_root()
    return (root / ".harness_py").resolve()


def get_global_dir() -> Path:
    """Return the global config directory, defaulting to ``~/.harness_py/``.

    Override with the ``HARNESS_PY_HOME`` environment variable.
    """
    override = os.environ.get("HARNESS_PY_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".harness_py"


def get_harness_py_dir() -> tuple[Path, Path]:
    """Return both harness_py directories as a ``(project_dir, global_dir)`` tuple.

    Both are :class:`Path` objects with ``agents/`` and ``skills/`` subdirectories
    available inside them. Project dir takes precedence over global when
    discovering skills and agents with the same name.
    """
    return get_project_dir(), get_global_dir()


def get_discovery_dirs(subdir: str) -> list[Path]:
    """Return ordered discovery directories for a given component (skills/agents).

    This helper centralizes the repeated pattern of resolving both project and
    global .harness_py subdirectories in one call, ensuring consistent ordering
    (project first) across all discovery modules.

    Args:
        subdir: The subdirectory name within ``.harness_py/`` to discover
            (e.g. ``"skills"`` or ``"agents"``).

    Returns:
        An ordered list of :class:`Path` objects — project first, then global.
    """
    project_dir, global_dir = get_harness_py_dir()
    return [project_dir / subdir, global_dir / subdir]

# ---------------------------------------------------------------------------
# Configuration file handling for providers and models.
# ---------------------------------------------------------------------------

CONFIG_FILENAME = "config.yaml"

def _load_yaml_file(path: Path) -> dict:
    """Load a YAML file if it exists, returning an empty dict otherwise."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        raise RuntimeError(f"Failed to parse config file {path}: {e}")

def _merge_providers(global_provs: list[dict], project_provs: list[dict]) -> list[ProviderConfig]:
    """Merge provider lists, preferring project definitions on name conflict.

    Returns a list of ProviderConfig dataclass instances.
    """
    merged: dict[str, ProviderConfig] = {}
    for prov in global_provs:
        if not isinstance(prov, dict) or "name" not in prov:
            continue
        name = prov["name"]
        merged[name] = ProviderConfig(
            provider_type=prov.get("type", ""),
            base_url=prov.get("base_url", ""),
            api_key=prov.get("api_key"),
            default_model=prov.get("default_model"),
        )
    for prov in project_provs:
        if not isinstance(prov, dict) or "name" not in prov:
            continue
        name = prov["name"]
        merged[name] = ProviderConfig(
            provider_type=prov.get("type", ""),
            base_url=prov.get("base_url", ""),
            api_key=prov.get("api_key"),
            default_model=prov.get("default_model"),
        )
    return list(merged.values())

# ---------------------------------------------------------------------------
# Module-level configuration cache — loaded once on first access.
# ---------------------------------------------------------------------------

_config_cache: dict | None = None


def _reset_config_cache() -> None:
    """Clear the module-level config cache. Primarily for testing."""
    global _config_cache
    _config_cache = None


def _get_cached_config() -> dict:
    """Return cached configuration, loading it lazily on first call."""
    global _config_cache
    if _config_cache is None:
        _config_cache = load_harness_config()
    return _config_cache


def load_harness_config() -> dict:
    """Load and merge configuration from global and project ``config.yaml`` files.

    Returns a dictionary with keys:
    - "providers": List[ProviderConfig]
    - "default_provider": Optional[str]
    - "default_model": Optional[str]
    """
    project_dir, global_dir = get_harness_py_dir()
    global_cfg_path = global_dir / CONFIG_FILENAME
    project_cfg_path = project_dir / CONFIG_FILENAME

    global_cfg = _load_yaml_file(global_cfg_path)
    project_cfg = _load_yaml_file(project_cfg_path)

    providers = _merge_providers(
        global_cfg.get("providers", []),
        project_cfg.get("providers", []),
    )

    default_provider = project_cfg.get("default_provider") or global_cfg.get("default_provider")
    default_model = project_cfg.get("default_model") or global_cfg.get("default_model")

    return {
        "providers": providers,
        "default_provider": default_provider,
        "default_model": default_model,
    }

def get_provider_config(name: str) -> ProviderConfig | None:
    """Retrieve a ProviderConfig by its identifier name.

    Matches against the provider's ``provider_type`` or ``base_url``.
    Returns ``None`` if not found.
    """
    cfg = _get_cached_config()
    for prov in cfg["providers"]:
        if prov.provider_type == name or prov.base_url == name:
            return prov
    return None

def get_default_provider() -> ProviderConfig | None:
    """Return the default provider configuration, if specified."""
    cfg = _get_cached_config()
    name = cfg.get("default_provider")
    if not name:
        return None
    for prov in cfg["providers"]:
        if prov.provider_type == name or prov.base_url == name:
            return prov
    return None

def get_default_model() -> str | None:
    """Return the default model name, if specified."""
    cfg = _get_cached_config()
    return cfg.get("default_model")

# Exported symbols.
__all__ = [
    "get_project_dir",
    "get_global_dir",
    "get_harness_py_dir",
    "get_discovery_dirs",
    "load_harness_config",
    "get_provider_config",
    "get_default_provider",
    "get_default_model",
]

