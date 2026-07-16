---
name: "harness_core.config"
description: "Configuration resolution — project and global .harness_py paths."
source: "harness_core/config.py"
---

Configuration resolution — project and global .harness_py paths.

## References
- [get_project_dir](harness_core_config_get_project_dir) - Return the project config directory ``project_root/
- [get_global_dir](harness_core_config_get_global_dir) - Return the global config directory, defaulting to ``~/
- [get_harness_py_dir](harness_core_config_get_harness_py_dir) - Return both harness_py directories as a ``(project_dir, global_dir)`` tuple
- [get_discovery_dirs](harness_core_config_get_discovery_dirs) - Return ordered discovery directories for a given component (skills/agents)
- [resolve_config_path](harness_core_config_resolve_config_path) - Resolve a relative path (e
- [_load_yaml_file](harness_core_config__load_yaml_file) - Load a YAML file if it exists, returning an empty dict otherwise
- [_build_providers_dict](harness_core_config__build_providers_dict) - Build a providers dict from a raw YAML provider list
- [_build_models_dict](harness_core_config__build_models_dict) - Build a models dict from a raw YAML model list
- [_reset_config_cache](harness_core_config__reset_config_cache) - Clear the module-level config cache
- [_get_cached_config](harness_core_config__get_cached_config) - Return cached configuration, loading it lazily on first call
- [load_harness_config](harness_core_config_load_harness_config) - Load and merge configuration from global and project ``config
- [get_provider_config](harness_core_config_get_provider_config) - Retrieve a ProviderConfig by its identifier name
- [get_model_config](harness_core_config_get_model_config) - Retrieve a ModelConfig by its name
- [get_default_model](harness_core_config_get_default_model) - Return the default model name, if specified
- [VALID_TASK_STATUSES](harness_core_config_VALID_TASK_STATUSES) - Constant
- [_SKILLS_DIR](harness_core_config__SKILLS_DIR) - Constant
- [_AGENTS_DIR](harness_core_config__AGENTS_DIR) - Constant
- [CONFIG_FILENAME](harness_core_config_CONFIG_FILENAME) - Constant
- [Module Index](../index/harness_core.md) - Parent module index
