# Policy Audit — gui-silent-crash-crash-visibility (Issue #46)

- **Timestamp:** 2026-05-31T02-43
- **Issue:** #46
- **Base branch:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Branch head:** `bug/gui-silent-crash-crash-visibility-46` @ `666e84a32aa158a4554cb0305c5695512e35f0cd`
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
| Python | Yes (4 production, 4 test) | `coverage/lcov.info` (per repo standard) — verification via `evidence/qa-gates/phase7/coverage-delta.md` | In scope |
| TypeScript | No | N/A | No `.ts/.tsx` files changed |
| PowerShell | No | N/A | No `.ps1/.psm1` files changed |
| C# | No | N/A | No `.cs/.csproj` files changed |

## Per-Finding Verdict Summary

| Finding | Severity | Verdict |
|---|---|---|
| F1: `src/gui/app.py` exceeds 500-line cap (503 lines, post-change) | Blocking | **FAIL** |
| F2: Spec AC-1 references `_resolve_log_dir`; implementation exposes `resolve_log_dir` (no underscore) | Material PARTIAL | **PARTIAL** |
| F3: Phase 4 `file-sizes.md` line counts disagree with `wc -l` / `awk NR` (PowerShell `Measure-Object -Line` undercount) | Material PARTIAL | **PARTIAL** |
| F4: Coverage evidence absent for production `src/gui/_crash_handler.py` closures (lines 254-263, 290-303, 374-383) | Informational | **PARTIAL** |

## Detailed Findings

### F1 — File-size cap violation in `src/gui/app.py` [Blocking, FAIL]

- **Rule:** `.claude/rules/general-code-change.md` — "No production code, test code, or reusable script file may exceed **500 lines**." AC-12 of the feature spec mirrors this rule.
- **Evidence:**
  - `awk 'END{print NR}' src/gui/app.py` -> `503`
  - `wc -l src/gui/app.py` -> `503`
  - Diff stat: `src/gui/app.py +12/-2` (net +10) on top of baseline 493 lines.
- **Impact:** The change moved `src/gui/app.py` from 493 (under cap) to 503 (over cap). This is a hard policy violation introduced by the feature branch.
- **Recommendation:** Extract the crash-handler installer invocation in `main()` into a small helper module (e.g., `src/gui/_crash_handler_bootstrap.py`) or move one of the existing helper closures inside `wire_control_signals` into a sibling module, then rerun the toolchain. Target: `<= 500` lines.

### F2 — Spec/code symbol drift: `_resolve_log_dir` vs `resolve_log_dir` [PARTIAL]

- **Rule:** `general-code-change.md` requires spec/code consistency; AC-1 verbatim text refers to `_resolve_log_dir(app_name, platform_system, env)`.
- **Evidence:**
  - Spec AC-1 (line 202 of `spec.md`): "...exposes a single `install_crash_handlers(...)` entry point plus a pure `_resolve_log_dir(app_name, platform_system, env)` helper."
  - Implementation `src/gui/_crash_handler.py` lines 54-60, 126: public symbol is `resolve_log_dir` (no leading underscore).
  - Plan P2-T2 documents the rename as deliberate ("Renamed from `_resolve_log_dir` to `resolve_log_dir` to satisfy Pyright strict-mode `reportPrivateUsage` when accessed from tests.").
- **Impact:** Behavioral contract is satisfied (pure helper exists; tests cover it). Documentation/spec drift only — readers comparing the spec to the source will see a name mismatch and a misleading underscore-private convention.
- **Recommendation:** Update spec AC-1 text to `resolve_log_dir`, or restore the underscore prefix in code and use `# pyright: ignore[reportPrivateUsage]` only in test access points if absolutely necessary (the rename approach is cleaner; updating the spec is the lower-risk fix).

### F3 — File-size evidence undercount in `evidence/qa-gates/phase4/file-sizes.md` [PARTIAL]

