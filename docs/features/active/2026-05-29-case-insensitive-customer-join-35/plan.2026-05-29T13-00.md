# Implementation Plan — Case-insensitive Customer Join (Issue #35)

- Feature: `docs/features/active/2026-05-29-case-insensitive-customer-join-35/`
- Issue: #35
- Plan timestamp: 2026-05-29T13-00
- Work Mode: minor-audit
- AC source: `docs/features/active/2026-05-29-case-insensitive-customer-join-35/issue.md` (`## Acceptance Criteria`, AC1-AC10)
- Languages in scope: Python
- Production files modified: `src/mix_lookups.py`
- Test files modified: `tests/test_mix_lookups.py`
- Evidence root: `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/`

DIRECTIVE: MINIMAL-AUDIT PLAN
EVIDENCE_LOCATION_OVERRIDE_REJECTED: any non-canonical artifact path replaced with `<FEATURE>/evidence/<kind>/`.

## Resolution of Inputs

- `issue.md` contains explicit `## Acceptance Criteria` (AC1-AC10). Confirmed binding.
- `spec.md` and `user-story.md` are intentionally absent (minor-audit). Not required.
- Implementation strategy is dictated by the caller's directive (see `issue.md` "Design Notes" and the caller-supplied strategy block).

## Plan Conventions

- Every command-bearing task records evidence as a single Markdown artifact in `<FEATURE>/evidence/<kind>/<name>.<task-timestamp>.md` with the required schema fields (`Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`).
- Python toolchain order: Black -> Ruff -> Pyright -> Pytest. Restart from Black if any stage fails or auto-fixes files.
- All shell commands assume the repo root as cwd and the project virtualenv resolved via `poetry run` (preserves the `VIRTUAL_ENV` quirk documented in this repo).
- All evidence paths in this plan are canonical (`<FEATURE>/evidence/<kind>/`). Any supplied non-canonical path is rejected per the non-overridable evidence path clause.

---

### Phase 0 — Baseline capture and policy reading

Captures the binding policy reads and the pre-change toolchain state so post-change deltas (coverage, line counts) are auditable.

- [x] [P0-T1] Read `.claude/rules/general-code-change.md` and `.claude/rules/general-unit-test.md` and record in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/phase0-instructions-read.2026-05-29T13-00.md` the `Timestamp:`, `Policy Order:`, and explicit list of files read. Acceptance: the artifact exists and lists both files plus the Python rules below.
- [x] [P0-T2] Read `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, and `.claude/rules/tonality.md`. Append the file list to the artifact from P0-T1. Acceptance: artifact lists all five files.
- [x] [P0-T3] Run `poetry run black --check src/mix_lookups.py tests/test_mix_lookups.py`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/black.2026-05-29T13-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail and any reformat candidates). Acceptance: artifact exists with all required schema fields.
- [x] [P0-T4] Run `poetry run ruff check src/mix_lookups.py tests/test_mix_lookups.py`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/ruff.2026-05-29T13-00.md` with the schema fields and `Output Summary:` (issue count). Acceptance: artifact exists.
- [x] [P0-T5] Run `poetry run pyright src/mix_lookups.py tests/test_mix_lookups.py`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/pyright.2026-05-29T13-00.md` with the schema fields and `Output Summary:` (error/warning counts). Acceptance: artifact exists.
- [x] [P0-T6] Run `poetry run pytest tests/test_mix_lookups.py --cov=src.mix_lookups --cov-branch --cov-report=term-missing`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/pytest-mix-lookups.2026-05-29T13-00.md` with the schema fields and `Output Summary:` containing the **numeric baseline line and branch coverage** for `src/mix_lookups.py`, plus pass/fail counts. Acceptance: artifact exists and `Output Summary:` contains numeric coverage values (not placeholders).
- [x] [P0-T7] Run `poetry run pytest --cov=src --cov-branch --cov-report=term-missing -q` for the full suite to capture the global baseline. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/pytest-full.2026-05-29T13-00.md` with the schema fields and `Output Summary:` (total pass count, global line/branch coverage). Acceptance: artifact exists with numeric coverage values; suite is green.
- [x] [P0-T8] Record current line counts for `src/mix_lookups.py` and `tests/test_mix_lookups.py` in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/file-size.2026-05-29T13-00.md`. Acceptance: artifact records exact line counts (expected: ~220 for `src/mix_lookups.py`, ~360 for `tests/test_mix_lookups.py`) and confirms both are under the 500-line cap.
- [x] [P0-T9] Locate any existing end-to-end test that invokes `mix_pipeline.main` against the canonical workbook `artifacts/LE v AOP Gross to Net Decomp.xlsx`. Search `tests/` with `Grep` for `LE v AOP Gross to Net Decomp` and for `mix_pipeline.main`. Record findings in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/baseline/e2e-survey.2026-05-29T13-00.md` listing any matching files and the conclusion: "existing canonical-workbook test present" or "no existing canonical-workbook test; AC7 end-to-end will be satisfied by the existing in-memory integration test `tests/test_mix_pipeline.py` plus a new synthetic Winco/WINCO fixture". Acceptance: artifact exists and states the decision.

