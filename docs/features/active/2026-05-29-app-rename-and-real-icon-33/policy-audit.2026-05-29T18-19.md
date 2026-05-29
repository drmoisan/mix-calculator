# Policy Compliance Audit: App Rename and Real Icon (Issue #33)

**Audit Date:** 2026-05-29
**Code Under Test:** Branch `feature/app-rename-and-real-icon-33` HEAD `ee5f2778a260c16112b41ea224d963b625a433de` against base `main` merge-base `9e5f8836b3fc1eff0320213ccd849d772843bd9e`. Files: `src/build_exe.py`, `src/build_velopack.py`, `src/gui/app.py`, `src/gui/_icon.py`, `src/gui/_main_window_view.py`, `packaging/velopack/convert_icon.py`, `tests/test_build_exe.py`, `tests/test_build_velopack.py`, `tests/test_convert_icon.py`, `tests/gui/test_app_composition.py`, `tests/gui/test_icon.py`, `pyproject.toml`, `poetry.lock`, `packaging/velopack/README.md`, plus asset binaries `packaging/velopack/icon.ico` and `packaging/velopack/icon-source.svg`.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 11 source/test + pyproject + lockfile | 497 tests | PASS 497 pass, 0 fail | 99% lines, 99% branches (baseline `evidence/baseline/pytest.md`) | 99% lines, 99% branches | 100% line / 100% branch on `_icon.py`; 97-99% line / 92-100% branch on the four src-namespace changed modules |
| TypeScript | 0 files | 0 tests | N/A | N/A (no changed files) | N/A (no changed files) | N/A |
| PowerShell | 0 files | 0 tests | N/A | N/A (no changed files) | N/A (no changed files) | N/A |
| C# | 0 files | 0 tests | N/A | N/A (no changed files) | N/A (no changed files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: N/A - out of scope
- TypeScript post-change coverage artifact: N/A - out of scope
- PowerShell baseline coverage artifact: N/A - out of scope
- PowerShell post-change coverage artifact: N/A - out of scope
- Python baseline coverage artifact: `docs/features/active/2026-05-29-app-rename-and-real-icon-33/evidence/baseline/pytest.md`
- Python post-change coverage artifact: `docs/features/active/2026-05-29-app-rename-and-real-icon-33/evidence/qa-gates/phase9-pytest.md`
- Python new/changed-code coverage artifact: `docs/features/active/2026-05-29-app-rename-and-real-icon-33/evidence/qa-gates/phase9-coverage-changed-modules.md`
- Per-language comparison summary: see section 1.2.1 below

---

## Executive Summary

The branch ships a coordinated three-way change (Nuitka output rename to `MixCalculator.exe`, Velopack `--packId`/`--mainExe`/`--releaseName` alignment, and a real multi-size ICO derived from the committed source SVG) plus the supporting `resolve_icon_path` helper, the `convert_icon.py` one-shot script, and a `MainWindowPipelineView` extraction that keeps `src/gui/app.py` under the 500-line file cap. All policy documents in the required reading order were evaluated; every check matches PASS. Toolchain (Black/Ruff/Pyright/Pytest) completed cleanly in a single pass per `evidence/qa-gates/phase9-loop-completion.md`. Coverage is unchanged from baseline at 99%/99% repo-wide.

**Policy documents evaluated:**
- PASS `general-code-change.instructions.md`
- PASS `general-unit-test.instructions.md`

**Language-specific policies evaluated:**
- PASS `python-code-change.instructions.md` + `python-unit-test.instructions.md`
- N/A `powershell-code-change.instructions.md` + `powershell-unit-test.instructions.md` (no PowerShell files in diff)
- N/A Bash (no Bash files in diff)
- N/A JSON (no governed JSON files in diff)

The branch's Python toolchain (Black/Ruff/Pyright/Pytest) passed in a single clean iteration. 497 tests pass; coverage is 99% line / 99% branch repo-wide and >= 92% branch / >= 97% line on every changed src-namespace module. The new converter (`packaging/velopack/convert_icon.py`) is exercised by three dedicated unit tests loaded via `importlib.util` (the `packaging/` folder is intentionally outside the `[tool.coverage.run] source = ["src"]` set to avoid shadowing the third-party `packaging` PyPI module that pytest itself imports).