- **Rule:** `general-code-change.md` 500-line cap; evidence artifacts must report verifiable, reproducible numbers.
- **Evidence:**
  - Phase-4 evidence reports: `src/gui/app.py` = 439 (post-change); `src/gui/_crash_handler.py` = 405; `src/gui/runners.py` = 223; `src/gui/workers/pipeline_worker.py` = 92.
  - Authoritative counts (`awk NR`): app.py = 503; _crash_handler.py = 495; runners.py = 270; pipeline_worker.py = 116.
  - Cause: PowerShell `(Get-Content <path> | Measure-Object -Line).Lines` counts line-terminator characters and undercounts versus `wc -l` / `awk NR` (no trailing newline / mixed EOL behavior).
- **Impact:** The evidence artifact concealed the AC-12 violation. The "all under 500" attestation in Phase 4 is inaccurate.
- **Recommendation:** Replace the PowerShell command with `wc -l` (via WSL/bash) or `(Get-Content <path>).Count` in PowerShell, regenerate `phase4/file-sizes.md`, and treat F1 as the actual remediation driver.

### F4 — Coverage gaps in `_crash_handler.py` closures [PARTIAL, informational]

- **Rule:** `.claude/rules/general-unit-test.md` / `quality-tiers.md` — line coverage >= 85%, branch coverage >= 75%, uniform across tiers; "Untested critical behavior is not acceptable even if the overall percentage looks good."
- **Evidence:** Phase 7 `pytest.md` per-file table:
  - `src/gui/_crash_handler.py`: 88% line, 100% branch (overall above threshold).
  - Uncovered lines: 254-263 (`_make_sys_excepthook` closure body), 290-303 (`_make_threading_excepthook` closure body), 374-383 (`_append_traceback`).
- **Impact:** The closures and the on-disk traceback append path are never exercised by tests. The numeric thresholds are met, but the structural correctness of the actual crash-write path is unverified. AC-2 verifies the four hooks are *recorded*; it does not verify the closures *function* end-to-end.
- **Recommendation:** Add three tests that invoke the closures with stub `crash_log_path` (using `BytesIO`-backed or `_append_traceback`-patched seam) so the formatted traceback record is written and asserted. This raises confidence in the AC-5 / AC-7 contracts and clears the residual coverage gap without rebinding process-wide hooks.

## Suppression Audit (Python)

- **Command:** `git diff 0b353ad..666e84a -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'`
- **Result:** No matches. No new `# noqa`, `# type: ignore`, or `# pyright: ignore` markers were added on the branch. Verdict: **PASS** — `python-suppressions.md` policy holds.

## Toolchain Loop Verification (Python)

| Stage | Phase 7 evidence | EXIT_CODE | Verdict |
|---|---|---|---|
| 1. Format (black) | `evidence/qa-gates/phase7/black.md` | 0 | PASS |
| 2. Lint (ruff) | `evidence/qa-gates/phase7/ruff.md` | 0 | PASS |
| 3. Type check (pyright) | `evidence/qa-gates/phase7/pyright.md` | 0 | PASS |
| 4. Architecture-boundary tests | Not separately gated in this repo; covered by unit tests | n/a | N/A |
| 5. Unit tests + coverage (pytest) | `evidence/qa-gates/phase7/pytest.md` | 0; 734 passed | PASS |
| 6. Contract / schema compat | No schema/contract surface touched | n/a | N/A |
| 7. Integration tests | Covered by pytest-qt cases in unit suite | 0 | PASS |
| Single-pass attestation | `evidence/qa-gates/phase7/single-pass-attestation.md` | 0 | PASS |

Toolchain-loop verdict: **PASS** — all four mandatory Python stages green in a single pass.

## Coverage Verification (Python)

Coverage verification uses pre-existing evidence at `evidence/qa-gates/phase7/pytest.md` and `evidence/qa-gates/phase7/coverage-delta.md`. The repo does not produce `coverage/lcov.info` for this feature; the per-file term-missing report is the authoritative artifact and is captured in the feature evidence folder.

### Per-File Coverage Comparison (Baseline vs Post-Change, Disposition)

- **src/gui/_crash_handler.py** (new file)
  - Baseline: n/a (file did not exist)
  - Post-change: 88% line, 100% branch (8/8)
  - Change: +118 statements, +10 branches, +2 missed lines
  - New/changed-code coverage: 88% line (>= 85%), 100% branch (>= 75%)
  - Disposition: PASS (threshold met); see F4 for an informational gap on the hook-closure bodies.
  - Evidence: `evidence/qa-gates/phase7/coverage-delta.md` line 9.

