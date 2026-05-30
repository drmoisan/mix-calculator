# rate-impacts-summed-ratio (Plan)

- **Issue:** #37
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/37
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-29T21-59
- **Status:** Draft
- **Version:** 0.2
- **Work Mode:** minor-audit
- **Requirements source (sole):** `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/issue.md` (`## Acceptance Criteria`, AC1–AC6)

**Canonical evidence root:** `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/evidence/`
All evidence artifacts MUST be written under `evidence/<kind>/` (e.g. `evidence/baseline/`, `evidence/regression-testing/`, `evidence/qa-gates/`). Non-canonical paths such as `artifacts/baselines/`, `artifacts/qa/`, or `artifacts/coverage/` are forbidden and fail preflight.

**Fail-closed evidence rule:** Each baseline command step, each final-QC command step, and the coverage-comparison step produces its own artifact. If any required baseline, QA, or coverage-comparison artifact is missing or has incomplete fields (`Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`), the verdict is BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Each evidence-producing task records its expected artifact path. Work is not complete without the artifact on disk.

**Scope lock (per-batch budget):** Exactly 1 production file (`src/mix_rate_impacts.py`) and 1 test file (`tests/test_mix_rate_impacts.py`). No other production or test files may be modified. Do NOT modify `src/_mix_transforms_helpers.py` behavior, `calc_ratios`, `_safe_div`, `src/mix_lookups.py`, or any policy file under `.claude/rules/`.

**Confidentiality constraint (non-negotiable):** Real workbook aggregate figures, reconciliation totals, and source dollar/lbs values are confidential and MUST NOT appear in the plan, the code, the tests, or any committed artifact. All tests use synthetic, proportional values only.

