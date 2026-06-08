# Feature Audit: loader-header-row-detection (#55)

**Audit Date:** 2026-06-06
**Feature Folder:** `docs/features/active/2026-06-06-loader-header-row-detection-55`
**Base Branch:** `main`
**Head Branch:** `fix/loader-header-row-detection`
**Work Mode:** `full-bug`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (merge-base commit `b655d81`)
- **Head branch/commit:** `fix/loader-header-row-detection` (commit `721a1bf`)
- **Merge base:** `b655d81da38e9e27c745460dab2d9ddaf04568ad`
- **Evidence sources:**
  - Primary: `git diff main...HEAD` and `git log main..HEAD` (authoritative; PR-context artifacts dated 2026-06-01 are stale relative to HEAD)
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt` (stale; superseded by direct diff)
  - Feature evidence: `docs/features/active/2026-06-06-loader-header-row-detection-55/evidence/**`
  - Additional evidence: independent re-run of Black/Ruff/Pyright and the detection + parity test subset
- **Feature folder used:** `docs/features/active/2026-06-06-loader-header-row-detection-55`
- **Requirements source:** `spec.md` (canonical; mirrored in `issue.md`)
- **Work mode resolution note:** `issue.md` carries the explicit marker `- Work Mode: full-bug`. Per the work-mode contract, `full-bug` resolves the AC source to `spec.md` only.
- **Scope note:** Audit scope is the full branch diff against `main`. The branch is a single commit. No caller scope narrowing was imposed.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `spec.md` — only authoritative source (work mode `full-bug`)
- `issue.md` — mirrors the same list (not the work-mode-authoritative source, tracked for parity)

### Acceptance criteria

1. AC-1: Importing an LE sheet whose header is on Excel row 1 (index 0) resolves columns and completes without the "Source schema mismatch" error.
2. AC-2: The standard `LE-8 + 4` and `AOP1` sheets (header at index 2) still load correctly; detection selects index 2 and loader output is unchanged (parity preserved; existing LE/AOP loader tests pass).
3. AC-3: Header detection is shared between the LE and AOP loaders via a single helper.
4. AC-4: A sheet with no resolvable header row within the scan window raises a clear `ValueError` naming the sheet and the expected columns (no silent fallback).
5. AC-5: Detection is deterministic and rejects a data row that coincidentally contains a few expected tokens (threshold guard).
6. AC-6: `read_excel_sheet` accepts `header=None` for the probe read; existing `header=2` callers are unaffected.
7. AC-7: All changed/added files remain <= 500 lines.
8. AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | LE header-at-index-0 resolves columns, no schema mismatch | PASS | `tests/test_normalize_le_header.py::test_flat_sheet_header_at_index_zero_resolves_columns` asserts `Customer` resolves and both rows kept; `normalize_le.load_source` wires `detect_header_row(..., min_match=20)`. | `poetry run pytest tests/test_normalize_le_header.py -q` | Detection selects index 0 for flat sheets. |
| 2 | Standard sheets (index 2) load; detection selects 2; parity preserved | PASS | 53 pre-existing LE/AOP loader tests pass unchanged (`evidence/regression-testing/parity-le-aop.md`); `test_flat_sheet_load_equals_standard_header_at_index_two` (LE + AOP) uses `pd.testing.assert_frame_equal`. | `poetry run pytest tests/test_normalize_le.py tests/test_load_aop.py -q` | Parity confirmed; output byte-identical for index-2 fixtures. |
| 3 | Detection shared via a single helper | PASS | `src/_header_detection.detect_header_row` imported by both `normalize_le.load_source` and `load_aop.load_aop` (diff lines confirm both imports). | `git diff main...HEAD -- src/normalize_le.py src/load_aop.py` | One shared helper, no duplication of scoring logic. |
| 4 | No resolvable header raises clear ValueError naming sheet and columns | PASS | `test_no_qualifying_row_raises_value_error_naming_sheet_and_columns` asserts sheet name and a normalized expected column appear in the message; `_header_detection.py` lines 150-156 raise with sheet, scan window, floor, and sorted expected tokens. | `poetry run pytest tests/test_header_detection.py -q` | Fail-fast; no silent fallback to header=2. |
| 5 | Deterministic; rejects coincidental-token data row (threshold guard) | PASS | `test_data_row_with_few_coincidental_tokens_below_threshold_not_selected` (score 2 < floor 5 raises) and `test_bytesio_rewind_makes_repeated_calls_deterministic`. Thresholds LE 20/25 and AOP 17/24 both exceed the 12 month tokens. | `poetry run pytest tests/test_header_detection.py -q` | Strict `>` resolves ties to the topmost row; deterministic. |
| 6 | `read_excel_sheet` accepts `header=None`; integer callers unaffected | PASS | `pandas_io.py` widened to `header: int | None` on both function and `_PandasReaders` Protocol; Pyright 0 errors; parity tests (integer callers) pass. | `poetry run pyright src/pandas_io.py` | Backward-compatible widening. |
| 7 | All changed/added files <= 500 lines | PASS | Independent `wc -l`: `_header_detection.py` 158, `load_aop.py` 416, `normalize_le.py` 470, `pandas_io.py` 172, `aop_fixtures.py` 317, `le_fixtures.py` 353, `test_header_detection.py` 167, `test_*_header.py` 59 each; pre-existing `test_normalize_le.py` 446, `test_load_aop.py` 494. | `wc -l <files>` | Largest touched file 494, under cap. |
| 8 | Full toolchain pass + coverage >= 85% line / >= 75% branch, no regression on changed lines | PASS | This audit: Black exit 0, Ruff exit 0, Pyright 0 errors, 63 detection/parity tests pass. Executor: 976 passed, 98% line / ~93.9% branch, 0 missed changed statements (`evidence/qa-gates/coverage-delta.md`, `final-*.md`). | `poetry run black --check src/ tests/`; `poetry run ruff check src/ tests/`; `poetry run pyright src/...`; `poetry run pytest --cov --cov-branch` | No regression on changed lines. |

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

1. None required for merge. The non-scope follow-up noted in `spec.md` (reconcile the bundled schemas' `header_row:0` with the detected header for the schema-driven path) can be tracked separately.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All eight criteria evaluate to PASS.
- Both `spec.md` and `issue.md` already carry all eight items as checked (`- [x]`); no source-file mutation was required during this audit. The check-off state matches the verified PASS evaluation.

### AC Status Summary

- Source: `docs/features/active/2026-06-06-loader-header-row-detection-55/spec.md` (canonical, work mode `full-bug`); mirrored in `issue.md`
- Total AC items: 8
- Checked off (delivered): 8
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 8 | 8 | 0 | Checkbox-backed; authoritative for `full-bug`; already checked, matches PASS evaluation. |
| `issue.md` | 8 | 8 | 0 | Checkbox-backed mirror; not the work-mode-authoritative source; already checked. |

No source-file checkbox change was made because all eight items were already checked by the executor and each is independently confirmed PASS in this audit.
