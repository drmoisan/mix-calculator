# Policy Audit — gui-silent-crash-crash-visibility (Issue #46) — Reaudit Cycle 1

- **Timestamp:** 2026-05-31T03-25
- **Issue:** #46
- **Base branch:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Branch head:** `bug/gui-silent-crash-crash-visibility-46` @ `e17da56195d576de38faf47cfbfca2382ca702f1`
- **Prior audit:** `policy-audit.2026-05-31T02-43.md` (Cycle 0)
- **Work mode:** full-bug (AC source: `spec.md`)
- **Scope:** Full branch diff vs base. No caller-supplied scope narrowing was applied.

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
| Python | Yes (5 production, 4 test) | per-file term-missing in `evidence/qa-gates/phase8/pytest.md` | In scope |
| TypeScript | No | N/A | No `.ts/.tsx` files changed |
| PowerShell | No | N/A | No `.ps1/.psm1` files changed |
| C# | No | N/A | No `.cs/.csproj` files changed |

Changed `.py` files (9):

- `src/gui/_crash_handler.py` (NEW)
- `src/gui/_crash_handler_bootstrap.py` (NEW in R1)
- `src/gui/app.py` (modified)
- `src/gui/runners.py` (modified)
- `src/gui/workers/pipeline_worker.py` (modified)
- `tests/gui/test_app_composition.py` (modified)
- `tests/gui/test_crash_handler.py` (NEW)
- `tests/gui/test_pipeline_worker.py` (modified)
- `tests/gui/test_runners_threaded.py` (NEW)

## Remediation Cycle 1 — Status of R1-R4

| Item | Verification | Result |
|---|---|---|
| R1 — `src/gui/app.py` <= 500 lines | `wc -l src/gui/app.py` -> 499; `awk 'END{print NR}'` -> 499 | **CLEARED** |
| R2 — Spec AC-1 uses `resolve_log_dir`; no stray `_resolve_log_dir` in code/spec | Spec.md grep for `_resolve_log_dir` returns no matches; only historical audit/evidence files retain the underscore form | **CLEARED** |
| R3 — Faithful line counts in phase4/file-sizes.md + phase8/file-sizes.md exists | Phase 4 artifact regenerated with `wc -l`/`awk NR`, reports `src/gui/app.py = 503` (pre-R1 state) with explicit correction note; phase 8 artifact at `evidence/qa-gates/phase8/file-sizes.md` reports `src/gui/app.py = 499` post-R1 | **CLEARED** |
| R4 — Three new closure tests exist and pass; `_crash_handler.py` line coverage >= 88% | Lines 435, 473, 511 of `tests/gui/test_crash_handler.py` define `test_sys_excepthook_appends_traceback_record`, `test_threading_excepthook_appends_traceback_record`, `test_append_traceback_swallows_oserror`; phase 8 pytest evidence reports `_crash_handler.py` at 100% line / 100% branch (was 88%) | **CLEARED** |

All four cycle-1 remediation items are cleared on their stated definition-of-done. However, the cycle introduced a new Blocking finding (F5) that did not exist in cycle 0; see Detailed Findings below.

## Per-Finding Verdict Summary

| Finding | Severity | Verdict |
|---|---|---|
| F5: `tests/gui/test_crash_handler.py` exceeds the 500-line cap (549 lines, NEW file from this branch, with +217 lines of R4 fixture/test code) | Blocking | **FAIL** |
| F1 (cycle 0 carryover): `src/gui/app.py` exceeds 500-line cap | Blocking | **CLEARED** (now 499 lines) |
| F2 (cycle 0 carryover): spec/code symbol drift `_resolve_log_dir` vs `resolve_log_dir` | PARTIAL | **CLEARED** (spec AC-1 now uses `resolve_log_dir`) |
| F3 (cycle 0 carryover): phase4 file-sizes evidence undercount | PARTIAL | **CLEARED** (phase4 regenerated; phase8 added) |
| F4 (cycle 0 carryover): closure-body coverage gap in `_crash_handler.py` | PARTIAL | **CLEARED** (3 new tests; 88% -> 100% line, residual missing lines empty) |

