---
name: "harness_core.skills.discovery"
description: "Skills discovery module — scans for and validates agent skills."
source: "harness_core/skills/discovery.py"
---

Skills discovery module — scans for and validates agent skills.

Supports two config paths:
- **Project path**: ``cwd/.harness_py/skills/``
- **Global path**: ``~/.harness_py/skills/`` (overridable via ``HARNESS_PY_HOME``)

When a skill name exists in both paths, the project version wins.

## References
- [parse_skill_metadata](harness_core_skills_discovery_parse_skill_metadata) - Parse a skill directory's SKILL
- [_merge_skill_discoveries](harness_core_skills_discovery__merge_skill_discoveries) - Merge multiple skill discovery results with precedence
- [discover_skills](harness_core_skills_discovery_discover_skills) - Discover and validate all skills across the specified directories
- [format_skill_catalog](harness_core_skills_discovery_format_skill_catalog) - Format a list of skills into a concise catalog for system prompt injection
- [get_skill_by_name](harness_core_skills_discovery_get_skill_by_name) - Look up a skill by name and return its parsed metadata
- [get_skill_body](harness_core_skills_discovery_get_skill_body) - Get the body content of a specific skill's SKILL
- [check_command_skill_collision](harness_core_skills_discovery_check_command_skill_collision) - Check for name collisions between provided command names and discovered skills
- [_SKILL_DISCOVERY_CACHE](harness_core_skills_discovery__SKILL_DISCOVERY_CACHE) - Constant
- [Module Index](../index/harness_core_skills.md) - Parent module index