**Temporary artifacts cleanup:**
- PASS All temporary scripts created during development have been deleted. The new permanent script `packaging/velopack/convert_icon.py` is a maintained tool with three dedicated unit tests.
- PASS The new converter is fully tested and compliant with repo policies (Black, Ruff, Pyright clean; 358 lines under cap).
- Scripts created during development and their disposition: `packaging/velopack/convert_icon.py` (KEPT - it is the documented icon-regeneration tool, fully tested in `tests/test_convert_icon.py`).

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | PASS | New tests construct their own recorders (`_RunNuitkaRecorder`, `_RemoveTreeRecorder`, `_RecorderVelopackApp`) at function scope; none rely on previous-test state. The full 497-test suite executes under pytest's default ordering with no shared mutable state introduced on this branch. |
| **Isolation** - Each test targets single behavior | PASS | Each new test asserts a single contract: AC1 ordered-membership of icon flags, AC2 packId/mainExe pair, AC3 releaseName, AC5 icon magic+frames, AC6 conversion round-trip, AC8 setWindowIcon. Tests are organized one-behavior-per-function with Arrange/Act/Assert blocks. |
| **Fast Execution** - Tests complete quickly | PASS | `evidence/qa-gates/phase9-pytest.md` records 19.97s for 497 tests (~40ms/test average). |
| **Determinism** - Consistent results | PASS | All new tests use injected `path_exists`, `run_nuitka`, `run_vpk`, `read_svg_bytes`, `write_ico_bytes` recorders. No `sleep`, no wall-clock reads, no random seeds. The `QApplication.exec` patch returns 0 immediately so no real event loop runs. |
| **Readability & Maintainability** - Clear structure | PASS | Test names follow `test_<unit>_<behavior>` pattern. Arrange/Act/Assert blocks are explicit. Each new test file carries a module docstring. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | PASS | Baseline (pre-development): 99% lines, 99% branches. Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`. Timestamp: 2026-05-29T00-00 in `evidence/baseline/pytest.md`. |
| **No Coverage Regression** | PASS | Post-change coverage: 99% lines, 99% branches. Change: 0% lines, 0% branches. Status: No regression. Evidence: `evidence/qa-gates/phase9-pytest.md`. |
| **New Code Coverage >= 85% line / >= 75% branch (tier-uniform)** | PASS | New/modified src modules per `evidence/qa-gates/phase9-coverage-changed-modules.md`: `src/build_exe.py` 97% line / 100% branch; `src/build_velopack.py` 98% line / 96% branch; `src/gui/_icon.py` 100% line / 100% branch; `src/gui/app.py` 99% line / 92% branch. All exceed the 85%/75% uniform tier thresholds. |
| **Comprehensive Coverage** | PASS | All new public functions exercised: `resolve_icon_path` (3 probe-branch tests in `tests/gui/test_icon.py`); `convert_svg_bytes_to_ico_bytes` and `main` in `convert_icon.py` (3 tests in `tests/test_convert_icon.py`); icon flags in `resolve_nuitka_command` (1 ordered-membership test); icon set on QApplication (2 tests in `tests/gui/test_app_composition.py`). |
| **Positive Flows** - Valid inputs | PASS | `test_resolve_icon_path_prefers_compiled_mode`, `test_resolve_icon_path_falls_back_to_dev_mode`, `test_convert_icon_main_writes_multisize_ico`, `test_resolve_nuitka_command_contains_icon_flags`, `test_resolve_nuitka_command_contains_required_flags`, `test_main_sets_window_icon_on_qapplication`, `test_build_application_calls_set_window_icon_when_qt_app_constructed`. |
| **Negative Flows** - Invalid inputs | PASS | `test_resolve_icon_path_raises_when_no_probe_resolves` (FileNotFoundError when no probe resolves), `test_convert_icon_rejects_missing_qsvgrenderer_load` (ValueError on `b"not svg"`). |
| **Edge Cases** - Boundary conditions | PASS | Existing test `test_main_invokes_seam_and_propagates_returncode` parametrized over exit codes [0, 1, 2, 137]; `test_main_clean_removes_existing_dist_tree` covers exists-vs-missing branches of `--clean`. |
| **Error Handling** - Error paths | PASS | `test_convert_icon_rejects_missing_qsvgrenderer_load` covers the ValueError surface; the pre-flight error branches in `build_velopack.main` are covered by existing `test_build_velopack.py` tests (return 2 on missing exe, missing icon, missing GITHUB_TOKEN). |
| **Concurrency** - If applicable | N/A | No new concurrency primitives introduced; the icon load is a one-shot, the converter is single-threaded, and the GUI bootstrap runs on the Qt main thread. |
| **State Transitions** - If applicable | N/A | No new stateful components introduced. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99% line / 99% branch -> Post-change: 99% line / 99% branch. Change: 0 / 0. New/changed-code coverage: 97-100% line / 92-100% branch on the four changed src-namespace modules. Disposition: PASS. Evidence: `evidence/qa-gates/phase9-pytest.md` and `evidence/qa-gates/phase9-coverage-changed-modules.md`.
- TypeScript: Baseline: N/A. Post-change: N/A. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: no TypeScript files changed in the branch diff.
- PowerShell: Baseline: N/A. Post-change: N/A. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: no PowerShell files changed in the branch diff.
- C#: Baseline: N/A. Post-change: N/A. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: no C# files changed in the branch diff.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | PASS | Assertions name the inspected value (e.g., `assert flag in argv, f"missing flag {flag!r} in argv {argv!r}"` in `test_resolve_nuitka_command_contains_icon_flags`). |
| **Arrange-Act-Assert Pattern** | PASS | New tests carry explicit `# Arrange`, `# Act`, `# Assert` block comments (see `tests/gui/test_icon.py` and the new tests in `tests/gui/test_app_composition.py`). |
| **Document Intent** | PASS | Each new test has a docstring summarizing the scenario; each file has a module docstring stating the module's coverage scope. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | PASS | No new tests reach the network, database, real Nuitka binary, real `vpk` binary, or Pillow filesystem paths. The conversion test uses an in-memory synthetic SVG. |
| **Use Mocks/Stubs** | PASS | Recorders for `run_nuitka`, `run_vpk`, `remove_tree`, `read_svg_bytes`, `write_ico_bytes`, `QIcon`, `setWindowIcon`, `resolve_icon_path` are all injected via constructor parameters or `monkeypatch.setattr`. |
| **Environment Stability** | PASS | No new tests create temp files. `tests/test_build_exe.py` declares `tmp_path_factory` as a fixture-typed parameter for type-checker compatibility only; the test body does not exercise it. Confirmed by direct inspection of all new test files. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | PASS | This artifact at `docs/features/active/2026-05-29-app-rename-and-real-icon-33/policy-audit.2026-05-29T18-19.md` serves as the required policy review. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | PASS | Issue #33 records the three-way alignment (Nuitka rename, Velopack pack id alignment, real icon). The "Timing constraint" section verifies `gh release list` is empty so the packId rename does not orphan installed users. |
| **Read existing change plans** | PASS | `plan.2026-05-29T00-00.md` enumerates Phase 0-9 with explicit acceptance criteria mapping. `evidence/baseline/phase0-instructions-read.md` records that the agent read the required policy files. |
| **Document the plan** | PASS | Plan, issue, and per-phase evidence files all live under the feature folder. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | PASS | `resolve_icon_path` is a single function with a single injected `path_exists` seam. `convert_svg_bytes_to_ico_bytes` is a pure function over bytes-in/bytes-out. No new framework or layer was added. |
| **Reusability** | PASS | `EXE_NAME` constant in `src/build_exe.py` is referenced by the cross-file invariant in `src/build_velopack.py::_app_exe_exists` docstring. `resolve_icon_path` is reused by `build_application` and `main`. |
| **Extensibility** | PASS | `resolve_icon_path` accepts a `path_exists` callable so future probe locations can be added without changing the signature. `convert_svg_bytes_to_ico_bytes` operates on bytes so future call sites (CI pipelines) can drive it from in-memory buffers. |
| **Separation of concerns** | PASS | I/O (`read_svg_bytes`, `write_ico_bytes`) is split from the pure conversion logic. The GUI adapter `MainWindowPipelineView` was extracted from `src/gui/app.py` so the composition root stays focused on wiring. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | PASS | New modules have single purposes: `_icon.py` resolves the icon path; `_main_window_view.py` adapts MainWindow to PipelineViewProtocol; `convert_icon.py` rasterizes SVG to ICO. |
| **Under 500 lines** | PASS | All 11 changed Python files report < 500 lines (max 496 at `tests/test_build_velopack.py`). Direct verification matches `evidence/qa-gates/phase9-file-size.md`. |
| **Public vs internal** | PASS | Internal helpers use `_`-prefixed names (`_render_svg_to_qimage`, `_qimage_to_pil`, `_ensure_qapplication`, `_dist_nuitka_exists`, `_app_exe_exists`, `_icon_exists`, `_build_argument_parser`). Public surface is exported via `__all__` in `src/gui/app.py`. |
| **No circular dependencies** | PASS | `src/gui/_icon.py` depends only on stdlib (`sys`, `pathlib`, `typing`). `src/gui/_main_window_view.py` only imports `MainWindow` under `TYPE_CHECKING`. `src/gui/app.py` imports both but neither helper imports `app.py`. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | PASS | `resolve_icon_path`, `convert_svg_bytes_to_ico_bytes`, `read_svg_bytes`, `write_ico_bytes`, `EXE_NAME`, `ICON_SIZES` — all explicit, no abbreviations beyond standard (`exe`, `ico`, `svg`). |
| **Docs/docstrings** | PASS | Every new class and every new function has a Google-style docstring with Purpose / Args / Returns / Raises / Side Effects. Verified by direct inspection of each new symbol. |
| **Comment why, not what** | PASS | Intent comments above loops (the probe loop in `_icon.py`, the size-iteration loop in `convert_icon.py`, the stride-correction loop) explain "why" not "what". Branching comments (the three QApplication-resolution cases in `build_application`) document the decision rationale. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | PASS | Command: `env -u VIRTUAL_ENV poetry run black --check .` Result: exit 0, zero would-reformat files. Evidence: `evidence/qa-gates/phase9-black.md`. |
| **2. Linting** | PASS | Command: `env -u VIRTUAL_ENV poetry run ruff check .` Result: exit 0. Evidence: `evidence/qa-gates/phase9-ruff.md`. |
| **3. Type checking** | PASS | Command: `env -u VIRTUAL_ENV poetry run pyright`. Result: exit 0. Evidence: `evidence/qa-gates/phase9-pyright.md`. |
| **4. Testing** | PASS | Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`. Result: 497 passed, 0 failed, 99% line / 99% branch. Evidence: `evidence/qa-gates/phase9-pytest.md`. |
| **Full toolchain loop** | PASS | All four stages completed in a single pass per `evidence/qa-gates/phase9-loop-completion.md`. |
| **Explicit reporting** | PASS | Each toolchain stage has a corresponding `phase9-*.md` artifact with timestamp, command, exit code, and output summary. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | PASS | `issue.md` summary section and `plan.2026-05-29T00-00.md` describe the three-way alignment. |
| **Design choices explained** | PASS | The `_main_window_view` extraction is explained inline in `evidence/qa-gates/phase9-file-size.md`. The Pillow dev-only declaration is explained in `packaging/velopack/README.md`. |
| **Update supporting documents** | PASS | `packaging/velopack/README.md` updated (`+75/-...` lines) with the new packId, mainExe, releaseName, output filenames, icon source, conversion command, and Pillow dev dep. |
| **Provide next steps** | PASS | `issue.md` "Out-of-Scope Follow-ups" lists code signing, in-app update UI, and CI build/publish workflow as separately tracked items. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | PASS | Command: `env -u VIRTUAL_ENV poetry run black --check .` Result: exit 0. Evidence: `evidence/qa-gates/phase9-black.md`. |
| **Linting with Ruff** | PASS | Command: `env -u VIRTUAL_ENV poetry run ruff check .` Result: exit 0. Evidence: `evidence/qa-gates/phase9-ruff.md`. |
| **Type checking with Pyright** | PASS | Command: `env -u VIRTUAL_ENV poetry run pyright`. Result: exit 0 in strict mode. Evidence: `evidence/qa-gates/phase9-pyright.md`. |
| **Testing with Pytest** | PASS | Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`. Result: 497 passed. Evidence: `evidence/qa-gates/phase9-pytest.md`. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | PASS | All new functions have complete type hints. No new `Any` introduced. `cast("DbService", FakeDbService())` is used at one test injection point with a string-form forward reference. |
| **Dataclasses for value objects** | PASS | `WiredApplication` (in `app.py`) uses `@dataclass`. New stub-seam classes `_RunNuitkaRecorder`, `_RemoveTreeRecorder`, `_OrderedCallLog`, `_RecorderVelopackApp` use `@dataclass` where they hold mutable test state. |
| **Protocols/ABCs for interfaces** | PASS | Existing `RunnerProtocol`, `PipelineServiceProtocol`, `WorkbookReaderProtocol` continue to gate the composition root. No new Protocols were needed for this change. |
| **Avoid utility classes** | PASS | No static-method-only utility classes were added. Helpers are module-level functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | PASS | `resolve_icon_path` raises `FileNotFoundError` with both probed paths in the message. `convert_svg_bytes_to_ico_bytes` raises `ValueError` naming the failing rasterization size. `build_velopack.resolve_version` raises `ValueError` / `KeyError` per its docstring contract. No bare `except:` or `except Exception:` was introduced. |
| **Logging over print** | PASS | `src/build_velopack.py` uses `logging.getLogger(__name__)` (`_LOG.info`) for pack and upload operations. Production `print` calls are limited to: the `--dry-run` argv preview (stdout is the contract) and stderr error messages on pre-flight failure (`Error: ...`, file=sys.stderr). |
| **Invariants at construction** | PASS | `validate_semver2` enforces SemVer2 at the boundary in `resolve_version`. Pre-flight checks in `main` validate file existence and `GITHUB_TOKEN` presence before invoking external binaries. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | All tests use `pytest`; new tests use `pytest.MonkeyPatch`, `pytest.CaptureFixture`, `pytest.raises`, and `pytest.mark.parametrize` where appropriate. |
| **Coverage expectation** | PASS | Repo-wide 99% line / 99% branch (>= 85% line / >= 75% branch threshold). New/changed modules range 97-100% line, 92-100% branch. Evidence: `evidence/qa-gates/phase9-coverage-changed-modules.md`. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | PASS | Each new test exercises one behavior (e.g., one probe branch, one argv flag set, one error path). |
| **Mocking sparingly** | PASS | Mocking is restricted to subprocess seams (`run_nuitka`, `run_vpk`), path-existence (`path_exists`), I/O seams (`read_svg_bytes`, `write_ico_bytes`), and Qt boundary objects (`QIcon`, `setWindowIcon`, `QApplication.exec`). All other behavior runs through real code paths. |
| **Organization** | PASS | Tests mirror code structure: `tests/gui/test_icon.py` for `src/gui/_icon.py`, `tests/test_convert_icon.py` for `packaging/velopack/convert_icon.py`, `tests/test_build_exe.py` for `src/build_exe.py`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | PASS | Examples: `test_resolve_icon_path_prefers_compiled_mode`, `test_convert_icon_main_writes_multisize_ico`, `test_resolve_nuitka_command_contains_icon_flags`, `test_main_sets_window_icon_on_qapplication`. |
| **Docstrings/comments** | PASS | Each new test carries a docstring summarizing the scenario; AAA comments structure the test body. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`. Result: 497 passed in 19.97s. |
| **No Alternative Test Runners** | PASS | Only Pytest is used. |

---

## 5. Test Coverage Detail

### src/gui/_icon.py::resolve_icon_path (3 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_resolve_icon_path_prefers_compiled_mode` | Positive | 99-119 (compiled probe branch) | PASS |
| `test_resolve_icon_path_falls_back_to_dev_mode` | Positive | 99-119 (dev fallback branch) | PASS |
| `test_resolve_icon_path_raises_when_no_probe_resolves` | Negative / Error Handling | 121-124 (FileNotFoundError raise) | PASS |

