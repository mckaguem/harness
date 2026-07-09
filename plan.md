# Plan for Making Harness Project Portable

## Current Issues Identified

### 1. Hardcoded Paths & CWD Dependencies
- **Test files**: Multiple `os.chdir("/workspaces/harness")` calls in `tests/test_agent.py`
- **Configuration**: `config.py` uses `Path.cwd()` for `.harness_py` discovery
- **Session management**: `session/session_utils.py` creates `.sessions` relative to cwd
- **Agent types**: `agent/types.py` uses `Path.cwd()` for CWD variable substitution

### 2. Project Structure Issues
- **Flat module layout**: Multiple top-level packages (`agent`, `commands`, `tools`, etc.)
- **No src/ directory**: Source code mixed with configuration files
- **Entry point**: `harness.py` at root level (should be in scripts/ or moved)

### 3. Import Patterns
- **Absolute imports**: Current imports assume flat structure
- **No relative imports**: Could cause issues when moving to src/ layout

## Recommended Changes

### Phase 1: Fix Hardcoded Path Assumptions
1. **Update `config.py`**:
   - Add project root detection via `__file__` or environment variable
   - Make `.harness_py` discovery work from any directory
   
2. **Update `session/session_utils.py`**:
   - Make session directory configurable via environment or config
   - Add option for absolute path specification
   
3. **Update `agent/types.py`**:
   - Make CWD resolution more flexible
   - Consider project-relative paths vs absolute paths

4. **Fix test files**:
   - Remove hardcoded `os.chdir("/workspaces/harness")`
   - Use temporary directories or mock current working directory

### Phase 2: Restructure Project Layout
1. **Create `src/harness/` directory**:
   ```
   src/harness/
   ├── __init__.py
   ├── agent/
   ├── commands/
   ├── terminal_io/
   ├── tools/
   ├── session/
   ├── skills/
   ├── model/
   └── __main__.py (or keep harness.py at root)
   ```

2. **Update `pyproject.toml`**:
   - Change `tool.setuptools.packages.find` to use `src/` layout
   - Update entry points if needed

3. **Update imports**:
   - Change from flat imports to `from harness.agent import ...`
   - Update all internal imports

### Phase 3: Make Entry Point Portable
1. **Create proper entry point**:
   - Move `harness.py` to `src/harness/__main__.py` or keep as script
   - Add `__main__.py` for `python -m harness` invocation

2. **Add setup.py or update pyproject.toml**:
   - Define proper console script entry point
   - Make installable via `pip install -e .`

### Phase 4: Configuration Management
1. **Environment variable support**:
   - `HARNESS_PROJECT_ROOT`: Override project root detection
   - `HARNESS_SESSIONS_DIR`: Custom session storage location
   - `HARNESS_CONFIG_DIR`: Custom config directory

2. **Configuration file**:
   - Consider adding `.harnessrc` or `harness.yaml` for project-specific config

### Phase 5: Testing & Validation
1. **Update test suite**:
   - Make tests independent of hardcoded paths
   - Use pytest fixtures for temporary project setups
   - Test from different working directories

2. **Create portability tests**:
   - Test project works when called from different directories
   - Test installation and import from another project

## Implementation Plan

### Step 1: Fix Immediate Path Issues
1. Remove hardcoded `/workspaces/harness` from test files
2. Make config resolution relative to project root (not cwd)
3. Update session directory creation to be configurable

### Step 2: Create src/ Structure (Optional but Recommended)
1. Move all source packages to `src/harness/`
2. Update all imports
3. Update pyproject.toml

### Step 3: Make Project Installable
1. Update pyproject.toml with proper metadata
2. Add console script entry point
3. Test `pip install -e .` works

### Step 4: Add Configuration Options
1. Add environment variable support
2. Create config resolution hierarchy (env -> config file -> defaults)
3. Document configuration options

### Step 5: Test Portability
1. Create test script that runs from different directories
2. Verify imports work correctly
3. Test skill/agent discovery from any directory

## Alternative Approach: Minimal Changes

If you prefer minimal changes:
1. Keep flat structure but fix CWD dependencies
2. Add project root detection via `__file__` in main entry point
3. Pass project root to all components that need it
4. Update tests to use temporary directories

## Success Criteria
1. Project can be imported/used from any directory
2. No hardcoded `/workspaces/harness` paths
3. Configuration resolves correctly relative to project root
4. Tests pass when run from different working directories
5. Can be installed via pip and used as a library

## Files to Modify
1. `config.py` - Path resolution
2. `session/session_utils.py` - Session directory creation
3. `agent/types.py` - CWD variable substitution
4. `tests/test_agent.py` - Remove hardcoded paths
5. `pyproject.toml` - Package configuration
6. `harness.py` - Entry point
7. All `__init__.py` files - Update imports if restructuring