---
name: "harness_core.agent.discovery"
description: "Agents discovery — scans both config paths for available agent YAML files."
source: "harness_core/agent/discovery.py"
---

Agents discovery — scans both config paths for available agent YAML files.

Supports two config paths (analogous to skills discovery):
- **Project path**: ``cwd/.harness_py/agents/``
- **Global path**: ``~/.harness_py/agents/``

When an agent name exists in both paths, the project version wins.

## References
- [_merge_agent_discoveries](harness_core_agent_discovery__merge_agent_discoveries) - Merge multiple agent discovery results with precedence
- [discover_agents](harness_core_agent_discovery_discover_agents) - Discover all agent YAML files across the specified directories
- [get_agent_yaml](harness_core_agent_discovery_get_agent_yaml) - Look up an agent YAML file by name
- [get_agent_yaml_paths](harness_core_agent_discovery_get_agent_yaml_paths) - Return the absolute paths to all available agents/ directories
- [_AGENT_DISCOVERY_CACHE](harness_core_agent_discovery__AGENT_DISCOVERY_CACHE) - Constant
- [Module Index](../index/harness_core_agent.md) - Parent module index
