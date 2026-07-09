# Portability Improvements Changelog

## Summary
Made the Harness project fully portable so it can be run from any directory. 
Removed hardcoded path dependencies and replaced them with project root detection.

## Files Modified

### 1. `utils.py` (NEW)
- Created new utility module with `project_root()` function
- Detects project root by looking for markers (.git, pyproject.toml, .harness_py)
- Starts from current file location or specified path
- Includes proper error handling and documentation

### 2. `config.py`
- Updated `get_project_dir()` to use `project_root()` instead of `Path.cwd()`
- Configuration now resolves relative to project root rather than current working directory
- Import: `from utils import project_root`

### 3. `session/session_utils.py`
- Updated `ensure_sessions_dir()` to use `project_root()` as default
- Sessions directory now created in project root instead of current working directory
- Maintained backward compatibility with optional `base_path` parameter
- Import: `from utils import project_root`

### 4. `tools/utils.py`
- Updated `is_safe_path()` to use `project_root()` with fallback to `Path.cwd()`
- Added fallback logic for when project markers aren't found
- Improved documentation to reflect new behavior
- Import: `from utils import project_root`

### 5. `tools/grep.py`
- Updated path resolution to use `project_root()` with fallback
- Ensures search paths are relative to project root
- Added error handling for missing project markers
- Import: `from utils import project_root`

### 6. `tools/activate_skill.py`
- Updated skill discovery paths to use `project_root()`
- Skills now discovered relative to project root
- Import: `from utils import project_root`

### 7. `tools/write_file.py`, `tools/read_file.py`, `tools/edit_file.py`
- Updated error messages to reference "project directory" instead of "current directory"
- Consistency improvements for error messages

### 8. `agent/types.py`
- Updated `_build_system_prompt()` to use `project_root()` with fallback
- Handles cases where project markers aren't found (test environments, library use)
- Updated documentation for CWD variable to reflect project root usage
- Import: `from utils import project_root`

### 9. `tests/test_agent.py`
- Removed 14 hardcoded `os.chdir("/workspaces/harness")` calls
- Replaced with portable `old_cwd = os.getcwd()` and `os.chdir(old_cwd)` pattern
- Tests now work from any directory
- Import: `from utils import project_root`

### 10. `tests/test_grep.py`
- Updated test to use `project_root()` instead of `Path.cwd()`
- Line 308: `target.relative_to(project_root())` instead of `target.relative_to(Path.cwd())`
- Import: `from utils import project_root`

### 11. `tests/test_skills.py`
- Updated skill discovery tests to use `project_root()`
- Lines 207, 222: `project_root() / ".harness_py" / "skills"` instead of `Path.cwd() / ".harness_py" / "skills"`
- Import: `from utils import project_root`

## Key Improvements

### 1. Portable Project Root Detection
- `project_root()` function detects project root via markers
- Works from any directory within or outside the project
- Falls back to current working directory when markers not found

### 2. Removed Hardcoded Paths
- Eliminated 14 instances of `os.chdir("/workspaces/harness")` in tests
- No more absolute path dependencies

### 3. Consistent Path Resolution
- All modules now resolve paths relative to project root
- Fallback to current working directory for edge cases
- Better compatibility with CI/CD environments

### 4. Improved Test Portability
- Tests can run from any directory
- Works in temporary clones (CI/CD pipelines)
- No assumptions about current working directory

## Testing Results
- **259 tests pass** from project root
- Tests pass from subdirectories (e.g., `tests/`)
- Tests pass in temporary clones
- Project can be imported/used from any directory

## Usage Examples

### From Project Root
```bash
cd /workspaces/harness
python harness.py
```

### From Subdirectory
```bash
cd /workspaces/harness/tests
python ../harness.py
```

### From Anywhere (with PYTHONPATH)
```bash
cd /any/directory
PYTHONPATH=/workspaces/harness python -c "from harness import main; main()"
```

### Installation and Use
```bash
# Install as editable package
pip install -e /workspaces/harness

# Use from anywhere
cd /any/directory
python -c "import harness; print(harness.__file__)"
```

## Future Considerations

### Optional: src/ Directory Structure
For even better packaging, consider moving to:
```
src/harness/  # All source code
tests/        # Test suite
```

### Optional: Environment Variables
Could add support for:
- `HARNESS_PROJECT_ROOT`: Override project root detection
- `HARNESS_CONFIG_DIR`: Custom configuration directory

### Optional: Configuration File
`.harnessrc` or `harness.yaml` for project-specific settings

## Conclusion
The Harness project is now fully portable and can be:
1. Run from any directory
2. Used as a library from other projects  
3. Installed via pip
4. Tested in CI/CD pipelines without path modifications
5. Contributed to by developers with different directory structures