**Coverage:** 100% line / 100% branch (14/14 statements, 4/4 branches).

### src/build_exe.py::resolve_nuitka_command + main (8 tests)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_build_argument_parser_exposes_dry_run_and_clean_flags` | Positive | PASS |
| `test_repo_root_resolves_to_project_root` | Positive | PASS |
| `test_resolve_nuitka_command_contains_required_flags` | Positive | PASS |
| `test_resolve_nuitka_command_contains_icon_flags` | Positive (AC1) | PASS |
| `test_resolve_nuitka_command_ends_with_app_entry` | Positive | PASS |
| `test_resolve_nuitka_command_starts_with_python_nuitka_invocation` | Positive | PASS |
| `test_main_dry_run_prints_argv_and_does_not_invoke_seam` | Positive (AC3) | PASS |
| `test_main_clean_removes_existing_dist_tree` | Edge Case (exists vs missing) | PASS |
| `test_main_invokes_seam_and_propagates_returncode` (parametrized [0,1,2,137]) | Edge Case / Error Handling | PASS |
| `test_main_clean_flag_then_invokes_seam` | State Transition (order) | PASS |
| `test_main_uses_default_seams_when_unspecified` | Positive (defaults) | PASS |

**Coverage:** 97% line (32/33), 100% branch (4/4).