## Detailed Findings

### F5 — File-size cap violation in `tests/gui/test_crash_handler.py` [Blocking, FAIL]

- **Rule:** `.claude/rules/general-code-change.md` — "No production code, **test code**, or reusable script file may exceed **500 lines**. Exceptions: temporary throwaway scripts created and deleted within an agent session; raw text fixtures for language-processing test data; Markdown documentation files." Test code is explicitly within scope; no exception applies here.
- **Evidence:**
  - `wc -l tests/gui/test_crash_handler.py` -> `549`
  - `awk 'END{print NR}' tests/gui/test_crash_handler.py` -> `549`
  - `git diff --stat 0b353ad..HEAD -- tests/gui/test_crash_handler.py` -> `1 file changed, 549 insertions(+)` (file is wholly new on this branch).
  - Cycle 0 head reported this same file at 332 lines (cycle 0 code-review file-size table). The R4 cycle-1 remediation added approximately 217 lines: a 76-line `_FakePath` / `_FakeFileHandle` fixture pair (lines 348-432) plus three new tests (~38 + 36 + 39 lines = ~113 lines, lines 435-549), pushing the file from 332 to 549.
- **Impact:** The 500-line cap is a hard policy rule with no tier-dependent exception. Test code is explicitly covered. Cycle 1 cleared R1 (production-file cap) but introduced a symmetrical violation on the test side. AC-12 of the spec says "No production file in the diff exceeds 500 lines"; the AC text scopes itself to production files and is technically satisfied, but the cross-cutting `general-code-change.md` cap is not.
- **Recommendation:** Split `tests/gui/test_crash_handler.py` into two cohesive files. Suggested split (lowest-risk):
  - `tests/gui/test_crash_handler.py` retains: AC-1..AC-4 / AC-7 installer-contract, idempotency, `resolve_log_dir` parametric tests, Qt message-handler routing (approx. lines 1-345 of the current file).
  - `tests/gui/test_crash_handler_closures.py` (NEW): the `_FakePath`/`_FakeFileHandle` fixture pair plus the three R4 closure-invocation tests (`test_sys_excepthook_appends_traceback_record`, `test_threading_excepthook_appends_traceback_record`, `test_append_traceback_swallows_oserror`).
  - Both files should land under 500 lines (current file is 549, the closure block is roughly 200, so the residual is roughly 345). Re-run the full toolchain; coverage on `_crash_handler.py` must remain at 100% line / 100% branch.
- **Definition of done:**
  - `awk 'END{print NR}' tests/gui/test_crash_handler.py` and any sibling test file each return `<= 500`.
  - All four Python toolchain stages pass in a single pass.
  - `_crash_handler.py` line and branch coverage remain at the post-R4 levels (100% / 100%).
- **Artifact paths:**
  - Code: `tests/gui/test_crash_handler.py` (split into two files).
  - Evidence: regenerate `evidence/qa-gates/phase8/file-sizes.md` to include the test file rows (the current artifact lists only production files).

## Suppression Audit (Python)

- **Command:** `git diff 0b353ad..e17da56 -- '*.py' | grep -E '^\+' | grep -vE '^\+\+\+' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'`
- **Result:** No matches. The R4 closure tests deliberately use `vars(crash_handler)[name]` instead of attribute access to avoid Pyright `reportPrivateUsage` and Ruff `B009`, so no suppression is needed (documented in `evidence/qa-gates/phase7/suppression-diff.md`).
- Verdict: **PASS** — `python-suppressions.md` policy holds; no new `# noqa`, `# type: ignore`, or `# pyright: ignore` markers were added.

## Toolchain Loop Verification (Python)