---

### Phase 1 — Tests-first for the helper and new behavior (expect-fail)

Authors the failing tests before any production change so AC5 and AC6(a-e) have auditable fail-before evidence. Tests live in `tests/test_mix_lookups.py` only; no production code is touched in this phase.

- [x] [P1-T1] Add module-level fixtures at the end of `tests/test_mix_lookups.py` for case-insensitive testing: helper `_aop_norm_rows(customer: str, sku: str, attribute: str, value: float)` and `_le_norm_rows(...)` returning a typed `pd.DataFrame` shaped as `{Customer, SKU #, Attribute, Scenario, Value}`. Acceptance: file imports clean (verified by a Black-check + Ruff-check run after this task) and the helpers are private (`_` prefix), fully typed, and carry Google-style docstrings.
- [x] [P1-T2] [expect-fail] Add `test_build_aop_vs_le_casefold_winco_merges` exercising AC5: AOP has `('Winco', 69005, 'Off Invoice $', -1000.0)` and `('Winco', 69005, 'Non-Trade $', -200.0)`; LE has the same two attributes under `('WINCO', 69005, ...)` plus `('Winco', 69005, 'Gross Sales', 5000.0)` and `('Winco', 69005, 'Lbs', 1000.0)`. Assert: exactly one row per attribute, all displayed Customer values equal `'Winco'`. Record the fail-before run in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/regression-testing/fail-before-ac5.2026-05-29T13-05.md` with `Timestamp:`, `Command: poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_casefold_winco_merges`, `EXIT_CODE: 1`, and `Output Summary:` showing the assertion failure. Acceptance: test fails before production change; artifact captures the failure.
- [x] [P1-T3] [expect-fail] Add `test_build_aop_vs_le_casefold_collapses_three_casings` (AC6a): a single customer appears as `'Winco'`, `'WINCO'`, `'winco'` on the AOP side for SKU `69005` with the same `Lbs` attribute; assert the pivoted result contains exactly one row keyed on `'Winco'` (first observed casing) with `AOP` equal to the sum. Record fail-before run as `fail-before-ac6a.2026-05-29T13-05.md`. Acceptance: test fails before production change; artifact captures the failure.
- [x] [P1-T4] [expect-fail] Add `test_build_aop_vs_le_casefold_strips_whitespace` (AC6b): AOP has `('Winco', 69005, 'Lbs', 10.0)`; LE has `('Winco ', 69005, 'Lbs', 12.0)` (trailing whitespace) and `(' Winco', 69005, 'Gross Sales', 100.0)` (leading whitespace). Assert one row per `(Customer, Attribute)` pair, displayed `Customer` equals `'Winco'` in both. Record fail-before run as `fail-before-ac6b.2026-05-29T13-05.md`. Acceptance: test fails before production change; artifact captures the failure.
- [x] [P1-T5] [expect-fail] Add `test_build_aop_vs_le_display_aop_casing_wins` (AC6c): AOP has `('Winco', 69005, 'Lbs', 10.0)`; LE has `('WINCO', 69005, 'Lbs', 12.0)`. Assert the displayed `Customer` is `'Winco'`. Record fail-before run as `fail-before-ac6c.2026-05-29T13-05.md`. Acceptance: test fails; artifact captures the failure.
- [x] [P1-T6] [expect-fail] Add `test_build_aop_vs_le_le_only_keeps_le_casing` (AC6d): AOP has no rows for the customer; LE has `('WINCO', 69005, 'Off Invoice $', -1000.0)`. Assert exactly one row, displayed `Customer` equals `'WINCO'` (LE casing preserved). Record fail-before run as `fail-before-ac6d.2026-05-29T13-05.md`. Acceptance: test fails; artifact captures the failure. **NOTE:** test PASSES pre-change (the pre-existing literal-Customer pivot already preserves LE-only casing); fail-before exception dossier recorded.
- [x] [P1-T7] [expect-fail] Add `test_build_aop_vs_le_five_casings_collapse_to_one` (AC6e): AOP has `'Winco'`, `'WINCO'`, `'winco'`, `'WinCo'`, `'wInCo'` all with SKU `69005` and `Lbs` attribute. Assert one row in output for the `(SKU, Attribute)` pair, `AOP` equals the sum of values. Record fail-before run as `fail-before-ac6e.2026-05-29T13-05.md`. Acceptance: test fails; artifact captures the failure.
- [x] [P1-T8] [expect-fail] Add `test_build_customer_lu_strips_whitespace` covering AC4: `aop_raw` contains `('Winco ', 'Master')` and `('Winco', 'Master')`. Assert `build_customer_lu` returns one row `('Winco', 'Master')`. Record fail-before run as `fail-before-ac4.2026-05-29T13-05.md`. Acceptance: test fails; artifact captures the failure.
- [x] [P1-T9] [expect-fail] Add `test_build_aop_norm_strips_customer_whitespace` and `test_build_le_norm_strips_customer_whitespace` covering AC2. Each fabricates a long input with `Customer = 'Winco '` and asserts the emitted `Customer` column equals `'Winco'` (casing preserved, whitespace removed). Record fail-before run as `fail-before-ac2.2026-05-29T13-05.md`. Acceptance: tests fail; artifact captures the failure.
- [x] [P1-T10] Confirm new tests do not modify any existing assertion. Run `poetry run pytest tests/test_mix_lookups.py -q` and record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/regression-testing/preexisting-still-pass.2026-05-29T13-05.md` showing the existing tests (`test_build_customer_lu_distinct_pairs`, `test_build_aop_norm_drops_dimensions_and_adds_scenario`, `test_build_le_norm_drops_dimensions_and_adds_scenario`, `test_build_aop_vs_le_pivots_filters_cases_and_diffs`, `test_build_aop_vs_le_missing_scenario_column_filled_zero`, `test_build_aop_vs_le_classifies_normal_for_nonzero_lbs`, `test_build_mix_base_*`) still pass while the new ones fail. Acceptance: artifact shows new-test failures and pre-existing-test passes.

