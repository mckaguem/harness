"""Tools subpackage — self-discovering skills.

A file is treated as a "skill" if it defines function_def at the top level.
This module scans the package directory for such files, builds the agent tool
schema from each one's function_def, and maintains a dispatcher registry
mapping tool names to their callables.
"""

import importlib.util
from pathlib import Path


def _discover_skills():
    """Scan this package's directory for skills — i.e. modules with function_def."""
    tools_dir = Path(__file__).parent
    schema = []
    registry = {}
    summary_registry = {}

    skip = {"__init__.py", "utils.py", "dispatcher.py"}

    for path in sorted(tools_dir.glob("*.py")):
        if path.name in skip or path == Path(__file__).parent / "__init__.py":
            continue

        try:
            spec = importlib.util.spec_from_file_location(
                f"tools.{path.stem}", path
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        except Exception as e:
            print(f"[tools] warning: failed to load skill {path.name}: {e}")
            continue

        function_def = getattr(mod, "function_def", None)
        if not isinstance(function_def, dict):
            continue  # not a skill — no function_def at the module level.

        name = function_def["function"]["name"]
        schema.append(function_def)
        registry[name] = mod

        summary_fn = getattr(mod, "summary", None)
        if callable(summary_fn):
            summary_registry[name] = summary_fn

    return schema, registry, summary_registry


AGENT_TOOLS: list[dict] = []
DISPATCH_REGISTRY: dict[str, callable] = {}
SUMMARY_REGISTRY: dict[str, callable] = {}


def _build() -> None:
    """Re-discover skills and populate AGENT_TOOLS / DISPATCH_REGISTRY / SUMMARY_REGISTRY."""
    global AGENT_TOOLS, DISPATCH_REGISTRY, SUMMARY_REGISTRY

    schema, registry, summary_registry = _discover_skills()
    AGENT_TOOLS = schema  # type: ignore[assignment]
    DISPATCH_REGISTRY = registry  # type: ignore[assignment]
    SUMMARY_REGISTRY = summary_registry  # type: ignore[assignment]


_build()