| Stage | Phase 8 evidence | EXIT_CODE | Verdict |
|---|---|---|---|
| 1. Format (black --check) | `evidence/qa-gates/phase8/black.md` | 0 | PASS |
| 2. Lint (ruff check) | `evidence/qa-gates/phase8/ruff.md` | 0 | PASS |
| 3. Type check (pyright) | `evidence/qa-gates/phase8/pyright.md` | 0 | PASS |
| 4. Architecture-boundary tests | Not separately gated in this repo; covered by unit tests | n/a | N/A |
| 5. Unit tests + coverage (pytest) | `evidence/qa-gates/phase8/pytest.md` | 0; 737 passed | PASS |
| 6. Contract / schema compat | No schema/contract surface touched | n/a | N/A |
| 7. Integration tests | Covered by pytest-qt cases in unit suite | 0 | PASS |
| Single-pass attestation | `evidence/qa-gates/phase8/single-pass-summary.md` | all 0 | PASS |

Toolchain-loop verdict: **PASS** — all four mandatory Python stages green in a single pass (the loop did not restart between black, ruff, pyright, and pytest).

## Coverage Verification (Python)

Coverage verification uses the pre-existing evidence at `evidence/qa-gates/phase8/pytest.md` and `evidence/qa-gates/phase9/coverage-delta.md`. The repo does not produce `coverage/lcov.info` for this feature; the per-file term-missing report is the authoritative artifact and is captured in the feature evidence folder.

### Per-File Coverage Comparison (Baseline vs Post-Change, Disposition)

### 1.2.1 Per-language coverage rows (Python)

- **src/gui/_crash_handler.py** (new file)
  - Baseline: n/a (file did not exist)
  - Post-change: 100% line (99/99), 100% branch (8/8)
  - Change: +99 statements, +8 branches, 0 missed lines (R4 closed the prior 88% gap)
  - New/changed-code coverage: 100% line (>= 85%), 100% branch (>= 75%)
  - Disposition: PASS (threshold met; F4 cycle-0 informational gap is closed)
  - Evidence: `evidence/qa-gates/phase8/pytest.md` per-file table; `evidence/qa-gates/phase9/coverage-delta.md` row (c).

- **src/gui/_crash_handler_bootstrap.py** (new file from R1)
  - Baseline: n/a (file did not exist)
  - Post-change: 100% line (6/6), 0 branches
  - Change: +6 statements, 0 branches
  - New/changed-code coverage: 100% line (>= 85%)
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase8/pytest.md`; covered via the retargeted composition-root test (`test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`).

- **src/gui/runners.py** (modified)
  - Baseline: 66% line, 0 branches
  - Post-change: 100% line (46/46), 100% branch
  - Change: +14 statements; coverage rose from 66% to 100%
  - New/changed-code coverage: 100% line (>= 85%)
  - Disposition: PASS (improvement; no regression)
  - Evidence: `evidence/qa-gates/phase8/pytest.md` per-file table.

- **src/gui/workers/pipeline_worker.py** (modified)
  - Baseline: 100% line, 0 branches
  - Post-change: 100% line (24/24), 100% branch (2/2)
  - Change: +2 statements (BaseException widening + re-raise); new branch denominator covered
  - New/changed-code coverage: 100% line (>= 85%), 100% branch (>= 75%)
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase8/pytest.md` per-file table.