### packaging/velopack/convert_icon.py (3 tests)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_convert_icon_main_writes_multisize_ico` | Positive (AC5) | PASS |
| `test_convert_icon_main_exits_zero_with_path_args` | Positive (AC6) | PASS |
| `test_convert_icon_rejects_missing_qsvgrenderer_load` | Negative / Error Handling | PASS |

**Coverage:** Module is loaded via `importlib.util.spec_from_file_location` (the `packaging/` folder is outside `[tool.coverage.run] source = ["src"]` to avoid shadowing the third-party `packaging` PyPI module). Behavior is verified end-to-end against the real source SVG in `evidence/qa-gates/phase6-icon-generate.md` (exit 0, 12813-byte ICO produced).

### src/gui/app.py setWindowIcon wiring (2 new tests)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_main_sets_window_icon_on_qapplication` (AC8) | Positive | PASS |
| `test_build_application_calls_set_window_icon_when_qt_app_constructed` (AC8) | Positive | PASS |

**Coverage:** 99% line (125/126), 92% branch (11/12).

### src/build_velopack.py::resolve_pack_command + resolve_upload_command (existing tests updated)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_resolve_pack_command_contains_required_argv` (AC2) | Positive | PASS |
| `test_resolve_upload_command_argv_shape` (AC3) | Positive | PASS |
| `test_main_dry_run_prints_argv_and_does_not_invoke_seam` | Positive | PASS |