**File-size constraint:** `src/mix_rate_impacts.py` (~124 lines today) and `tests/test_mix_rate_impacts.py` MUST each remain under 500 lines.

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read repository policy files in the required order and record the read evidence. Order: `CLAUDE.md`; `.claude/rules/general-code-change.md`; `.claude/rules/general-unit-test.md`; `.claude/rules/python.md`; `.claude/rules/python-suppressions.md`; `.claude/rules/self-explanatory-code-commenting.md`; `.claude/rules/quality-tiers.md`; `.claude/rules/tonality.md`. Write `evidence/baseline/phase0-instructions-read.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read.
- [x] [P0-T2] Capture the Black formatting baseline. Command: `poetry run black --check .`. Write `evidence/baseline/black.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (formatted/would-reformat file counts).
- [x] [P0-T3] Capture the Ruff lint baseline. Command: `poetry run ruff check .`. Write `evidence/baseline/ruff.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (error count).
- [x] [P0-T4] Capture the Pyright type-check baseline. Command: `poetry run pyright`. Write `evidence/baseline/pyright.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (error/warning counts).
- [x] [P0-T5] Capture the Pytest + coverage baseline. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `evidence/baseline/pytest-coverage.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording numeric headline values: total passed/failed count, total line-coverage percent, total branch-coverage percent, and the per-module line/branch coverage for `src/mix_rate_impacts.py`.

> Note on the Poetry environment: if Poetry installs into or reads a global interpreter, prefix each `poetry run …` command with `env -u VIRTUAL_ENV` (or clear `VIRTUAL_ENV` for the shell) so the project virtual-env is used. Record the exact command actually run in each artifact.

### Phase 1 — Constrained Small-Path Implementation

Delegated to the small-path implementation engineer. Scope is locked to `src/mix_rate_impacts.py` (production) and `tests/test_mix_rate_impacts.py` (test). Toolchain order during implementation is Black → Ruff → Pyright → Pytest, restarting from Black on any failure or file change.

**Implementation tasks (production — `src/mix_rate_impacts.py`):**

- [x] [P1-T1] In `build_rate_impacts`, after `wide = stack_pivot(...)` (currently line 91) and before the impact-formula block (currently lines 95-112), insert a recomputation block that derives the per-unit and %GS metrics at the `{Customer, SKU #}` grain from the additive dollar/volume wide columns already present in `wide`: `Net-Revenue $ - AOP/LE`, `Lbs - AOP/LE`, `Gross Sales - AOP/LE`, `Off Invoice $ - AOP/LE`, `Trade Spend $ - AOP/LE`, `Non-Trade $ - AOP/LE`. Acceptance: the recomputation block exists and the carried/summed ratio columns (`Gross Sales Per Lb - Diff`, `OI %GS - AOP/Diff`, `Trade %GS - AOP/Diff`, `Non-Trade %GS - AOP/Diff`, `Net Rev Per Lb - Diff`) are no longer read for the impact formulas; instead the recomputed values are used. (Maps AC1.)
- [x] [P1-T2] Recompute the per-Lb metrics using a guarded divide whose zero-denominator semantics are identical to `_safe_div`/`calc_ratios` (`den > 0` ⇒ quotient, else `0.0`). Compute: `net_rev_per_lb_AOP = guarded_div(wide["Net-Revenue $ - AOP"], wide["Lbs - AOP"])`; `net_rev_per_lb_LE = guarded_div(wide["Net-Revenue $ - LE"], wide["Lbs - LE"])`; `Net Rev Per Lb - Diff = net_rev_per_lb_LE - net_rev_per_lb_AOP`. Compute `Gross Sales Per Lb - AOP/LE` from `Gross Sales` over `Lbs` and `Gross Sales Per Lb - Diff = LE - AOP`. Acceptance: per-Lb diffs are derived from dollars/volume, and a zero-`Lbs` denominator yields `0.0` (not `inf`/`NaN`). (Maps AC1, AC2.)
- [x] [P1-T3] Recompute the %GS metrics for AOP and LE from the deduction dollars over `Gross Sales`: `OI %GS = guarded_div(Off Invoice $, Gross Sales)`, `Trade %GS = guarded_div(Trade Spend $, Gross Sales)`, `Non-Trade %GS = guarded_div(Non-Trade $, Gross Sales)`, each per scenario; `… %GS - Diff = LE - AOP`. Also retain the recomputed `OI %GS - AOP`, `Trade %GS - AOP`, `Non-Trade %GS - AOP` used by `Calc Gross Price Impact on Net`. Acceptance: all %GS AOP/LE/Diff values are derived from dollars over `Gross Sales`, with the `Gross Sales <= 0` case yielding `0.0`. (Maps AC1, AC2.)
- [x] [P1-T4] Resolve the guarded-divide source as a single binary decision and document it in an inline comment: either (preferred) add a thin public `safe_div` wrapper in `src/_mix_transforms_helpers.py` that delegates to the existing `_safe_div` (no behavior change to `_safe_div` or `calc_ratios`) and import it, OR import the existing `_safe_div` directly into `src/mix_rate_impacts.py`, OR implement an equivalent vectorized `den > 0` guard locally in `src/mix_rate_impacts.py`. Acceptance: exactly one approach is used, the guard semantics match `_safe_div` (`den > 0`), and `calc_ratios`/`_safe_div` behavior is unchanged. If the wrapper option is chosen, note that it adds a re-export to `_mix_transforms_helpers.py` within the no-behavior-change constraint; if that would exceed the 1-production-file scope lock, prefer the local-guard or direct-import option. (Maps AC2; honors scope lock.)
- [x] [P1-T5] Feed the six existing impact formulas (`RATE_IMPACT_COLUMNS`: `Calc Gross Price Impact on Gross`, `Calc Gross Price Impact on Net`, `OI Rate Impact`, `Trade Rate Impact`, `Non-Trade Rate Impact`, `Calc Net Price Impact`) using the recomputed columns, leaving the formula arithmetic unchanged. Acceptance: the six formula expressions are structurally identical to the current code except that their ratio inputs now come from the recomputed columns. (Maps AC1.)
- [x] [P1-T6] Update the `build_rate_impacts` docstring and add intent comments per `.claude/rules/self-explanatory-code-commenting.md` to state that the per-Lb and %GS metrics are recomputed from the additive dollar/volume wide columns (rather than read from carried/summed ratio columns) and to explain the zero-denominator guard rationale. Acceptance: the docstring reflects the recompute behavior and the recompute block carries a meta-what + why comment; no numbered notes are used. (Maps AC1.)
- [x] [P1-T7] Confirm `src/mix_rate_impacts.py` remains under 500 lines. Acceptance: line count < 500. (Honors file-size constraint.)

**Implementation tasks (test — `tests/test_mix_rate_impacts.py`):**

- [x] [P1-T8] [expect-fail] Add a regression test for the zero-volume deduction sub-row mechanism using synthetic, proportional values only (no confidential figures). Construct an `aop_vs_le` fixture for a single normal `{Customer, SKU #}` pair whose summed/carried `Net Rev Per Lb - Diff` would be zero (the artifact of summing a per-Lb ratio across a sub-row that carried deduction dollars with zero volume), but whose additive dollar/volume columns (`Net-Revenue $ - AOP/LE`, `Lbs - AOP/LE`) imply a non-zero per-Lb diff. Assert that the recomputed `Net Rev Per Lb - Diff` (and the resulting `Calc Net Price Impact`) is the dollar-derived non-zero value. Tag `[expect-fail]` because it fails against the pre-change code that reads the carried summed ratio; capture the failing run in `evidence/regression-testing/fail-before.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (Maps AC3.)
- [x] [P1-T9] Add a reconciliation test (synthetic values only) for a single-SKU Customer x Category group: assert that the SKU-level `Calc Net Price Impact` summed to the `{Customer, Category}` grain equals the category-level net-price impact, so the SKU Mix residual nets to 0 for the single-SKU group. Acceptance: the rollup equality holds within a tight float tolerance (e.g. `1e-9`). (Maps AC4.)
- [x] [P1-T10] Add or retain a behavior-preservation test proving that a SKU with a single fine-grain row (one row per attribute, `Lbs > 0`) produces recomputed per-Lb and %GS values identical to the previously carried ratios. Confirm the existing four tests in `tests/test_mix_rate_impacts.py` still pass unchanged; if the existing fixture supplies only ratio attributes (`Gross Sales Per Lb`, `OI %GS`, etc.) and not the additive dollar/volume columns the recompute now requires, extend the fixture with the consistent dollar/volume columns (`Net-Revenue $`, `Lbs`, `Gross Sales`, `Off Invoice $`, `Trade Spend $`, `Non-Trade $`) for AOP/LE such that the recomputed ratios equal the existing hand-computed expectations. Acceptance: all existing assertions pass and the single-fine-grain recompute equals the carried ratio. (Maps AC5.)
- [x] [P1-T11] Confirm `tests/test_mix_rate_impacts.py` remains under 500 lines. Acceptance: line count < 500. (Honors file-size constraint.)

**Implementation completion acceptance:** All P1 tasks satisfied; AC1–AC5 are exercised by the test file; the regression test (P1-T8) fails before the production change and passes after it; no file outside the 2-file scope is modified.

### Phase 2 — Final QC Loop

Run the full Python toolchain in order (Black → Ruff → Pyright → Pytest). If any step fails or changes files, restart from Black until a single clean pass completes. Each command-bearing task is unconditional and MUST be executed and recorded; `SKIPPED` is not a valid passing outcome.

- [x] [P2-T1] Run formatting. Command: `poetry run black .`. Write `evidence/qa-gates/black.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (files reformatted/unchanged). If files change, restart the loop from this task.
- [x] [P2-T2] Run linting. Command: `poetry run ruff check .`. Write `evidence/qa-gates/ruff.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count). Suppressions are only permitted per `.claude/rules/python-suppressions.md`.
- [x] [P2-T3] Run type checking. Command: `poetry run pyright`. Write `evidence/qa-gates/pyright.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts; must be 0 errors).
- [x] [P2-T4] Run tests with coverage. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `evidence/qa-gates/pytest-coverage.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` recording numeric post-change values: passed/failed count, total line-coverage percent, total branch-coverage percent, and per-module line/branch coverage for `src/mix_rate_impacts.py`.
- [x] [P2-T5] Coverage delta / threshold verification. Compare baseline vs post-change coverage and assert thresholds: total line coverage >= 85%, total branch coverage >= 75%, and no regression on the changed lines in `src/mix_rate_impacts.py`. Write `evidence/qa-gates/coverage-delta.2026-05-29T21-59.md` reporting `baseline line %`, `post-change line %`, `baseline branch %`, `post-change branch %`, and `changed-code coverage %` for `src/mix_rate_impacts.py`. If any threshold is unmet, the verdict is remediation-required (not PASS). (Maps AC6.)
- [x] [P2-T6] Confirm the regression test (P1-T8) passes after the production change and record the pass-after run in `evidence/regression-testing/pass-after.2026-05-29T21-59.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (AC3 and AC4 assertions passing).
- [x] [P2-T7] Reduced minor-audit reconciliation: verify on disk that every Phase 0 baseline artifact and every Phase 2 QC/regression/coverage artifact exists with complete schema fields, that no `spec.md` or `user-story.md` is present in the feature folder, and that `issue.md` retains its explicit `## Acceptance Criteria` section. Mirror the issue-update note at `evidence/issue-updates/issue-37.2026-05-29T21-59.md`. If any artifact is missing, fields are incomplete, or an unexpected spec/user-story file appears, fail closed (BLOCKED/INCOMPLETE). (Maps AC6; minor-audit fail-closed gate.)

