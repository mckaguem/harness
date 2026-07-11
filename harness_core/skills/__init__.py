"""Skills module — skill discovery, activation, and management.

This module provides:
1. Skill discovery from .harness_py/skills/ directory
2. Skill activation and execution
3. Skill message interception and processing
4. Base skill class for creating new skills
"""

from .discovery import discover_skills, get_skill_by_name, get_skill_body, format_skill_catalog
from .interceptor import intercept_message, InterceptorKind, InterceptorOutcome
from .base import Skill, YamlSkill

__all__ = [
    "discover_skills",
    "get_skill_by_name",
    "get_skill_body",
    "format_skill_catalog",
    "intercept_message",
    "InterceptorKind",
    "InterceptorOutcome",
    "Skill",
    "YamlSkill",
]