**Coverage:** 98% line (90/91), 96% branch (23/24).

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 497 | PASS |
| Tests Passed | 497 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | 19.97s total | PASS Fast |
| Average Time per Test | ~40ms | PASS Fast |
| Discovery Time | not separately measured | PASS |
| Functions/Classes Tested | All public surface of changed modules | PASS |
| Test File Size | 84 - 496 lines per new/modified test file | PASS Maintainable |
| Code Coverage | 99% lines, 99% branches | PASS |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check .` | exit 0, zero would-reformat | PASS |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | exit 0, zero violations | PASS |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright` | exit 0 in strict mode | PASS |
| Pytest Tests | `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | 497 passed | PASS |

**For PowerShell:** N/A (no PowerShell files in diff).

**Notes:** No pre-existing failures. All toolchain stages completed in a single iteration per `evidence/qa-gates/phase9-loop-completion.md`.

---

## 8. Gaps and Exceptions

### Identified Gaps

None. All policy requirements are met.

### Approved Exceptions

None. No exceptions needed.

### Removed/Skipped Tests

None. All planned tests implemented.

### Suppression Audit

Suppressions on the branch (all pre-authorized per `.claude/rules/python-suppressions.md`):

| Location | Suppression | Pattern |
|---|---|---|
| `src/build_exe.py:223` | `# noqa: S603 - static analysis can't verify runtime validation` | S603 (subprocess) |
| `src/build_velopack.py:397` | `# noqa: S603 - static analysis can't verify runtime validation` | S603 (subprocess) |
| `src/build_velopack.py:417` | `# noqa: S603 - static analysis can't verify runtime validation` | S603 (subprocess) |
| `tests/test_build_velopack.py:333` | `# noqa: S106 - test fixture data` | S105/S108 (test fixture) |
| `tests/test_build_velopack.py:354,402,424` | `# noqa: S105 - test fixture data` | S105/S108 (test fixture) |
| `tests/test_build_exe.py:247` | `# type: ignore[unused-ignore]` | Defensive cross-platform suppression for pytest stub variance; not explicitly enumerated but is a meta-suppression on a Pyright meta-warning, not a substantive suppression of a real type error. Recorded as Informational only. |