---

## Acceptance Criteria Traceability

| AC | Description | Plan tasks |
|---|---|---|
| AC1 | Recompute per-Lb and %GS metrics from additive dollar/volume columns at `{Customer, SKU #}`; six impact formulas unchanged | P1-T1, P1-T2, P1-T3, P1-T5, P1-T6 |
| AC2 | Zero-denominator guard consistent with `calc_ratios`/`_safe_div` (`den > 0` ⇒ value, else 0) | P1-T2, P1-T3, P1-T4 |
| AC3 | Regression test (synthetic): zero-volume deduction sub-row yields non-zero dollar-derived `Net Rev Per Lb - Diff`/`Calc Net Price Impact` | P1-T8 (fail-before), P2-T6 (pass-after) |
| AC4 | Reconciliation: SKU-level `Calc Net Price Impact` rolled up to Customer x Category equals category net-price impact for single-SKU group (SKU Mix = 0) | P1-T9, P2-T6 |
| AC5 | Single-fine-grain SKUs unchanged (recomputed ratio equals carried ratio); existing tests pass | P1-T10 |
| AC6 | Black, Ruff, Pyright, Pytest pass; coverage >= 85% line / >= 75% branch; no regression on changed lines | P0-T2..P0-T5, P2-T1..P2-T5, P2-T7 |