- **src/gui/runners.py** (modified)
  - Baseline: 66% line, 0 branches
  - Post-change: 100% line, no branch denominators in this file
  - Change: +14 statements; line coverage rose from 66% to 100%
  - New/changed-code coverage: 100% line (>= 85%)
  - Disposition: PASS (improvement; no regression)
  - Evidence: `evidence/qa-gates/phase7/coverage-delta.md` line 10.

- **src/gui/workers/pipeline_worker.py** (modified)
  - Baseline: 100% line, 0 branches
  - Post-change: 100% line, 100% branch (2/2)
  - Change: +2 statements (BaseException widening + re-raise); new branch denominator covered
  - New/changed-code coverage: 100% line (>= 85%), 100% branch (>= 75%)
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase7/coverage-delta.md` line 11.

- **src/gui/app.py** (modified)
  - Baseline: 99% line, 92% branch (12/12 with 1 partial)
  - Post-change: 99% line, 92% branch (12/12 with 1 partial)
  - Change: +3 statements (installer import + invocation block); no regression
  - New/changed-code coverage: changed lines (installer import/call) covered by the new composition-root test
  - Disposition: PASS
  - Evidence: `evidence/qa-gates/phase7/coverage-delta.md` line 12.

### Repo-Wide Per-Language Coverage

- Python total: 99% line (3618 of 3651 statements covered); branch partials 23/660. Above the 85% line and 75% branch thresholds. Disposition: PASS.
- Evidence: `evidence/qa-gates/phase7/pytest.md` "Headline coverage" section.

### Coverage Checklist (Python)

- [x] Coverage artifact present (per-file term-missing in `evidence/qa-gates/phase7/pytest.md`).
- [x] Repo-wide coverage line >= 85% (99%).
- [x] Repo-wide coverage branch >= 75% (~96%).
- [x] Each new file >= 85% line / >= 75% branch (`_crash_handler.py` 88%/100%).
- [x] Each modified file no regression on changed lines (runners.py improved; pipeline_worker.py unchanged; app.py unchanged).

### Coverage Checklist (TypeScript)

- [x] No TypeScript files changed on the branch; coverage verification not required for this branch.

### Coverage Checklist (PowerShell)

- [x] No PowerShell files changed on the branch; coverage verification not required for this branch.

### Coverage Checklist (C#)

- [x] No C# files changed on the branch; coverage verification not required for this branch.

## Evidence Location Compliance

Scan command: `git diff --diff-filter=AM --name-only 0b353ad..666e84a -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'`

Result: no matches. All branch-added evidence lives under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/<kind>/`. Verdict: **PASS** — evidence-location invariant holds.

The `validate_evidence_locations.py` script is not present in this repo (`scripts/validate_evidence_locations.py` does not exist); the git-diff scan above is the substitute per the persistent agent memory entry.

## Rejected Scope Narrowing

None. The caller prompt requested full feature-vs-base audit; no narrowing was attempted.

## Dependency Diff

- Command: `git diff --name-only 0b353ad..666e84a -- pyproject.toml poetry.lock`
- Result: empty (no changes). Verdict: **PASS** (AC-11 satisfied).

## Final Policy Verdict

**FAIL** — one Blocking finding (F1, AC-12 file-size cap violation in `src/gui/app.py`). The other findings are PARTIAL/informational and do not, on their own, block merge.

## Appendix A — Verification Commands

- `awk 'END{print NR}' src/gui/app.py src/gui/_crash_handler.py src/gui/runners.py src/gui/workers/pipeline_worker.py`
- `git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..666e84a32aa158a4554cb0305c5695512e35f0cd`
- `git diff 0b353adcd596ff450db5cfa7ca771ef22565e53a..666e84a32aa158a4554cb0305c5695512e35f0cd -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'`
- `git diff --diff-filter=AM --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..666e84a32aa158a4554cb0305c5695512e35f0cd -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'`
- `grep -nE 'except\s*:' src/gui/_crash_handler.py src/gui/runners.py src/gui/workers/pipeline_worker.py src/gui/app.py`