- **src/gui/app.py** (modified)
  - Baseline: 99% line (138/138 with 1 missed line 314), 92% branch
  - Post-change: 99% line (137/137 with 1 missed line 314), 92% branch
  - Change: -1 statement (R1 net reduction after bootstrap extraction); no regression
  - New/changed-code coverage: 100% on the installer-call site
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase9/coverage-delta.md` row (d).

### Repo-Wide Per-Language Coverage

- Python total: 99% line (3656 statements, 20 missed); branch ~96.5% (660 branches, 23 partial). Above the 85% line / 75% branch thresholds. Disposition: PASS.
- Evidence: `evidence/qa-gates/phase8/pytest.md` headline coverage.

### Coverage Checklist (Python)

- [x] Coverage artifact present (per-file term-missing in `evidence/qa-gates/phase8/pytest.md` and delta in `evidence/qa-gates/phase9/coverage-delta.md`).
- [x] Repo-wide coverage line >= 85% (99%).
- [x] Repo-wide coverage branch >= 75% (~96.5%).
- [x] Each new file >= 85% line / >= 75% branch (`_crash_handler.py` 100%/100%; `_crash_handler_bootstrap.py` 100%).
- [x] Each modified file no regression on changed lines (runners.py improved; pipeline_worker.py unchanged; app.py unchanged).

### Coverage Checklist (TypeScript)

- [x] No TypeScript files changed on the branch; coverage verification not required for this branch.

### Coverage Checklist (PowerShell)

- [x] No PowerShell files changed on the branch; coverage verification not required for this branch.

### Coverage Checklist (C#)

- [x] No C# files changed on the branch; coverage verification not required for this branch.

## Evidence Location Compliance

- **Scan command:** `git diff --diff-filter=AM --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..e17da56195d576de38faf47cfbfca2382ca702f1 -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'`
- **Result:** Empty. No files were written to any non-canonical evidence path. All branch-added evidence lives under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/<kind>/`.
- **Note:** The `validate_evidence_locations.py` script is not present in this repo (`scripts/validate_evidence_locations.py` does not exist); the git-diff scan above is the substitute per the persistent agent memory entry.
- Verdict: **PASS** — evidence-location invariant holds.

## Rejected Scope Narrowing

None. The caller prompt requested a full feature-vs-base reaudit and explicitly reaffirmed the scope invariant ("Scope determination is your responsibility per the skill's scope invariant; do not narrow scope."). No narrowing was attempted by the caller and none was applied.

## Dependency Diff

- Command: `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..e17da56195d576de38faf47cfbfca2382ca702f1 -- pyproject.toml poetry.lock`
- Result: empty (no changes). Verdict: **PASS** (AC-11 satisfied).

## File-Size Compliance Table (Authoritative `awk NR` counts at HEAD)

| File | Lines | Under 500-line cap | Notes |
|---|---|---|---|
| src/gui/_crash_handler.py | 495 | Yes (5 lines of headroom) | Near cap; new module |
| src/gui/_crash_handler_bootstrap.py | 94 | Yes | New in R1 |
| src/gui/runners.py | 270 | Yes | +114 vs baseline |
| src/gui/workers/pipeline_worker.py | 116 | Yes | +37 vs baseline |
| src/gui/app.py | 499 | Yes (1 line of headroom) | Post-R1 reduction |
| tests/gui/test_app_composition.py | 480 | Yes (20 lines of headroom) | +79 vs baseline |
| tests/gui/test_pipeline_worker.py | 244 | Yes | +99 vs baseline |
| tests/gui/test_runners_threaded.py | 151 | Yes | New |
| tests/gui/test_crash_handler.py | 549 | **No** (49 lines over) | New; R4 fixture + 3 tests pushed file over cap |

## Final Policy Verdict

**FAIL** — one Blocking finding (F5: `tests/gui/test_crash_handler.py` 549 lines > 500-line cap). All cycle-0 carryover findings (F1-F4) are cleared. The single remaining blocking finding requires another short remediation cycle to split the test file.

## Appendix A — Verification Commands

- `awk 'END{print NR}' src/gui/app.py src/gui/_crash_handler.py src/gui/_crash_handler_bootstrap.py src/gui/runners.py src/gui/workers/pipeline_worker.py`
- `for f in tests/gui/test_app_composition.py tests/gui/test_runners_threaded.py tests/gui/test_pipeline_worker.py tests/gui/test_crash_handler.py; do echo "$f: $(awk 'END{print NR}' "$f")"; done`
- `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..e17da56195d576de38faf47cfbfca2382ca702f1`
- `git diff 0b353adcd596ff450db5cfa7ca771ef22565e53a..e17da56195d576de38faf47cfbfca2382ca702f1 -- '*.py' | grep -E '^\+' | grep -vE '^\+\+\+' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'`
- `git diff --diff-filter=AM --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..e17da56195d576de38faf47cfbfca2382ca702f1 -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'`
- `grep -nE 'except\s*:' src/gui/_crash_handler.py src/gui/_crash_handler_bootstrap.py src/gui/runners.py src/gui/workers/pipeline_worker.py src/gui/app.py`
- `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..e17da56195d576de38faf47cfbfca2382ca702f1 -- pyproject.toml poetry.lock`