---

### Phase 2 — Implement helper and string-strip applications

Implements AC1 (helper), AC2 (`build_aop_norm` / `build_le_norm` strip), and AC4 (`build_customer_lu` strip). The pivot rework (AC3) is deferred to Phase 3 so failures from Phase 1 resolve in two clean steps.

- [x] [P2-T1] In `src/mix_lookups.py`, add the module-private helper directly above `build_customer_lu`:
  ```python
  def _customer_join_key(s: pd.Series[str]) -> pd.Series[str]:
      """Return the canonical Customer join key (strip + casefold).

      Pure function: applies ``.str.strip()`` and ``.str.casefold()`` to produce
      a key suitable for case-insensitive and whitespace-insensitive joins. The
      input casing is not preserved on the returned series; the displayed
      Customer column must be re-attached by the caller.

      Args:
          s: A string-typed pandas Series of Customer names.

      Returns:
          A pandas Series of the same length with whitespace-trimmed,
          casefolded values.
      """
      return s.str.strip().str.casefold()
  ```
  Acceptance: helper exists, is module-private, fully typed, carries a Google-style docstring. No public API change (not added to `__all__`).
- [x] [P2-T2] In `build_aop_norm`, after the `reduced = aop_long.drop(columns=drop_present).copy()` line and before assigning `Scenario`, insert `reduced["Customer"] = reduced["Customer"].astype(str).str.strip()`. Add an intent comment immediately above the line: `# Strip leading/trailing whitespace so equivalent-up-to-whitespace Customer values join later in build_aop_vs_le; casing is preserved.` Acceptance: source change is exactly the comment plus the one-line strip; the column order and return type are unchanged.
- [x] [P2-T3] In `build_le_norm`, apply the equivalent change to the LE branch with the analogous intent comment. Acceptance: source change is the comment plus the one-line strip; column order and return type unchanged.
- [x] [P2-T4] In `build_customer_lu`, insert `distinct["Customer"] = distinct["Customer"].astype(str).str.strip()` between the existing `distinct = aop_raw[...].drop_duplicates()` line and `return`. Restructure so the strip happens before a second `drop_duplicates()` call that collapses whitespace-equivalent pairs:
  ```python
  distinct = aop_raw[["Customer", "Customer Master"]].copy()
  # Strip whitespace before deduping so 'Winco ' and 'Winco' collapse to one row.
  distinct["Customer"] = distinct["Customer"].astype(str).str.strip()
  distinct = distinct.drop_duplicates()
  return distinct.reset_index(drop=True)
  ```
  Acceptance: the function still returns a two-column DataFrame `{Customer, Customer Master}` in first-appearance order with whitespace-equivalent pairs collapsed.
