# Import Refactoring Analysis Report

## Summary
Analysis of Python files in `/workspaces/harness` to identify imports that need updating for refactoring.

## Files Requiring Updates

### 1. Imports of skills_discovery module (should be from skills.discovery)
**Files to update:**
1. `agent/types.py` (line 212): `import skills_discovery`
2. `harness.py` (line 16): `from skills_discovery import discover_skills, format_skill_catalog`
3. `skills/interceptor.py` (line 130): `from skills_discovery import get_skill_by_name`
4. `tests/test_skills.py` (lines 53, 66, 76, 87, 203): Multiple imports from `skills_discovery`
5. `tools/activate_skill.py` (line 24): `from skills_discovery import get_skill_body`

**Current imports:** `from skills_discovery` or `import skills_discovery`
**Should be:** `from skills.discovery`

### 2. Imports of skills_interceptor module (should be from skills.interceptor)
**Files to update:**
1. `agent/loop.py` (line 13): `from skills_interceptor import intercept_message, InterceptorKind`

**Current imports:** `from skills_interceptor`
**Should be:** `from skills.interceptor`

### 3. Imports of model_utils module (should be from model.utils)
**Files to update:**
1. `tests/test_terminal_io.py` (line 10): `from model_utils import get_context_length`

**Current imports:** `from model_utils`
**Should be:** `from model.utils`

### 4. Imports from deprecated agent.session or agent.session_utils
**Findings:** No imports found using `from agent.session` or `from agent.session_utils`. All session-related imports correctly use `from session` or `from session.session_utils`.

### 5. Imports from sessions module (should be from session)
**Findings:** No imports found using `from sessions`. All imports correctly use `session` (singular).

## Additional Notes

### Current Correct Imports (Already Following New Structure)
1. `session` module imports are already correct (using `from session` not `from sessions`)
2. `session.session_utils` imports are already correct
3. `session.context_compression` imports are already correct

### Dependency Analysis Findings
The `dependency_analyzer.py` file contains references to module names in its dependency categorization logic (lines 218, 220, 216) but these are string comparisons, not import statements, and don't need changing.

## Total Files Requiring Updates: 7 files
1. agent/types.py
2. harness.py
3. skills/interceptor.py
4. tests/test_skills.py
5. tools/activate_skill.py
6. agent/loop.py
7. tests/test_terminal_io.py

## Recommended Update Strategy
1. **Batch update by module type**: Update all `skills_discovery` imports first, then `skills_interceptor`, then `model_utils`
2. **Test after each batch**: Run tests to ensure no regressions
3. **Verify imports still work**: Check that the refactored modules (`skills.discovery`, `skills.interceptor`, `model.utils`) properly export the same functions/classes