# Feature Audit: le-loader-required-vs-output-columns (#57)

**Audit Date:** 2026-06-07
**Feature Folder:** `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57`
**Base Branch:** `main`
**Head Branch:** `fix/loader-header-row-detection` (HEAD `3ae79b1`; #57 delta isolated via `git diff 721a1bf..HEAD`)
**Work Mode:** `full-bug`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (merge-base `b655d81da38e9e27c745460dab2d9ddaf04568ad`, 2026-06-06T22:10:29-04:00)
- **Head branch/commit:** `fix/loader-header-row-detection` (commit `3ae79b1`)
- **Merge base:** `b655d81`
- **Evidence sources:**
  - Primary: `git diff 721a1bf..HEAD` (isolated #57 delta) and independent toolchain re-runs
  - Secondary baseline diff: per-file `git diff 721a1bf..HEAD -- <path>`
  - Feature evidence: `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/**`
  - Additional evidence: grep survey of `src/` for source `YTD/YTG` and source `Super Category` readers
- **Feature folder used:** `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57`
- **Requirements source:** `spec.md` (work mode `full-bug`; mirrored in `issue.md`)
- **Work mode resolution note:** `issue.md` line 10 carries `- Work Mode: full-bug`; the authoritative AC source is therefore `spec.md` only.
- **Scope note:** The #57 delta is isolated from the already-reviewed #55 header-detection work by baselining at commit `721a1bf` (the #55 feature-review-artifacts commit). The intervening `.vscode/launch.json` chore (`fceb35e`) is not source-governed.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/spec.md` — only source (work mode `full-bug`)

### Acceptance criteria

1. AC-1: An LE sheet without a `YTD/YTG` column imports successfully (no "could not resolve required column(s): ['YTD/YTG']" error).
2. AC-2: An LE sheet without a source `Super Category` column imports successfully; output `Super Category` is still derived from `PPG`.
3. AC-3: The protected LE loader requires only the 23 must-have source columns (`Customer`, `SKU Descripiton`, `SKU #`, `Type`, `GtN Mapping`, `Jan`..`Dec`, `FY`, `Q1`..`Q4`, `PPG`); `YTD/YTG` and source `Super Category` are optional (located by name, carried if present, tolerated if absent).
4. AC-4: The standard `LE-8 + 4` source (with `YTD/YTG` + `Super Category` present) produces byte-identical output to today (parity; existing LE loader tests pass).
5. AC-5: A source missing a genuine must-have column raises a clear column-resolution error naming the missing column.
6. AC-6: A flat LE sheet (header row 0, no `YTD/YTG`, no `KEY`) imports to the full `TARGET_COLUMNS` set.
7. AC-7: `load_aop` is unchanged; AOP imports unaffected.
8. AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines; all files <= 500 lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | YTD/YTG-less sheet imports | PASS | `test_load_source_without_ytd_ytg_succeeds_and_drops_it` passes; `resolve_le_columns` excludes located optionals from the required set and never raises on their absence (diff lines 150-209). | `poetry run pytest tests/test_normalize_le.py -q` | Loaded frame asserted to lack `YTD/YTG`. |
| 2 | Super-Category-less sheet imports; output from PPG | PASS | `test_load_source_without_super_category_output_super_from_ppg` asserts `out.iloc[0]["Super Category"] == "PX" == PPG`; `normalize()` line 270 unchanged (`output["Super Category"] = first_rows["PPG"]`). | `poetry run pytest tests/test_normalize_le.py -q` | Source Super Category never read. |
| 3 | Loader requires only the 23 must-have columns; two optionals by name | PASS | `REQUIRED_COLUMNS` = `TEXT_COLUMNS + [*MONTH_COLUMNS, "FY", *QUARTER_COLUMNS, "PPG"]`; `test_required_columns_has_exactly_23_entries` and `test_optional_by_name_is_ytd_ytg_and_super_category` pass; `EXPECTED_COLUMNS = REQUIRED_COLUMNS`. | `poetry run pytest tests/test_normalize_le_columns.py -q` | Optionals located by `normalize_name`, no fuzzy, carried only when present. |
| 4 | Parity for the standard full-column source (byte-identical) | PASS | `test_full_column_source_output_parity_with_standard_fixture` uses `pd.testing.assert_frame_equal`; existing `set(frame.columns) == set(SOURCE_COLUMNS)` assertion passes; `test_both_optionals_present_are_located_and_carried_to_canonical_names` confirms carry. | `poetry run pytest tests/test_normalize_le.py tests/test_schema_loader_parity_le.py -q` | Output `Super Category` = PPG; `YTD/YTG` absent from output. |
| 5 | Missing must-have column raises a naming error | PASS | `test_missing_required_column_raises_value_error_naming_it` drops PPG, asserts `pytest.raises(ValueError, match="PPG")`; `resolve_columns` over `REQUIRED_COLUMNS` raises naming the column. | `poetry run pytest tests/test_normalize_le_columns.py -q` | Negative path preserved. |
| 6 | Flat LE84Data sheet (index 0, no YTD/YTG, no KEY) imports to TARGET_COLUMNS | PASS | `test_flat_le84data_style_sheet_imports_to_target_columns` asserts `set(out.columns) == set(TARGET_COLUMNS)` (26 cols). | `poetry run pytest tests/test_normalize_le_header.py -q` | Header detection at index 0 + must-have-only requirement. |
| 7 | `load_aop` unchanged; AOP unaffected | PASS | `git diff 721a1bf..HEAD -- src/load_aop.py src/_load_aop_helpers.py` returns empty; `tests/test_load_aop.py` passes unchanged. | `git diff 721a1bf..HEAD -- src/load_aop.py src/_load_aop_helpers.py; poetry run pytest tests/test_load_aop.py -q` | Confirmed no diff in either AOP file. |
| 8 | Full toolchain pass; coverage thresholds; files <= 500 lines | PASS | Black/Ruff/Pyright clean on the 5 changed files; whole suite 987 passed; repo-wide 99.08% line / 93.96% branch; changed modules 100% line; largest changed file 499 lines. No suppressions added. No `.github/workflows/**` changes. | `poetry run black --check`, `poetry run ruff check`, `poetry run pyright`, `poetry run pytest --cov --cov-branch` | See policy-audit.2026-06-07T21-15.md Sections 2.5, 7. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 8 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. None required for #57. When the PR runs CI, confirm the green run as part of the orchestrator's standard CI gate (no workflow files were modified by #57, so the `modified-workflow-needs-green-run` rule does not fire).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All 8 criteria are evaluated PASS and are already checked (`- [x]`) in the authoritative source files (`spec.md` and the mirrored `issue.md`).
- No criterion is PARTIAL, FAIL, or UNVERIFIED, so no checkbox needed to be left unchecked.
- No source-file checkbox change was required because the executor had already checked off all 8 criteria after verification; the reviewer confirms those check-offs are evidence-backed and leaves them as-is.

### AC Status Summary

- Source: `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/spec.md`
- Total AC items: 8
- Checked off (delivered): 8
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 8 | 8 | 0 | Checkbox-backed; authoritative (work mode full-bug) |
| `issue.md` | 8 | 8 | 0 | Checkbox-backed mirror; not authoritative but consistent |