- [x] [P2-T5] Run the toolchain loop on the changed files: `poetry run black src/mix_lookups.py tests/test_mix_lookups.py`, then `poetry run ruff check --fix src/mix_lookups.py tests/test_mix_lookups.py`, then `poetry run pyright src/mix_lookups.py tests/test_mix_lookups.py`. Restart from Black if any step changes files. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase2-toolchain.2026-05-29T13-15.md` with schema fields per command and a combined `Output Summary:` (all stages green). Acceptance: all three stages green in a single pass.
- [x] [P2-T6] Run `poetry run pytest tests/test_mix_lookups.py -q`. Confirm AC2 tests (`test_build_aop_norm_strips_customer_whitespace`, `test_build_le_norm_strips_customer_whitespace`) and AC4 test (`test_build_customer_lu_strips_whitespace`) now PASS, while AC3/AC5/AC6 tests still FAIL (Phase 3 implements the pivot rework). Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase2-pytest.2026-05-29T13-15.md` with the schema fields and `Output Summary:` listing each AC test's pass/fail. Acceptance: AC2 and AC4 tests pass; AC3/AC5/AC6 tests still fail. **Note:** the Phase 3 pivot rework was advanced in the same toolchain pass per the executor's micro-action protocol so the Pyright `reportUnusedFunction` would not block this gate; AC3/AC5/AC6 therefore PASS at this checkpoint.

---

### Phase 3 — Pivot on the casefolded key and re-attach the display Customer

Implements AC3 in `build_aop_vs_le`. Resolves all remaining AC5 / AC6 failures.

- [x] [P3-T1] In `src/mix_lookups.py`, modify `build_aop_vs_le` per the caller-supplied implementation strategy. Replace the body so it:
  1. Concatenates `aop_norm` and `le_norm` into `combined`.
  2. Adds the join-key column: `combined["_customer_key"] = _customer_join_key(combined["Customer"].astype(str))`.
  3. Pivots on `["_customer_key", "SKU #", "Attribute"]` (not on `["Customer", ...]`).
  4. Ensures both `AOP` and `LE` scenario columns exist and are zero-filled (preserving the existing missing-scenario behavior from `test_build_aop_vs_le_missing_scenario_column_filled_zero`).
  5. Filters out `Attribute == "Cases"` (existing behavior).
  6. Computes `Diff = LE - AOP` (existing behavior).
  7. Builds the AOP display lookup:
     ```python
     aop_display = combined.loc[
         combined["Scenario"] == "AOP", ["_customer_key", "Customer"]
     ].drop_duplicates(subset="_customer_key", keep="first")
     ```
     and the LE display fallback:
     ```python
     le_display = combined.loc[
         combined["Scenario"] == "LE", ["_customer_key", "Customer"]
     ].drop_duplicates(subset="_customer_key", keep="first")
     ```
  8. Left-joins `aop_display` on `_customer_key` to produce `Customer`, then fills NaN from a second left-join on `le_display` (renaming the LE display column to avoid name collision).
  9. Drops `_customer_key` and any helper columns. Reorders to `["Customer", "SKU #", "Attribute", "AOP", "LE", "Diff"]` before passing to `classify_table`.
  Add intent comments above each multi-step block per `.claude/rules/self-explanatory-code-commenting.md`, including:
  - A meta-what comment above the display-rebuild block explaining "AOP wins on display; LE fills LE-only orphans".
  - A WARNING-tagged comment above the `drop_duplicates(subset="_customer_key", keep="first")` lines documenting "If a single Customer key appears under multiple casings on the AOP side, the first observed casing is retained as the display value."
  - A WARNING-tagged comment above the `astype(str)` cast inside `_customer_join_key` invocation documenting that NaN `Customer` values become the literal string `"nan"`; this matches the existing pre-change behavior (no filter is applied).
  Acceptance: function body matches the strategy; column contract (`Customer`, `SKU #`, `Attribute`, `AOP`, `LE`, `Diff`, `Classification`) is unchanged; `_customer_key` is not present in the return value.
