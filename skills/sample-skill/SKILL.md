---
name: sample-skill
description: A test skill for verifying Agent Skills implementation. Use this to validate the discovery, activation, and execution pipeline.
---

# Sample Skill Instructions

This is a test skill used to verify that the Agent Skills system works correctly.

## When to Use

- During development testing
- To validate progressive disclosure flow
- For integration testing of skill activation

## Steps

1. Confirm you have read this instruction set
2. Verify the skills directory structure exists: `skills/sample-skill/`
3. Check that optional directories are present (scripts/, references/)

## Example Commands

To list skill contents:
```bash
ls -la skills/sample-skill/
```

To run a test script:
```bash
python skills/sample-skill/scripts/test.py
```

## Edge Cases

- Skill directory might be empty
- SKILL.md body may be minimal
- Scripts may require dependencies
