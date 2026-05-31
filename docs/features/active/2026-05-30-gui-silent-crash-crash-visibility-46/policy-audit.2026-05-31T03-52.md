# Policy Audit — gui-silent-crash-crash-visibility (Issue #46) — Reaudit Cycle 2

- **Timestamp:** 2026-05-31T03-52
- **Issue:** #46
- **Base branch:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Branch head:** `bug/gui-silent-crash-crash-visibility-46` @ `b59bb3660ce9fa510a450d326f92ffd46a1776aa`
- **Prior audits:** `policy-audit.2026-05-31T02-43.md` (Cycle 0), `policy-audit.2026-05-31T03-25.md` (Cycle 1)
- **Cycle-2 remediation inputs:** `remediation-inputs.2026-05-31T03-25.md` (single Blocking item: R5)
- **Cycle-2 remediation plan:** `remediation-plan.2026-05-31T03-25.md`
- **Work mode:** full-bug (AC source: `spec.md`)
- **Scope:** Full branch diff vs base. No caller-supplied scope narrowing was applied.

## Coverage Metrics by Language

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 10 files (5 production, 5 test) | 737 tests collected | PASS — 737 pass, 0 fail | 99.5% lines, 96.5% branches (cycle-1 post-state) | 99.5% lines, 96.5% branches | 100% line / 100% branch on `_crash_handler.py`; 100% on `_crash_handler_bootstrap.py`; 100% on `runners.py`; 100% on `pipeline_worker.py`; 99% line on `app.py` |
| TypeScript | 0 files | N/A | N/A | N/A (out of scope) | N/A (out of scope) | N/A |
| PowerShell | 0 files | N/A | N/A | N/A (out of scope) | N/A (out of scope) | N/A |
| C# | 0 files | N/A | N/A | N/A (out of scope) | N/A (out of scope) | N/A |

## Coverage Evidence Checklist

- Python baseline coverage artifact: `artifacts/python/lcov.info` (pre-existing; aggregated by the cycle-2 pytest run).
- Python post-change coverage artifact: `artifacts/python/lcov.info` + `evidence/qa-gates/phase8/pytest.md`.
- TypeScript baseline coverage artifact: `N/A - out of scope` (no `.ts/.tsx` files changed on this branch).
- TypeScript post-change coverage artifact: `N/A - out of scope` (no `.ts/.tsx` files changed on this branch).
- PowerShell baseline coverage artifact: `N/A - out of scope` (no `.ps1/.psm1` files changed on this branch).
- PowerShell post-change coverage artifact: `N/A - out of scope` (no `.ps1/.psm1` files changed on this branch).
- C# baseline coverage artifact: `N/A - out of scope` (no `.cs/.csproj` files changed on this branch).
- C# post-change coverage artifact: `N/A - out of scope` (no `.cs/.csproj` files changed on this branch).
- Per-language comparison summary: see "Coverage Verification (Python)" section below.

## Executive Summary

The cycle-2 R5 remediation cleared the sole Blocking finding from cycle 1. All cycle-0 carryover findings (F1-F4) and the cycle-1 finding (F5) are now CLEARED. The full Python toolchain passes single-pass (black, ruff, pyright, pytest at 737/737). `src/gui/_crash_handler.py` line/branch coverage is 100%/100% (verified against `artifacts/python/lcov.info`); repo-wide Python coverage is 99.5% line / 96.5% branch. No new suppression markers (`# noqa`, `# type: ignore`, `# pyright: ignore`) were introduced on the branch. `pyproject.toml` and `poetry.lock` are unchanged. All ten changed `.py` files (5 production + 5 test) are under the 500-line cap defined in `.claude/rules/general-code-change.md`, including `tests/gui/test_crash_handler.py` (332 lines, down from 549) and the new sibling `tests/gui/test_crash_handler_closures.py` (258 lines). Scope was the full branch diff against base `0b353ad`; no caller-supplied scope narrowing was applied. Final policy verdict: **PASS**.

## Policy Reading Order