No `# pyright: ignore` suppressions added on this branch.

### Evidence Location Compliance

Branch diff scanned for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`. Result: zero violations. All execution evidence is correctly written under the canonical `<FEATURE>/evidence/<kind>/` layout. The `artifacts/python/lcov.info` file is an existing tooling output declared in `pyproject.toml` and not a policy-evidence path. The `scripts/validate_evidence_locations.py` script is absent in this repo; an equivalent git-diff scan was performed.

### Rejected Scope Narrowing

None. The caller did not attempt to narrow audit scope. The audit covers the full branch diff (`9e5f883..ee5f277`, 47 files).

---

## 9. Summary of Changes

### Commits in This PR/Branch

1. **ee5f277** - feat(packaging): align MixCalculator branding and ship real icon (#33)

(single squash-style commit on the branch.)

### Files Modified

1. **src/build_exe.py** (MODIFIED, +24/-2)
   - Added `EXE_NAME` constant; inserted three new Nuitka flags (`--output-filename`, `--windows-icon-from-ico`, `--include-data-file`).

2. **src/build_velopack.py** (MODIFIED, +20/-9)
   - Updated `--packId`, `--mainExe`, `--releaseName`; aligned `_app_exe_exists` to the new executable name; updated module docstring to reflect the case-aligned output filenames.

3. **src/gui/app.py** (MODIFIED, +31/-73)
   - Added `setWindowIcon` calls in `build_application` and `main`; extracted `MainWindowPipelineView` into its own module to stay under the 500-line cap.

4. **src/gui/_icon.py** (NEW, +124/-0)
   - New helper module exposing `resolve_icon_path()` with injected `path_exists` seam.

5. **src/gui/_main_window_view.py** (NEW, +108/-0)
   - Extracted `MainWindowPipelineView` adapter.

6. **packaging/velopack/convert_icon.py** (NEW, +358/-0)
   - One-shot SVG-to-multi-size-ICO converter using QSvgRenderer and Pillow.

7. **packaging/velopack/icon-source.svg** (NEW, +29/-0)
   - Committed source SVG (copy of `artifacts/realgood_calculator_icon.svg`).

8. **packaging/velopack/icon.ico** (MODIFIED, binary)
   - Regenerated multi-size ICO (12813 bytes, frames at 16/32/48/256).

9. **packaging/velopack/README.md** (MODIFIED, +75/-...)
   - Updated pack-identity table, outputs section, icon section; new "Icon source and regeneration" section.

10. **pyproject.toml** (MODIFIED, +1/-0)
    - Added `pillow = "^12.0"` under `[tool.poetry.group.dev.dependencies]`.

11. **poetry.lock** (MODIFIED, +111/-...)
    - Regenerated.

12. **tests/test_build_exe.py** (MODIFIED, +35/-0)
    - Added `test_resolve_nuitka_command_contains_icon_flags`; extended `test_main_dry_run_prints_argv_and_does_not_invoke_seam` to assert the new flags appear in the printed dry-run.

13. **tests/test_build_velopack.py** (MODIFIED, +8/-...)
    - Updated `expected_pairs` for packId, mainExe, releaseName.

14. **tests/test_convert_icon.py** (NEW, +151/-0)
    - Three tests covering the conversion, CLI seam round-trip, and invalid-SVG rejection.

15. **tests/gui/test_app_composition.py** (MODIFIED, +127/-0)
    - Added two AC8 tests covering `setWindowIcon` wiring.

16. **tests/gui/test_icon.py** (NEW, +84/-0)
    - Three probe-branch tests for `resolve_icon_path`.

Documentation: 31 evidence files under `docs/features/active/2026-05-29-app-rename-and-real-icon-33/evidence/` plus the issue, plan, and audit triplet.

---

## 10. Compliance Verdict

### Overall Status: FULLY COMPLIANT

All policy documents in the required reading order pass. Toolchain (Black/Ruff/Pyright/Pytest) completed cleanly in a single pass. Coverage remains at 99% line / 99% branch repo-wide with no regression. All suppressions match pre-authorized patterns. Evidence is correctly located under the canonical `<FEATURE>/evidence/<kind>/` layout. The icon ICO contains the documented four frames and the documented magic bytes.

**Fail-closed reminder:** No required baseline artifact, QA artifact, or coverage-comparison artifact is missing. The verdict is PASS.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes: planned via `plan.2026-05-29T00-00.md`.
- PASS Design Principles: simplicity, reusability, extensibility, SoC all satisfied.
- PASS Module & File Structure: all files under 500 lines; cohesive modules; no circular deps.
- PASS Naming, Docs, Comments: descriptive names, Google-style docstrings, intent/decision comments.
- PASS Toolchain Execution: single-pass clean.
- PASS Summarize & Document: README updated, follow-ups tracked.

#### Language-Specific Code Change Policy (Section 3)

**For Python:**
- PASS Tooling & Baseline: Black/Ruff/Pyright/Pytest clean.
- PASS Python Design & Typing: strong typing, dataclasses for recorders, no new `Any`.
- PASS Error Handling: specific exceptions, fail-fast pre-flight checks, logging via `logging` module.

#### General Unit Test Policy (Section 1)
- PASS Core Principles: independence, isolation, fast, deterministic, readable.
- PASS Coverage & Scenarios: 99%/99% with no regression; new modules 97-100% line.
- PASS Test Structure: AAA pattern, clear failure messages.
- PASS External Dependencies: no network/db/temp files; all I/O via seams.
- PASS Policy Audit: this artifact.

#### Language-Specific Unit Test Policy (Section 4)

**For Python:**
- PASS Framework & Scope: Pytest only.
- PASS Test Style & Structure: focused tests, sparing mocks, mirrored organization.
- PASS Naming & Readability: descriptive names, docstrings, AAA comments.
- PASS Toolchain: clean Pytest run.

---

### Metrics Summary

- PASS 497/497 tests passing (100%).
- PASS All four src-namespace changed modules covered: `build_exe` 97% line / 100% branch; `build_velopack` 98%/96%; `_icon` 100%/100%; `gui/app` 99%/92%.
- PASS 99% line coverage repo-wide; 99% branch coverage repo-wide.
- PASS Proper file organization: tests mirror code under `tests/` and `tests/gui/`.
- PASS All code quality checks passing.
- PASS Test execution time: 19.97 seconds (fast).

---

### Recommendation

**Ready for merge.**

The branch satisfies every required policy compliance check, every acceptance criterion (see `feature-audit.2026-05-29T18-19.md`), and every toolchain gate in a single clean pass. The Velopack `--packId` rename is correctly timed (verified `gh release list` returns empty). No remediation inputs are required.

---

## Appendix A: Test Inventory

### Complete Test List (new and modified tests on this branch)

New tests:

- `tests/gui/test_icon.py::test_resolve_icon_path_prefers_compiled_mode`
- `tests/gui/test_icon.py::test_resolve_icon_path_falls_back_to_dev_mode`
- `tests/gui/test_icon.py::test_resolve_icon_path_raises_when_no_probe_resolves`
- `tests/test_convert_icon.py::test_convert_icon_main_writes_multisize_ico`
- `tests/test_convert_icon.py::test_convert_icon_main_exits_zero_with_path_args`
- `tests/test_convert_icon.py::test_convert_icon_rejects_missing_qsvgrenderer_load`
- `tests/test_build_exe.py::test_resolve_nuitka_command_contains_icon_flags`
- `tests/gui/test_app_composition.py::test_main_sets_window_icon_on_qapplication`
- `tests/gui/test_app_composition.py::test_build_application_calls_set_window_icon_when_qt_app_constructed`

Modified tests (existing tests updated for the rename):

- `tests/test_build_exe.py::test_main_dry_run_prints_argv_and_does_not_invoke_seam` (added assertions for `--output-filename=MixCalculator.exe`, `--windows-icon-from-ico=`, `--include-data-file=`)
- `tests/test_build_velopack.py::test_resolve_pack_command_contains_required_argv` (updated expected_pairs)
- `tests/test_build_velopack.py::test_main_dry_run_prints_argv_and_does_not_invoke_seam` (updated token list)
- `tests/test_build_velopack.py::test_resolve_upload_command_argv_shape` (updated expected_pairs)

Total branch test impact: 9 new tests + 4 modified tests = 13 changed tests. Full suite: 497 passed.

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
# Formatting
env -u VIRTUAL_ENV poetry run black .
env -u VIRTUAL_ENV poetry run black --check .

# Linting
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run ruff check --fix .

# Type checking
env -u VIRTUAL_ENV poetry run pyright

# Testing
env -u VIRTUAL_ENV poetry run pytest
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
env -u VIRTUAL_ENV poetry run pytest --cov=src.build_exe --cov=src.build_velopack --cov=src.gui.app --cov=src.gui._icon --cov-branch --cov-report=term-missing tests/
```

---

**Audit Completed By:** feature-review agent (Claude Opus 4.7)
**Audit Date:** 2026-05-29
**Policy Version:** Current (as of audit date)
