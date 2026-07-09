# Portability Issues Report

---

## 1. Executive Summary

The project currently contains multiple hard‑coded absolute paths (`/workspaces/harness`) and relies on `Path.cwd()` for locating configuration, sessions, and other resources. These practices break portability: the code works only when the repository is located at the exact absolute path used during development or when the process is started from that directory. Running the project from any other location results in `FileNotFoundError`, incorrect session handling, and failing tests.

---

## 2. Current Architecture Analysis

- **Configuration (`config.py`)** – Determines the location of the hidden directory `.harness_py` using `Path.cwd()`. This assumes the working directory is the repository root.
- **Agent Types (`agent/types.py`)** – Accepts a `cwd` argument that defaults to `Path.cwd()`. Many agents use this default, meaning their internal file resolution is tied to the process' current directory.
- **Session Management (`session/session_utils.py`)** – Stores session files under `Path.cwd() / ".sessions"`.
- **Utilities (`tools/utils.py`, `tools/grep.py`, `tools/activate_skill.py`)** – Build paths with `Path.cwd()` and then resolve them.
- **Tests (`tests/test_agent.py`)** – Contain explicit `os.chdir("/workspaces/harness")` calls to force the cwd to the repository root before each test block.

---

## 3. Specific Issues Identified

| File | Line | Problematic Code | Issue Type |
|------|------|------------------|------------|
| `tests/test_agent.py` | 37 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 60 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 84 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 101 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 118 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 135 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 158 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 176 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 197 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 217 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 236 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 257 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 276 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `tests/test_agent.py` | 296 | `os.chdir("/workspaces/harness")` | Hard‑coded absolute path |
| `agent/types.py` | 145 | `cwd = Path.cwd() if cwd is None else (Path(cwd) if isinstance(cwd, str) else cwd)` | Implicit reliance on CWD |
| `config.py` | 23 | `return (Path.cwd() / ".harness_py").resolve()` | Implicit reliance on CWD |
| `session/session_utils.py` | 192 | `sessions_dir = Path.cwd() / ".sessions"` | Implicit reliance on CWD |
| `tools/utils.py` | 11‑12 | `cwd = Path.cwd().resolve()` / `target = (Path.cwd() / filename).resolve()` | Implicit reliance on CWD |
| `tools/grep.py` | 49‑50 | `cwd = Path.cwd().resolve()` / `target = (Path.cwd() / path).resolve()` | Implicit reliance on CWD |
| `tools/activate_skill.py` | 48‑56 | Uses `Path.cwd()` to locate the `.harness_py/skills` directory and the skill files | Implicit reliance on CWD |

---

## 4. Impact Assessment

- **Running from a different directory**: All components that compute paths relative to `Path.cwd()` will point to the wrong location, causing missing‑file errors, inability to locate the hidden `.harness_py` directory, and failing session persistence.
- **CI/CD pipelines**: Build agents often check out the repository into temporary workspaces (e.g., `/tmp/checkout123`). The hard‑coded absolute paths will not exist, causing test failures and broken builds.
- **Developer experience**: Contributors cloning the repo to a different path must manually edit tests or set the CWD, which is error‑prone.
- **Packaging**: If the project is installed as a package and executed from a virtual environment, `Path.cwd()` will reflect the runtime cwd (e.g., a user's home directory) rather than the package location, breaking configuration discovery.

---

## 5. Recommendations

### 5.1 High‑Priority Fixes

1. **Replace `os.chdir("/workspaces/harness")` in tests**
   - **Current**: `os.chdir("/workspaces/harness")`
   - **Fix**: Use `os.chdir(Path(__file__).resolve().parents[2])` (or a fixture that sets the cwd to the repository root dynamically).
   - **Rationale**: Makes tests independent of absolute location.

2. **Centralise project root discovery**
   - Add a helper function, e.g., `def project_root() -> Path: return Path(__file__).resolve().parents[2]` (adjust depth as appropriate).
   - Update all `Path.cwd()` usages that are meant to point at the repo root to use `project_root()` instead.

3. **Configuration Path**
   - **Current**: `return (Path.cwd() / ".harness_py").resolve()` in `config.py`
   - **Fix**:
   ```python
   from .utils import project_root
   def get_config_dir() -> Path:
       return project_root() / ".harness_py"
   ```
   - Ensure callers import and use `get_config_dir()`.

### 5.2 Medium‑Priority Fixes

- **Session Directory**: Change `sessions_dir = Path.cwd() / ".sessions"` to `sessions_dir = project_root() / ".sessions"`.
- **Tool utilities** (`tools/utils.py`, `tools/grep.py`, `tools/activate_skill.py`): Replace any `Path.cwd()` concatenations with `project_root()`.
- **Agent Types**: Remove the default `cwd = Path.cwd()`; require callers to pass explicit `cwd` or default to `project_root()`.

### 5.3 Low‑Priority / Clean‑up

- Audit any remaining `Path.cwd()` occurrences that are truly intended to reflect the *runtime* cwd (e.g., when a user explicitly changes directory) and document them.
- Add unit tests that verify path resolution works when the repo is cloned to a temporary directory.

---

## 6. Python Project Best Practices for Portability

| Practice | Description |
|----------|-------------|
| **Never hard‑code absolute paths** | Use `Path(__file__)` relative to the module file or a dedicated project‑root helper. |
| **Prefer `Path` over string joins** | `pathlib.Path` provides OS‑agnostic path handling. |
| **Make the repository root discoverable** | A single function – e.g., `project_root()` – should be the source of truth for all relative paths. |
| **Explicitly pass configuration directories** | Functions/classes that need a location should accept a `base_path: Path` argument instead of implicitly using `Path.cwd()`. |
| **Use fixtures for test CWD** | Pytest fixtures can `chdir` to the repo root before each test, making the test suite independent of the environment. |
| **Document expectations** | README should state that the project can be run from any directory and that no manual path changes are required. |

---

## 7. Implementation Roadmap

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| **Phase 1 – Foundations** | • Add `project_root()` helper in a new module `harness/utils.py`.<br>• Update `config.py`, `session/session_utils.py`, and `tools/*` to use the helper.<br>• Run existing test suite to capture failures. | 2 days |
| **Phase 2 – Test Refactor** | • Replace all `os.chdir("/workspaces/harness")` calls with a Pytest fixture `repo_root_cwd` that changes directory to `project_root()`.
• Remove duplicate `os.chdir` lines.
• Add documentation for the fixture. | 1 day |
| **Phase 3 – Agent & Core Code** | • Modify `agent/types.py` to default `cwd` to `project_root()` when omitted.
• Review any remaining `Path.cwd()` usages; replace with `project_root()` or add comments if intentional.
• Add type hints and unit tests for the new behaviour. | 2 days |
| **Phase 4 – Verification & Cleanup** | • Run full test matrix on multiple temporary clone locations.
• Update CI configuration to clone repo into a random directory and run tests.
• Update README with portability notes.
• Lint and format changes. | 1 day |
| **Phase 5 – Release** | • Bump version, generate changelog entry summarising portability fixes.
• Publish to PyPI (if applicable). | 0.5 day |

**Total estimated effort:** ~6.5 working days.

---

*Prepared by the Documentation & Content Agent.*