1. `CLAUDE.md` (standing instructions)
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/python.md`
5. `.claude/rules/python-suppressions.md`
6. `.claude/rules/quality-tiers.md`
7. `.claude/rules/self-explanatory-code-commenting.md`
8. `.claude/rules/tonality.md`
9. `.claude/rules/benchmark-baselines.md` (not in scope; no benchmark/baseline files touched)
10. `.claude/rules/ci-workflows.md` (not in scope; no `.github/workflows/**` files touched)

## Languages in Scope (Branch Diff)

| Language | Changed files? | Coverage artifact required | Notes |
|---|---|---|---|
| Python | Yes (5 production, 5 test) | `artifacts/python/lcov.info` + per-file term-missing in `evidence/qa-gates/phase8/pytest.md` | In scope |
| TypeScript | No | N/A | No `.ts/.tsx` files changed |
| PowerShell | No | N/A | No `.ps1/.psm1` files changed |
| C# | No | N/A | No `.cs/.csproj` files changed |

Changed `.py` files (10):

- `src/gui/_crash_handler.py` (NEW; 495 lines)
- `src/gui/_crash_handler_bootstrap.py` (NEW in R1; 94 lines)
- `src/gui/app.py` (modified; 499 lines)
- `src/gui/runners.py` (modified; 270 lines)
- `src/gui/workers/pipeline_worker.py` (modified; 116 lines)
- `tests/gui/test_app_composition.py` (modified; 480 lines)
- `tests/gui/test_crash_handler.py` (NEW; 332 lines post-R5 split)
- `tests/gui/test_crash_handler_closures.py` (NEW in R5; 258 lines)
- `tests/gui/test_pipeline_worker.py` (modified; 244 lines)
- `tests/gui/test_runners_threaded.py` (NEW; 151 lines)

## 1. General Unit Test Policy Compliance

This audit evaluates the test suite against `.claude/rules/general-unit-test.md`. Findings are summarized below; detailed coverage metrics are in section 5 and verdicts are recorded in the per-finding table.

- **Independence:** PASS. Tests run in any order under pytest default collection; phase-4 single-pass evidence confirms 737/737 pass with no intra-test state leakage.
- **Isolation:** PASS. Each test targets one behavior. The R5 split moved closure-direct-invocation tests into their own module so the installer-contract surface is exercised separately from the on-disk write closures.
- **Fast execution:** PASS. Phase-4 pytest evidence reports `22.62s` total wall time for 737 tests.
- **Determinism:** PASS. The relocated closure tests continue to use the in-memory `BytesIO` sink via `_FakePath`/`_FakeHandle` and the `vars(crash_handler)[name]` private-symbol access pattern. No temporary files. No real I/O. No randomness.
- **Readability and maintainability:** PASS. Module docstrings in both test files document purpose, responsibilities, and the no-temp-files determinism note.
- **Coverage thresholds (>= 85% line, >= 75% branch repo-wide and on changed files):** PASS. Detail in section 5 and in "Coverage Verification (Python)" below.
- **No temporary files in tests:** PASS. Both new test files use in-memory `BytesIO` sinks; no real disk I/O.

## 2. General Code Change Policy Compliance

- **Simplicity first:** PASS. R5 is a pure relocation; no new abstraction, no helper module, no class hierarchy added.
- **File-size limit (<= 500 lines for production code, test code, and reusable scripts):** PASS. See the File-Size Compliance Table below. All ten branch-touched `.py` files are under the cap.
- **Toolchain loop (format, lint, type-check, test):** PASS single-pass per `evidence/qa-gates/phase4/single-pass-summary.md`. One intermediate ruff TC002/TC003 finding during R5 authoring was fixed by moving `pytest` and `pathlib.Path` into the `TYPE_CHECKING` block of the new closures file (resolution per `python-suppressions.md` workaround; no suppression added). After the fix, every stage in a single iteration returned EXIT_CODE 0 without modifying any file mid-loop.
- **Error handling and logging:** PASS. The cycle-0/cycle-1 widening of the `pipeline_worker.py` boundary to `except BaseException` (with explicit re-raise of `KeyboardInterrupt`/`SystemExit`) plus `logger.error(..., exc_info=True)` is unchanged in cycle 2.
- **Public-API stability:** PASS. No public-API change in cycle 2 (R5 modifies tests only).
- **Dependencies:** PASS. `pyproject.toml` and `poetry.lock` are unchanged across the full branch diff (verified).
- **I/O boundaries / no temp files in tests:** PASS. The relocated closure tests use `_FakePath`/`_FakeHandle` with `BytesIO` sinks; no `tempfile` import; no disk I/O.

## 3. Language-Specific Code Change Policy Compliance

### 3A. Python (`.claude/rules/python.md` + `.claude/rules/python-suppressions.md`)

- **Black formatting:** PASS — `evidence/qa-gates/phase4/black.md` EXIT_CODE 0; 175 files unchanged.
- **Ruff lint:** PASS — `evidence/qa-gates/phase4/ruff.md` EXIT_CODE 0.
- **Pyright type-check:** PASS — `evidence/qa-gates/phase4/pyright.md` EXIT_CODE 0; 0 errors / 0 warnings / 0 informations.
- **Pytest:** PASS — `evidence/qa-gates/phase4/pytest.md` EXIT_CODE 0; 737 passed.
- **PEP 8 naming, strong typing, absolute imports, no bare `except`:** PASS — confirmed by Pyright and ruff cleans, plus `grep -nE 'except\s*:' src/gui/_crash_handler.py src/gui/_crash_handler_bootstrap.py src/gui/runners.py src/gui/workers/pipeline_worker.py src/gui/app.py` returns no matches.
- **Suppression policy:** PASS — no new `# noqa`, `# type: ignore`, or `# pyright: ignore` markers anywhere in the branch diff. The R5 split preserved the cycle-1 `vars(crash_handler)[name]` private-symbol access pattern that avoids the need for `# pyright: ignore` and `# noqa: B009`. See "Suppression Audit (Python)" below.

### 3B-3D. TypeScript / PowerShell / C#

Not applicable on this branch (no files changed in those languages).

## 4. Language-Specific Unit Test Policy Compliance

### 4A. Python (`.claude/rules/python.md` pytest rules)

- **Pytest as the only runner:** PASS — only `poetry run pytest` is used.
- **One behavior per test:** PASS — each test name (e.g., `test_install_crash_handlers_installs_all_four_hooks`, `test_sys_excepthook_appends_traceback_record`) describes a single behavior.
- **AAA structure:** PASS — each test has explicit arrange/act/assert sections; the three relocated R4 tests preserve the cycle-1 AAA shape.
- **Parametrize over boundaries:** PASS — `test_resolve_log_dir_branches` uses `pytest.mark.parametrize` over Windows/Darwin/Linux branches with and without environment overrides.
- **Patch at import location:** PASS — `tests/gui/test_app_composition.py` patches `src.gui.app.install_crash_handlers` at the use site to verify the single-call contract.
- **No temp files, no sleeps, no real network:** PASS — confirmed for both test files.
- **Coverage:** PASS — section 5 details.

### 4B-4D. PowerShell / Bash / JSON tests

Not applicable on this branch.

## 5. Test Coverage Detail

Coverage metrics are sourced from `artifacts/python/lcov.info` and `evidence/qa-gates/phase8/pytest.md`. Per-file LF/LH/BRF/BRH values are quoted directly from the lcov record (`SF:` block aggregation).

### Per-file coverage (changed files in branch diff)

| File | LF | LH | Line % | BRF | BRH | Branch % | New-code threshold | Disposition |
|---|---|---|---|---|---|---|---|---|
| `src/gui/_crash_handler.py` (NEW) | 99 | 99 | 100.0% | 8 | 8 | 100.0% | >= 85% line / >= 75% branch | PASS |
| `src/gui/_crash_handler_bootstrap.py` (NEW in R1) | 6 | 6 | 100.0% | 0 | 0 | n/a | >= 85% line | PASS |
| `src/gui/runners.py` (modified) | 46 | 46 | 100.0% | 0 | 0 | n/a | no regression on changed lines | PASS (improved from 66% to 100%) |
| `src/gui/workers/pipeline_worker.py` (modified) | 24 | 24 | 100.0% | 2 | 2 | 100.0% | no regression on changed lines | PASS |
| `src/gui/app.py` (modified) | 137 | 136 | 99.3% | 12 | 11 | 91.7% | no regression on changed lines | PASS (missed line is at unchanged line 314) |

### Repo-wide rollup (Python)

| Metric | Value | Threshold | Disposition |
|---|---|---|---|
| Line coverage | 3636 / 3656 = **99.5%** | >= 85% | PASS |
| Branch coverage | 637 / 660 = **96.5%** | >= 75% | PASS |

### Test execution summary

| Metric | Value |
|---|---|
| Total tests collected | 737 |
| Tests passed | 737 (100%) |
| Tests failed | 0 |
| Warnings | 1 (1 deprecation warning unchanged versus cycle-1 post-state) |
| Wall time | 22.62s |
| Relocated R4 tests collected from new file | 3 (`test_sys_excepthook_appends_traceback_record`, `test_threading_excepthook_appends_traceback_record`, `test_append_traceback_swallows_oserror`) |

## 6. Test Execution Metrics

| Metric | Value | Disposition |
|---|---|---|
| Total Tests | 737 | PASS |
| Tests Passed | 737 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | 22.62s | PASS (fast) |
| Average Time per Test | ~30.7ms | PASS (fast) |
| Test files in cycle-2 scope | 5 | n/a |
| Largest test file | `tests/gui/test_app_composition.py` (480 lines) | PASS (under cap) |
| Largest production file | `src/gui/app.py` (499 lines) | PASS (under cap) |
| Repo-wide line coverage | 99.5% | PASS |
| Repo-wide branch coverage | 96.5% | PASS |

## 7. Code Quality Checks

| Check | Command | EXIT_CODE | Disposition |
|---|---|---|---|
| Black formatting | `poetry run black --check .` | 0 | PASS |
| Ruff linting | `poetry run ruff check .` | 0 | PASS |
| Pyright type checking | `poetry run pyright` | 0 | PASS |
| Pytest with coverage | `poetry run pytest --cov --cov-branch --cov-report=term-missing` | 0 | PASS |
| Single-pass attestation | `evidence/qa-gates/phase4/single-pass-summary.md` (`Single-Pass Result: PASS`) | n/a | PASS |
| Suppression-marker scan | `git diff 0b353ad..b59bb36 -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'` | 1 (no matches) | PASS |
| Dependency-diff scan | `git diff --name-only 0b353ad..b59bb36 -- pyproject.toml poetry.lock` | 0 (empty output) | PASS |
| Evidence-location scan | `git diff --diff-filter=AM --name-only 0b353ad..b59bb36 | grep -E "^artifacts/(baselines|qa|evidence|coverage)/"` | 1 (no matches) | PASS |

## Cycle-2 Remediation — Status of R5

The R5 definition-of-done has nine independent verification items. Each item is verified directly against branch HEAD `b59bb36`; all nine are CLEARED.

1. R5 item (`tests/gui/test_crash_handler.py` <= 500 lines) — `wc -l` returned 332; `awk 'END{print NR}'` returned 332 — CLEARED.
2. R5 item (`tests/gui/test_crash_handler_closures.py` exists and <= 500 lines) — `wc -l` returned 258; `awk 'END{print NR}'` returned 258 — CLEARED.
3. R5 item (`_FakePath` / `_FakeHandle` fixture pair present in new file) — `grep -nE "^class _Fake" tests/gui/test_crash_handler_closures.py` returned lines 55 and 97 — CLEARED.
4. R5 item (three R4 closure tests present in new file) — `grep -nE "^def test_(sys_excepthook_appends_traceback_record|threading_excepthook_appends_traceback_record|append_traceback_swallows_oserror)" tests/gui/test_crash_handler_closures.py` returned lines 144, 182, 220 — CLEARED.
5. R5 item (closure tests removed from original file) — `grep -nE "_Fake\|test_sys_excepthook_appends\|test_threading_excepthook_appends\|test_append_traceback_swallows_oserror" tests/gui/test_crash_handler.py` returned 0 matches — CLEARED.
6. R5 item (`_crash_handler.py` coverage at or above cycle-1 post-fix state, line >= 88%, branch >= 75%) — phase-8 pytest evidence and lcov agree on 99/99 lines (100%) and 8/8 branches (100%); cycle-1 post-fix state was also 100%/100% — CLEARED.
7. R5 item (no new suppression markers added across the diff) — `git diff 0b353ad..b59bb36 -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'` returned EXIT_CODE 1 with no matches — CLEARED.
8. R5 item (all 737 tests pass) — phase-8 `pytest.md` reports `737 passed`, EXIT_CODE 0 — CLEARED.
9. R5 item (single-pass toolchain green) — phase-4 `single-pass-summary.md` records `Single-Pass Result: PASS` with EXIT_CODE 0 from black, ruff, pyright, and pytest in the same loop iteration — CLEARED.

R5 (the only Blocking item carried over from cycle 1) is cleared on its full definition of done. No new findings were introduced by the split.

## Per-Finding Verdict Summary

| Finding | Severity | Verdict |
|---|---|---|
| F5 (cycle-1 carryover): `tests/gui/test_crash_handler.py` exceeds 500-line cap | Blocking | **CLEARED** (now 332 lines; closures relocated to new sibling file) |
| F1 (cycle-0 carryover): `src/gui/app.py` exceeds 500-line cap | Blocking | **CLEARED** (now 499 lines) |
| F2 (cycle-0 carryover): spec/code symbol drift `_resolve_log_dir` vs `resolve_log_dir` | PARTIAL | **CLEARED** (spec AC-1 uses `resolve_log_dir`) |
| F3 (cycle-0 carryover): phase4 file-sizes evidence undercount | PARTIAL | **CLEARED** (phase4 regenerated; phase8 expanded post-R5 to include all four test files) |
| F4 (cycle-0 carryover): closure-body coverage gap in `_crash_handler.py` | PARTIAL | **CLEARED** (100% line / 100% branch) |

No new findings at cycle 2.

## Suppression Audit (Python)

- **Command:** `git diff 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'`
- **Result:** Zero matches across the entire branch diff (EXIT_CODE 1 from `grep`). The relocated closure tests in `tests/gui/test_crash_handler_closures.py` continue to access private symbols via `vars(crash_handler)[name]`, so no `# pyright: ignore` or `# noqa: B009` was introduced by the split.
- Verdict: **PASS** — `python-suppressions.md` policy holds; no new `# noqa`, `# type: ignore`, or `# pyright: ignore` markers were added by R5 or by any earlier cycle.

## Toolchain Loop Verification (Python)

| Stage | Phase 4 evidence (cycle-2 single-pass) | Phase 8 evidence | EXIT_CODE | Verdict |
|---|---|---|---|---|
| 1. Format (black --check) | `evidence/qa-gates/phase4/black.md` | `evidence/qa-gates/phase8/black.md` | 0 | PASS |
| 2. Lint (ruff check) | `evidence/qa-gates/phase4/ruff.md` | `evidence/qa-gates/phase8/ruff.md` | 0 | PASS |
| 3. Type check (pyright) | `evidence/qa-gates/phase4/pyright.md` | `evidence/qa-gates/phase8/pyright.md` | 0 | PASS |
| 4. Architecture-boundary tests | Not separately gated in this repo; covered by unit tests | n/a | n/a | N/A |
| 5. Unit tests + coverage (pytest) | `evidence/qa-gates/phase4/pytest.md` | `evidence/qa-gates/phase8/pytest.md` | 0; 737 passed | PASS |
| 6. Contract / schema compat | No schema/contract surface touched | n/a | n/a | N/A |
| 7. Integration tests | Covered by pytest-qt cases in unit suite | included in phase 8 pytest | 0 | PASS |
| Single-pass attestation | `evidence/qa-gates/phase4/single-pass-summary.md` (`Single-Pass Result: PASS`) | `evidence/qa-gates/phase8/single-pass-summary.md` | all 0 | PASS |

Toolchain-loop verdict: **PASS** — all four mandatory Python stages green in a single pass at cycle-2 exit. The phase-4 summary notes one intermediate ruff TC002/TC003 failure during R5 authoring that was fixed (moving `pytest` and `pathlib.Path` into the `TYPE_CHECKING` block of `tests/gui/test_crash_handler_closures.py`); the four EXIT_CODE 0 values come from the same green loop iteration after that fix.

## Coverage Verification (Python)

Coverage verification uses the pre-existing artifacts at `artifacts/python/lcov.info` and `evidence/qa-gates/phase8/pytest.md`. Coverage was not regenerated by this reaudit.

### Per-File Coverage Comparison (Baseline vs Post-Change, Disposition)

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.5% line / 96.5% branch (cycle-1 post-state). Post-change: 99.5% line / 96.5% branch. Change: 0.0% line / 0.0% branch (invariant; the R5 split moved tests between files but did not alter execution coverage). New/changed-code coverage: 100% line / 100% branch on `src/gui/_crash_handler.py` (LF=99 LH=99 BRF=8 BRH=8), 100% on `src/gui/_crash_handler_bootstrap.py`, 100% on `src/gui/runners.py`, 100% on `src/gui/workers/pipeline_worker.py`, 99.3% line / 91.7% branch on `src/gui/app.py`. Disposition: PASS. Evidence: `artifacts/python/lcov.info`; `evidence/qa-gates/phase8/pytest.md`.
- TypeScript: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (no `.ts/.tsx` files changed in branch diff).
- PowerShell: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (no `.ps1/.psm1` files changed in branch diff).
- C#: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (no `.cs/.csproj` files changed in branch diff).

#### Per-file Python coverage rows

- **src/gui/_crash_handler.py** (new file)
  - Baseline: n/a (file did not exist)
  - Post-change: 100% line (99/99), 100% branch (8/8) — verified against `artifacts/python/lcov.info`
  - Change: +99 statements, +8 branches, 0 missed lines
  - New/changed-code coverage: 100% line (>= 85%), 100% branch (>= 75%)
  - Disposition: PASS (cycle-1 post-R4 state preserved through the R5 split)
  - Evidence: `evidence/qa-gates/phase8/pytest.md` per-file table; `artifacts/python/lcov.info` SF record for `src\gui\_crash_handler.py` LF=99 LH=99 BRF=8 BRH=8.

- **src/gui/_crash_handler_bootstrap.py** (new file from R1)
  - Baseline: n/a (file did not exist)
  - Post-change: 100% line (6/6), 0 branches
  - Change: +6 statements, 0 branches
  - New/changed-code coverage: 100% line (>= 85%)
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase8/pytest.md`; `artifacts/python/lcov.info` SF=`src\gui\_crash_handler_bootstrap.py` LF=6 LH=6.

- **src/gui/runners.py** (modified)
  - Baseline: 66% line, 0 branches (pre-feature head)
  - Post-change: 100% line (46/46), 100% branch (0/0)
  - Change: +14 statements; coverage rose from 66% to 100%
  - New/changed-code coverage: 100% line (>= 85%)
  - Disposition: PASS (improvement; no regression)
  - Evidence: `evidence/qa-gates/phase8/pytest.md`; `artifacts/python/lcov.info` SF=`src\gui\runners.py` LF=46 LH=46.

- **src/gui/workers/pipeline_worker.py** (modified)
  - Baseline: 100% line, 0 branches (pre-feature head)
  - Post-change: 100% line (24/24), 100% branch (2/2)
  - Change: +2 statements (BaseException widening + re-raise); +2 branches covered
  - New/changed-code coverage: 100% line (>= 85%), 100% branch (>= 75%)
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase8/pytest.md`; `artifacts/python/lcov.info` SF=`src\gui\workers\pipeline_worker.py` LF=24 LH=24 BRF=2 BRH=2.

- **src/gui/app.py** (modified)
  - Baseline: 99% line (138 stmts, 1 missed), 92% branch (pre-feature)
  - Post-change: 99% line (137 stmts, 1 missed), 92% branch (11/12)
  - Change: -1 statement (R1 bootstrap extraction); no regression on changed lines (the missed line is at unchanged line 314)
  - New/changed-code coverage: 100% on the installer-call site
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase8/pytest.md`; `artifacts/python/lcov.info` SF=`src\gui\app.py` LF=137 LH=136 BRF=12 BRH=11.

### Repo-Wide Per-Language Coverage

- Python total (lcov rollup): 3636 / 3656 lines (**99.5%**); 637 / 660 branches (**96.5%**). Both above the 85% line / 75% branch policy floors. Disposition: PASS.
- Evidence: `artifacts/python/lcov.info` aggregate; `evidence/qa-gates/phase8/pytest.md` headline coverage (3656 stmts, 20 missed; 660 branches, 23 partial).

### Coverage Checklist (Python)

- [x] Coverage artifact present (`artifacts/python/lcov.info` and per-file term-missing at `evidence/qa-gates/phase8/pytest.md`).
- [x] Repo-wide coverage line >= 85% (99.5%).
- [x] Repo-wide coverage branch >= 75% (96.5%).
- [x] Each new file >= 85% line / >= 75% branch (`_crash_handler.py` 100%/100%; `_crash_handler_bootstrap.py` 100%).
- [x] Each modified file no regression on changed lines (`runners.py` improved; `pipeline_worker.py` unchanged at 100%; `app.py` unchanged at 99%).

### Coverage Checklist (TypeScript)

- [x] No TypeScript files changed on the branch; coverage verification not required for this branch.

### Coverage Checklist (PowerShell)

- [x] No PowerShell files changed on the branch; coverage verification not required for this branch.

### Coverage Checklist (C#)

- [x] No C# files changed on the branch; coverage verification not required for this branch.

## Evidence Location Compliance

- **Scan command:** `git diff --diff-filter=AM --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa | grep -E "^artifacts/(baselines|qa|evidence|coverage)/"`
- **Result:** Empty (EXIT_CODE 1 from `grep`). No files were written to any non-canonical evidence path on this branch. All branch-added evidence lives under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/<kind>/`.
- **Note:** The `validate_evidence_locations.py` script is not present in this repo; the git-diff scan above is the substitute per the persistent agent memory entry `evidence-validator-script-absent`.
- Verdict: **PASS** — evidence-location invariant holds.

## Rejected Scope Narrowing

None. The caller prompt for cycle 2 reaffirmed the scope invariant verbatim ("Scope determination is your responsibility per the skill's scope invariant; do not narrow scope.") and asked for a full feature-vs-base reaudit. No narrowing was attempted by the caller and none was applied.

## Dependency Diff

- Command: `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa -- pyproject.toml poetry.lock`
- Result: empty (no changes). Verdict: **PASS** (AC-11 satisfied across all three cycles).

## File-Size Compliance Table (Authoritative `awk NR` counts at HEAD)

| File | Lines | Under 500-line cap | Notes |
|---|---|---|---|
| src/gui/_crash_handler.py | 495 | Yes (5 lines of headroom) | Unchanged in cycle 2; near cap |
| src/gui/_crash_handler_bootstrap.py | 94 | Yes | New in R1 |
| src/gui/runners.py | 270 | Yes | +114 vs baseline |
| src/gui/workers/pipeline_worker.py | 116 | Yes | +37 vs baseline |
| src/gui/app.py | 499 | Yes (1 line of headroom) | Post-R1 reduction |
| tests/gui/test_app_composition.py | 480 | Yes (20 lines of headroom) | Unchanged in cycle 2 |
| tests/gui/test_crash_handler.py | 332 | Yes (168 lines of headroom) | Post-R5 split (was 549 at cycle-1 head) |
| tests/gui/test_crash_handler_closures.py | 258 | Yes (242 lines of headroom) | NEW in R5 |
| tests/gui/test_pipeline_worker.py | 244 | Yes | +99 vs baseline |
| tests/gui/test_runners_threaded.py | 151 | Yes | New |

All ten production and test files are under the 500-line cap. The cap defined in `.claude/rules/general-code-change.md` (which applies to production code, test code, and reusable scripts) is satisfied across the entire branch diff.

## Final Policy Verdict

**PASS** — zero Blocking findings remain. All cycle-0 carryover findings (F1-F4) and the cycle-1 finding (F5) are cleared. The single-pass Python toolchain is green (black, ruff, pyright, pytest), repo-wide Python coverage is 99.5% line / 96.5% branch (above policy floors), no new suppression markers were added, no dependency files were modified, no evidence-location violations were detected, and no scope narrowing was attempted by the caller.

## 8. Gaps and Exceptions

### Identified Gaps

**None.** All policy requirements are met. The cycle-1 carry-over Blocking finding (F5) was cleared by the cycle-2 R5 split. No new gaps were introduced.

### Approved Exceptions

**None.** No exceptions were requested or approved in this cycle.

### Removed/Skipped Tests

**None.** No tests were removed or skipped. The three R4 closure-invocation tests were relocated verbatim from `tests/gui/test_crash_handler.py` to `tests/gui/test_crash_handler_closures.py`; their assertions, seam (`vars(crash_handler)[name]`), and `BytesIO` sink are unchanged. Total collected test count remained 737 across the split.

## 9. Summary of Changes

### Cycle-2 Commits

1. `b59bb36` — `test(gui): split test_crash_handler.py to restore 500-line cap (#46 cycle 2)`

### Files Modified in Cycle 2

1. **`tests/gui/test_crash_handler.py`** (MODIFIED) — trimmed from 549 to 332 lines by removing the `_FakePath` / `_FakeHandle` fixture pair and the three R4 closure-invocation tests. Top-of-file imports pruned to remove symbols no longer referenced by the retained tests.
2. **`tests/gui/test_crash_handler_closures.py`** (NEW) — 258 lines holding the relocated `_FakePath` / `_FakeHandle` classes and the three R4 closure tests. Module docstring documents purpose, responsibilities, and the no-temp-files determinism note. Imports use `TYPE_CHECKING` for `pytest`, `pathlib.Path`, and `collections.abc.Callable` to satisfy ruff TC002/TC003.
3. **`docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md`** (REGENERATED IN PLACE) — Last Updated 2026-05-31T03-25; results table now includes all five production files plus all five test files; every row shows PASS under the 500-line cap.
4. **`docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pytest.md`** (REGENERATED IN PLACE) — Timestamp 2026-05-31T03-25; `737 passed`; per-file coverage tables show the post-split state.
5. **Phase 0-7 evidence artifacts** (NEW under `evidence/qa-gates/phase0..phase7/`) — baseline, single-pass-summary, AC re-eval, and cross-checks per the cycle-2 plan.
6. **`docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`** (MODIFIED) — AC-12 cycle-2 note added (line 227); `Last Updated: 2026-05-31T03-25`.

### Full-Branch Files Modified (relative to base `0b353ad`)

- **Production (5):** `src/gui/_crash_handler.py` (NEW, 495), `src/gui/_crash_handler_bootstrap.py` (NEW in R1, 94), `src/gui/runners.py` (+92/-15, now 270), `src/gui/workers/pipeline_worker.py` (+19/-5, now 116), `src/gui/app.py` (+8/-2, now 499).
- **Test (5):** `tests/gui/test_crash_handler.py` (NEW; 332 post-R5), `tests/gui/test_crash_handler_closures.py` (NEW in R5; 258), `tests/gui/test_runners_threaded.py` (NEW; 151), `tests/gui/test_pipeline_worker.py` (+99; 244), `tests/gui/test_app_composition.py` (+79; 480).
- **Dependencies:** `pyproject.toml` and `poetry.lock` are unchanged.

## 10. Compliance Verdict

### Overall Status: FULLY COMPLIANT (PASS)

The branch satisfies every applicable policy requirement. Zero Blocking findings remain. All four mandatory Python toolchain stages pass in a single pass. Coverage thresholds are met repo-wide and per changed file. No suppression-policy violations. No dependency churn. No file-size-cap violations. No evidence-location violations. No scope narrowing was applied.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS — Design principles: simplicity-first R5 split, no new abstraction.
- PASS — File-size cap: all 10 changed `.py` files under 500 lines.
- PASS — Toolchain loop: single-pass green per `evidence/qa-gates/phase4/single-pass-summary.md`.
- PASS — Dependencies: no `pyproject.toml` / `poetry.lock` delta.

#### Language-Specific Code Change Policy (Section 3) — Python
- PASS — Black, Ruff, Pyright, Pytest all EXIT_CODE 0.
- PASS — Suppression policy: zero new `# noqa` / `# type: ignore` / `# pyright: ignore` markers across the branch diff.
- PASS — Naming, typing, error handling all conformant.

#### General Unit Test Policy (Section 1)
- PASS — Determinism: `_FakePath`/`_FakeHandle` use `BytesIO`; no temp files.
- PASS — Coverage thresholds met repo-wide (99.5% line, 96.5% branch) and on every changed file.

#### Language-Specific Unit Test Policy (Section 4) — Python
- PASS — Pytest as the sole runner; parametric `resolve_log_dir` tests; AAA structure; patch-at-import-location pattern for `install_crash_handlers` composition-root test.

### Metrics Summary

- 737/737 tests passing (100%)
- 99.5% repo-wide line coverage
- 96.5% repo-wide branch coverage
- 100% line / 100% branch on `src/gui/_crash_handler.py` (cycle-1 R4 state preserved by R5 split)
- All 10 changed `.py` files under the 500-line cap
- Zero new suppression markers
- Zero dependency changes
- Single-pass toolchain green

### Recommendation

**Ready for merge** — the cycle-2 R5 split closes the only outstanding finding from cycle 1 without disturbing any coverage or behavioral invariant. The feature-vs-base diff is policy-clean across all evaluated dimensions.

## Appendix A: Test Inventory

The cycle-2 split changed which file a few tests are collected from but did not change the total inventory.

### `tests/gui/test_crash_handler.py` (10 tests post-R5)

- `test_module_exposes_documented_public_surface`
- `test_resolve_log_dir_branches` (parametric: Windows with/without LOCALAPPDATA, Darwin, Linux with/without XDG_STATE_HOME)
- `test_install_crash_handlers_installs_all_four_hooks`
- `test_install_crash_handlers_disabled_returns_noop`
- `test_install_crash_handlers_is_idempotent`
- `test_qt_message_handler_routes_categories_to_logging_levels`

### `tests/gui/test_crash_handler_closures.py` (3 tests, NEW in R5)

- `test_sys_excepthook_appends_traceback_record`
- `test_threading_excepthook_appends_traceback_record`
- `test_append_traceback_swallows_oserror`

### Other GUI test files in branch diff

- `tests/gui/test_runners_threaded.py` (NEW): thread-affinity probe and queued-connection assertions for `ThreadedRunner.run`.
- `tests/gui/test_pipeline_worker.py` (extended): worker-boundary exception capture, traceback logging, KeyboardInterrupt/SystemExit re-raise pins.
- `tests/gui/test_app_composition.py` (extended): composition-root single-call contract for `install_crash_handlers`.

Total collected from the branch-touched test files: 13 + the existing pipeline/runner/composition tests; total suite-wide: 737.

## Appendix B: Toolchain Commands Reference

```
# Format
poetry run black --check .

# Lint
poetry run ruff check .

# Type-check
poetry run pyright

# Test with coverage
poetry run pytest --cov --cov-branch --cov-report=term-missing

# Line counts (triple-verification)
awk 'END{print NR}' <path>
wc -l <path>
pwsh -NoProfile -Command "(Get-Content <path>).Count"

# Branch-diff scans
git diff 0b353ad..b59bb36 -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'
git diff --name-only 0b353ad..b59bb36 -- pyproject.toml poetry.lock
git diff --diff-filter=AM --name-only 0b353ad..b59bb36 | grep -E "^artifacts/(baselines|qa|evidence|coverage)/"

# Coverage rollup from lcov
python -c "<lcov LF/LH/BRF/BRH aggregator>" artifacts/python/lcov.info
```

## Appendix A — Verification Commands

- `git rev-parse HEAD` -> `b59bb3660ce9fa510a450d326f92ffd46a1776aa`
- `git merge-base main bug/gui-silent-crash-crash-visibility-46` -> `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- `awk 'END{print NR}' src/gui/app.py src/gui/_crash_handler.py src/gui/_crash_handler_bootstrap.py src/gui/runners.py src/gui/workers/pipeline_worker.py`
- `awk 'END{print NR}' tests/gui/test_app_composition.py tests/gui/test_runners_threaded.py tests/gui/test_pipeline_worker.py tests/gui/test_crash_handler.py tests/gui/test_crash_handler_closures.py`
- `wc -l tests/gui/test_crash_handler.py tests/gui/test_crash_handler_closures.py`
- `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa`
- `git diff 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'`
- `git diff --diff-filter=AM --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa | grep -E "^artifacts/(baselines|qa|evidence|coverage)/"`
- `grep -nE 'except\s*:' src/gui/_crash_handler.py src/gui/_crash_handler_bootstrap.py src/gui/runners.py src/gui/workers/pipeline_worker.py src/gui/app.py`
- `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..b59bb3660ce9fa510a450d326f92ffd46a1776aa -- pyproject.toml poetry.lock`
- `python -c "<lcov parser>"` aggregate read of `artifacts/python/lcov.info` (yields LF=3656 LH=3636, BRF=660 BRH=637).