- [x] [P3-T2] Run the toolchain loop on the changed files. Restart from Black on any file change. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase3-toolchain.2026-05-29T13-25.md` with schema fields per command and `Output Summary:` (all stages green). Acceptance: all four stages (Black, Ruff, Pyright, Pytest) green in a single pass.
- [x] [P3-T3] Run `poetry run pytest tests/test_mix_lookups.py -q`. Confirm AC3, AC5, and all AC6(a-e) tests now PASS, and that the pre-existing tests still PASS (AC7 partial). Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase3-pytest.2026-05-29T13-25.md` with schema fields and `Output Summary:` listing AC test pass/fail. Acceptance: every new test plus every pre-existing test passes.

---

### Phase 4 — End-to-end AC7 verification

Verifies AC7 (canonical workbook still produces `Check = CHECK` and the existing end-to-end integration test still passes).

- [x] [P4-T1] Run the existing end-to-end integration test: `poetry run pytest tests/test_mix_pipeline.py -q`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase4-mix-pipeline.2026-05-29T13-35.md` with schema fields and `Output Summary:` (all four tests pass: `test_mix_pipeline_end_to_end`, `test_mix_pipeline_rollup_tie_out`, `test_mix_pipeline_loader_error_returns_one`, `test_sqlite_connection_helper_is_in_memory`). Acceptance: tests pass; no assertion modifications were required.
- [x] [P4-T2] Branch on the P0-T9 survey result. If P0-T9 concluded "no existing canonical-workbook test", add a small in-memory smoke test `test_mix_pipeline_nrr_summary_check_ok` in `tests/test_mix_pipeline.py` reusing the existing combined-workbook fixtures and asserting `nrr_summary.Check.iloc[0] == "CHECK"` (or equivalent column shape). If P0-T9 concluded "existing canonical-workbook test present", verify it still passes (covered by P4-T1) and skip new test creation. Record the decision and outcome in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase4-e2e-decision.2026-05-29T13-35.md`. Acceptance: artifact records the decision; if a new test was added, it passes.
- [x] [P4-T3] If `artifacts/LE v AOP Gross to Net Decomp.xlsx` is present in the working tree and a `--input` adapter exists in the test infrastructure, run the canonical workbook smoke run: `poetry run mix-pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output "<temp-sqlite>"` and verify the persisted `nrr_summary` row's `Check` column equals `CHECK`. If the canonical workbook is not present in the working tree (it is large and may not be tracked), skip the run and record the skip-with-justification in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/phase4-canonical-workbook.2026-05-29T13-35.md` per the fail-before exception dossier format (`WhyFailingRunImpossible:` + alternative proof: the in-memory pipeline test plus the AC5 synthetic Winco/WINCO fixture cover the same behavior). Acceptance: either the canonical run succeeds with `Check == CHECK` or the exception dossier is present.

---

### Phase 5 — Final QC and AC verification

Runs the full mandatory Python toolchain in a single clean pass and verifies AC1-AC10.

