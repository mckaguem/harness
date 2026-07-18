"""Agent type definition — model, tools, and system prompt configuration."""

from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Dict


from harness_core.model.types import ProviderConfig
from harness_core.utils import project_root
from harness_core.memory import read_memory, memory_section

import yaml

# Built-in variable names recognised in system prompt templates.
_SYSTEM_VARIABLES = {"CWD", "SKILLS", "AGENTS", "TOOLS"}


@dataclass
class AgentType:
    """Definition of an agent — its model, tools, and system prompt."""

    name: str = ""
    model_name: str = ""
    provider_model_name: str = ""
    context_length: int = 4096
    system_prompt: str = ""
    provider_config: ProviderConfig | None = None
    agent_tools: list[str] = field(default_factory=list)
    temperature: float | None = None           # NEW — sampling temperature, optional
    top_p: float | None = None                 # NEW — nucleus sampling parameter, optional
    max_tokens: int | None = None              # NEW — alias for max_output_tokens in config.yaml, optional (display/introspection)
    reasoning_effort: str | None = None        # NEW — "none"/"minimal"/"low"/"medium"/"high"/"xhigh"/"max", optional

    @staticmethod
    def _substitute_variables(
        system_prompt: str,
        cwd: Path,
        skills: list[tuple] | None = None,
        agents: list[Dict] | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        """Substitute template variables of the form ``${VAR_NAME}`` in *system_prompt*.

        The supported variable names are:

        +-----------+-------------------------------------------------------+
        | Variable  | Value                                                 |
        +===========+=======================================================+
        | ``CWD``   | Absolute path of the project root (detected via project markers). |
        +-----------+-------------------------------------------------------+
        | ``SKILLS``| One line per discovered skill (name: description),    |
        |           | joined by newlines. Empty string if none discovered.  |
        +-----------+-------------------------------------------------------+
        | ``AGENTS``| One line per available agent (name: description),     |
        |           | joined by newlines. Empty string if none discovered.  |
        +-----------+-------------------------------------------------------+
        | ``TOOLS`` | One line per available tool (tool name and short      |
        |           | description from its function_def), joined by         |
        |           | newlines. Empty string if none provided.              |
        +-----------+-------------------------------------------------------+

        Unsupported variable names are left intact so typos surface as literal
        ``${UNLIKELY_NAME}`` placeholders rather than silently disappearing.

        Args:
            system_prompt: The raw prompt text sourced from the agent YAML.
            cwd: The project root directory to insert for ``$CWD``.
            skills: Optional list of ``(name, metadata)`` tuples (from
                :func:`skills_discovery.discover_skills`).
            agents: Optional list of dicts describing available agents,
                each with at least ``name`` and ``description`` keys.
            tools: Optional list of tool schema dicts. Each entry should have
                a ``function.description`` key; if missing, the bare function
                name is used.

        Returns:
            The prompt text with all recognised variables substituted.
        """

        def _replace(match):
            var_name = match.group(1) or match.group(2)
            if not var_name:
                return match.group(0)
            if var_name not in _SYSTEM_VARIABLES:
                # Leave unknown placeholders untouched so typos are visible.
                return match.group(0)

            if var_name == "CWD":
                return str(cwd.resolve())

            if var_name == "SKILLS":
                if not skills:
                    return ""
                lines = []
                for name, meta in skills:
                    desc = (meta.get("description") or "No description provided").strip()
                    # Truncate very long descriptions so the prompt stays compact.
                    if len(desc) > 200:
                        desc = desc[:197] + "..."
                    lines.append(f"- {name}: {desc}")
                return "\n".join(lines)

            if var_name == "AGENTS":
                if not agents:
                    return ""
                return "\n".join(
                    f"- {a.get('name', '<unknown>')}: {a.get('description', 'No description provided').strip()}"
                    for a in agents
                )

            # TOOLS
            if not tools:
                return ""
            lines = []
            for tool in tools:
                func = tool.get("function", {}) if isinstance(tool, dict) else {}
                name = func.get("name", "<unknown>")
                desc = (func.get("description") or name).strip()
                if len(desc) > 200:
                    desc = desc[:197] + "..."
                lines.append(f"- {name}: {desc}")
            return "\n".join(lines)

        # Match ${VAR} or $VAR syntax (where VAR is UPPERCASE_WORD).
        pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)'
        return re.sub(pattern, _replace, system_prompt)

    @staticmethod
    def _build_system_prompt(
        raw_prompt: str,
        cwd: Path | None = None,
        skills: list[tuple] | None = None,
        agents: list[Dict] | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        """Build the final system prompt for an agent.

        The supplied *raw_prompt* is sourced from the agent's YAML file. Any
        template variables (e.g. ``${CWD}``, ``${SKILLS}``, ``${AGENTS}``,
        ``${TOOLS}``) are substituted with runtime data from discovery
        mechanisms. If no template variables are present, a small backwards-
        compatible "current working directory name" footer is still appended so
        existing prompts continue to work unchanged.

        Args:
            raw_prompt: The base prompt text sourced from the agent YAML.
            cwd: Current working directory (defaults to project root via ``utils.project_root()``).
            skills: Optional list of ``(name, metadata)`` tuples from skill discovery.
            agents: Optional list of dicts describing available agents.
            tools: Optional list of tool schema dicts from the tool registry.

        Returns:
            The fully-built system prompt with variables substituted.
        """
        if cwd is None:
            try:
                cwd = project_root()
            except FileNotFoundError:
                # Fall back to current working directory if project markers aren't found
                # (e.g., in test environments or when used as a library)
                cwd = Path.cwd()
        else:
            cwd = Path(cwd) if isinstance(cwd, str) else cwd

        # Detect whether the raw prompt originally contained any template variables.
        had_template_vars = bool(re.search(r'\$\{?[A-Z_][A-Z0-9_]*\}?', raw_prompt))

        prompt = AgentType._substitute_variables(
            raw_prompt, cwd=cwd, skills=skills, agents=agents, tools=tools,
        )

        # Append backwards-compatible "current working directory name" footer.
        if not had_template_vars:
            prompt += f"\nCurrent working directory name: {cwd.name}"

        # Inject the persistent project memory (MEMORY.md) section, if any.
        # memory_section() returns "" when there is no memory, so this is safe
        # and unconditional.
        memory = read_memory()
        prompt += memory_section(memory)

        return prompt
    
    @classmethod
    def from_file(cls, path: str) -> "AgentType":
        """Load agent definition from a YAML file and build its system prompt.

        Expected format::
        
            name: "my_agent"                              # optional display name
            model_name: "model/identifier"
            system_prompt: "You are an autonomous coding assistant..."
            agent_tools: [execute_bash, write_file]       # or ["*"] for all
        
        The ``system_prompt`` is read directly from the YAML and augmented by
        appending the current working directory name.

        Args:
            path: Path to the YAML file.
            
        Returns:
            An AgentType instance with its system prompt fully built.
            
        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValueError: If required fields are absent or malformed, or if 
                        ``system_prompt`` is missing from the YAML.
        """
        yaml_path = Path(path)
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Agent definition file not found: {path}")
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        name = config.get("name", Path(path).stem)  # fall back to filename stem
        model_name = config.get("model_name")
        if not model_name:
            from harness_core.config import get_default_model
            default_model = get_default_model()
            if default_model is None:
                raise ValueError(
                    f"YAML '{path}' does not contain 'model_name' and no "
                    "default model is configured."
                )
            model_name = default_model

        # Resolve provider_config from the model's configuration. Providers are
        # specified entirely through the model config (no separate top-level
        # default_provider, and the agent YAML no longer carries a 'provider' key).
        from harness_core.config import get_model_config
        model_cfg = get_model_config(model_name)
        if model_cfg is None:
            raise ValueError(
                f"Model '{model_name}' referenced by '{path}' is not defined in "
                "config.yaml under 'models:'."
            )
        provider_name = model_cfg.get("provider")
        if not provider_name:
            raise ValueError(
                f"Model '{model_name}' in config.yaml must specify a 'provider'."
            )
        from harness_core.config import get_provider_config
        resolved_provider = get_provider_config(provider_name)
        if resolved_provider is None:
            raise ValueError(
                f"Provider '{provider_name}' for model '{model_name}' is not "
                "defined in config.yaml under 'providers:'."
            )
        provider_model_name = model_cfg.get("provider_model_name") or model_name

        # Compute the context length. Prefer the model config's value; fall back
        # to the global default from the harness config.
        from harness_core.config import load_harness_config
        if model_cfg.get("context_length") is not None:
            context_length = int(model_cfg["context_length"])
        else:
            context_length = int(load_harness_config()["context_length"])

        temperature = model_cfg.get("temperature")
        top_p = model_cfg.get("top_p")
        max_tokens = model_cfg.get("max_tokens")
        reasoning_effort = model_cfg.get("reasoning_effort")

        agent_tools = config.get("agent_tools", [])
        if not isinstance(agent_tools, list):
            raise ValueError("'agent_tools' must be a list of strings")

        system_prompt_raw = config.get("system_prompt")
        if not system_prompt_raw:
            raise ValueError(
                f"YAML '{path}' is missing required 'system_prompt' field. "
                f"The system prompt must now be defined inline in the YAML, "
                f"not referenced via a separate file."
            )

        # Resolve skills, agents and tools via the existing discovery mechanisms.
        from harness_core.agent.discovery import discover_agents as _discover_agents
        from harness_core.tools import AGENT_TOOLS
        from harness_core.skills import discovery

        try:
            discovered_skills = list(discovery.discover_skills())
        except Exception:
            discovered_skills = []

        try:
            discovered_agent_names = _discover_agents()
        except Exception:
            discovered_agent_names = []

        agent_descriptions: list[Dict] = []
        for agent_name, a_yaml_path in discovered_agent_names:
            # Try to load the YAML and extract a description. Fall back to an
            # empty string if the file is missing or malformed.
            try:
                with open(a_yaml_path, "r", encoding="utf-8") as fh:
                    cfg = yaml.safe_load(fh) or {}
                agent_descriptions.append({
                    "name": str(cfg.get("name", agent_name)),
                    "description": str(cfg.get("description", "")) or f"Agent '{agent_name}'",
                })
            except Exception:
                agent_descriptions.append({
                    "name": agent_name,
                    "description": f"Agent '{agent_name}'",
                })

        # Build the augmented system prompt with discovered context.
        system_prompt = cls._build_system_prompt(
            raw_prompt=system_prompt_raw,
            skills=discovered_skills if discovered_skills else None,
            agents=agent_descriptions if agent_descriptions else None,
            tools=AGENT_TOOLS if AGENT_TOOLS else None,
        )

        return cls(
            name=name,
            model_name=model_name,
            provider_model_name=provider_model_name,
            context_length=context_length,
            system_prompt=system_prompt,
            provider_config=resolved_provider,
            agent_tools=agent_tools,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )
    
    def inject_extra_system_prompt(self, text: str) -> None:
        """Append additional text to the existing system prompt.

        This is useful for injecting context-specific instructions without
        rebuilding the entire augmented prompt (which includes cwd name).

        Args:
            text: The string to append. Leading/trailing whitespace should be
                  provided by the caller if desired.
        """
        self.system_prompt = f"{self.system_prompt}\n\n{text}"