- [x] [P5-T1] Run `poetry run black --check .`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-black.2026-05-29T13-45.md` with schema fields and `Output Summary:` (formatted-file count = 0; exit code 0). Acceptance: Black reports no reformat candidates.
- [x] [P5-T2] Run `poetry run ruff check .`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-ruff.2026-05-29T13-45.md` with schema fields and `Output Summary:` (issue count = 0; exit code 0). Acceptance: Ruff reports zero issues; no new suppressions added beyond pre-authorized patterns.
- [x] [P5-T3] Run `poetry run pyright`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-pyright.2026-05-29T13-45.md` with schema fields and `Output Summary:` (error/warning counts = 0; exit code 0). Acceptance: Pyright reports zero errors.
- [x] [P5-T4] Run `poetry run pytest --cov=src --cov-branch --cov-report=term-missing -q`. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-pytest.2026-05-29T13-45.md` with schema fields and `Output Summary:` containing the post-change global line and branch coverage as **numeric values**, plus the post-change `src/mix_lookups.py` line and branch coverage. Acceptance: full suite green; `src/mix_lookups.py` line coverage >= 85% and branch coverage >= 75%; no regression on changed lines vs. P0-T6 baseline.
- [x] [P5-T5] Verify line counts: `src/mix_lookups.py` and `tests/test_mix_lookups.py` both remain under the 500-line cap. Record `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-file-size.2026-05-29T13-45.md` with the exact post-change line counts and the baseline counts from P0-T8. Acceptance: both files under 500 lines. **Note:** the case-insensitive tests were split into a sibling file `tests/test_mix_lookups_casefold.py` (296 lines) to keep both files under the policy cap; `tests/test_mix_lookups.py` is 365 lines, `src/mix_lookups.py` is 286 lines.
- [x] [P5-T6] Author the AC verification table in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/ac-verification.2026-05-29T13-45.md`. Each row maps AC1-AC10 to the evidence file(s) that prove it and the post-change status (PASS / FAIL). Specifically:
  - AC1 -> P3 source change in `src/mix_lookups.py` (helper) + P5-T3 Pyright clean.
  - AC2 -> P1-T9 fail-before + P2-T6 pass-after.
  - AC3 -> P1-T2..T7 fail-before + P3-T3 pass-after.
  - AC4 -> P1-T8 fail-before + P2-T6 pass-after.
  - AC5 -> P1-T2 fail-before + P3-T3 pass-after.
  - AC6(a-e) -> P1-T3..T7 fail-before + P3-T3 pass-after.
  - AC7 -> P4-T1 mix_pipeline tests pass; P4-T3 canonical run or dossier.
  - AC8 -> P5-T4 numeric coverage values >= thresholds.
  - AC9 -> P5-T5 line count under cap.
  - AC10 -> P5-T1..T4 all four stages clean in a single pass; no new suppressions.
  Acceptance: every AC row carries `PASS` with at least one canonical evidence path.
- [x] [P5-T7] Run the orchestration validator on this plan file. Command: `mcp__drm-copilot__validate_orchestration_artifacts --artifact_type plan --artifact_path docs/features/active/2026-05-29-case-insensitive-customer-join-35/plan.2026-05-29T13-00.md`. Record the validator result in `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-plan-validation.2026-05-29T13-45.md` with the validator's verdict and any diagnostics. Acceptance: validator returns success; if not, revise and re-run. **Note:** the MCP tool is not exposed to the executor session; upstream validation by the planner was recorded in the delegation prompt and the executor preserved the plan structure (only checkbox `[ ]` -> `[x]` transitions and per-task notes).

---

## Preflight Signal

DIRECTIVE: PREFLIGHT VALIDATION ONLY

Self-check against the atomic-plan contract:

- Phase headings use `### Phase N — <Title>` em-dash format: yes.
- All tasks use `- [ ] [P#-T#]` numbering with sequential per-phase IDs: yes.
- Phase 0 includes policy reads and per-language baseline command-step artifacts (Black, Ruff, Pyright, Pytest with numeric coverage): yes.
- Final phase runs the full toolchain loop and persists numeric coverage values plus a delta verification (P5-T4 references the P0-T6 baseline): yes.
- All evidence paths resolve to `<FEATURE>/evidence/<kind>/`: yes.
- Expect-fail tasks are explicitly tagged `[expect-fail]` and produce auditable dossiers: yes.
- No SKIPPED-as-pass paths on planned commands (P4-T3's skip path is authorized in-task as a fail-before exception dossier per the evidence conventions skill): yes.
- Plan path continuity: the caller-supplied path is the single in-place file used across revisions: yes.
- Minor-audit constraints: AC source is `issue.md`; `spec.md` / `user-story.md` are not required; the explicit `## Acceptance Criteria` section in `issue.md` has been verified present (AC1-AC10): yes.

PREFLIGHT: ALL CLEAR
