# Code Review: le-loader-required-vs-output-columns (#57)

**Review Date:** 2026-06-07
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57`
**Feature Folder Selection Rule:** Suffix `-57` matches the issue number in the branch/issue context.
**Base Branch:** `main` (merge-base `b655d81`, 2026-06-06T22:10:29-04:00)
**Head Branch:** `fix/loader-header-row-detection` (HEAD `3ae79b1`; #57 delta isolated via `git diff 721a1bf..HEAD`)
**Review Type:** Initial review

---

## Executive Summary

This change makes the protected LE loader require only the 23 must-have source columns and treat `YTD/YTG` and source `Super Category` as optional-by-name (located if present, tolerated if absent). It resolves the import failure where a `YTD/YTG`-less LE sheet raised `could not resolve required column(s): ['YTD/YTG']`, even though those two columns are never read for the output (`YTD/YTG` is dropped at emit; output `Super Category` is derived from `PPG`).

**What changed:**
- `src/_normalize_le_columns.py`: introduces `REQUIRED_COLUMNS` (23 = 5 text + 12 months + FY + 4 quarters + PPG) and `OPTIONAL_BY_NAME = ["YTD/YTG", "Super Category"]`; redefines `EXPECTED_COLUMNS = REQUIRED_COLUMNS`; rewrites `resolve_le_columns` to locate KEY plus each optional by normalized name (no fuzzy, no raise on absence), exclude located columns from the resolvable set, require only `REQUIRED_COLUMNS`, and carry located optionals into the selection only when present.
- `src/normalize_le.py`: `load_source` builds `columns_to_keep` from `REQUIRED_COLUMNS` then appends located optionals and KEY from the selection; the header-detection comment is updated to 23 tokens while `min_match=20` is unchanged. `normalize()` and `validate_tieouts()` are untouched.
- Tests: a new `tests/test_normalize_le_columns.py` (6 unit tests) plus 4 load/normalize tests (including a parity test) and 1 flat LE84Data-style import test.

The implementation mirrors the established AOP `load_aop`/`_load_aop_helpers` optional-by-name pattern, which keeps the codebase consistent. Toolchain is clean and the parity invariant is verified by a dedicated test.

**Top 3 risks:**
1. Parity regression for the standard full-column LE source — mitigated and verified by `test_full_column_source_output_parity_with_standard_fixture` (passes) plus the existing `set(frame.columns) == set(SOURCE_COLUMNS)` assertion.
2. An unupdated importer of LE `EXPECTED_COLUMNS` (now 25->23) breaking — mitigated; the sole external consumer `tests/test_etl_columns.py` uses LE `EXPECTED_COLUMNS` as both actual and expected argument, so it stays self-consistent; all 102 targeted tests pass.
3. A must-have column accidentally made optional — mitigated; `REQUIRED_COLUMNS` is an explicit list reviewed against `normalize()`/`validate_tieouts()` readers, and the missing-required negative test confirms a clear error.

**PR readiness recommendation:** **Go** — All toolchain checks pass, parity is verified, AOP/CI are untouched, and all eight acceptance criteria are met with no blocking findings.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Nit | `tests/test_normalize_le.py` | whole file | The file is 499 lines, one below the 500-line cap; further additions will require splitting. | Optional: when next extending LE pure-transform tests, move the new #57 load tests into `test_normalize_le_columns.py` or a new module. | Repository file-size cap is 500 lines; this file recurrently clusters near the cap. | `awk END{print NR}` = 499; persistent reviewer memory on normalize-le test clustering. |
| Info | `src/_normalize_le_columns.py` | lines 88-113 | `EXPECTED_COLUMNS` is redefined to alias `REQUIRED_COLUMNS` rather than removed; the dual name is retained for re-export/back-compat with `test_etl_columns.py` and the header-token set. | None; intentional and documented in the comment block. | Keeping `EXPECTED_COLUMNS` avoids breaking the sole external consumer and the header-detection token derivation. | Diff lines 88-113; survey `evidence/baseline/baseline-expected-columns-usage.md`. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The change reuses the existing KEY-location idiom for the two new optionals, keeping `resolve_le_columns` a single pass and consistent with the AOP module convention. The intent is well-documented: comments explain that `YTD/YTG` is dropped at emit and output `Super Category` is derived from `PPG`, so tolerating their absence is safe.
- The required set is an explicit, reviewable list (`REQUIRED_COLUMNS`) rather than a subtractive expression, which makes the must-have contract auditable against `normalize()` readers.
- `load_source` builds `columns_to_keep` in a deterministic order (required first, then located optionals in `OPTIONAL_BY_NAME` order, then KEY), preserving the prior selection/rename-in-one-pass behavior.

#### Typing and API notes

- New constants are typed `list[str]`; `optional_actual: dict[str, str]` and `located: set[...]` are correctly typed. `resolve_le_columns` keeps its `tuple[dict[str, str], str | None]` signature. No `Any` introduced. Both `REQUIRED_COLUMNS` and `OPTIONAL_BY_NAME` are added to `__all__` in the helper module and the re-exporting `normalize_le.py`, so the public surface is explicit.

#### Error handling and logging

- A genuinely missing required column still raises `ValueError` (propagated from `resolve_columns`) naming the column; verified by `test_missing_required_column_raises_value_error_naming_it`. The extra-column path remains a `logger.warning`, not a raise. No broad exception handling.

---

## Test Quality Audit

The added tests cover the optional-by-name contract at both the pure-helper level (`resolve_le_columns`) and the integration level (`load_source`/`normalize`), including the critical parity case and the AC-6 flat-sheet case. Coverage evidence shows the changed source modules at 100% line.

### Reviewed test and QA artifacts

- `tests/test_normalize_le_columns.py` — verifies the 23-column required set, the optional-by-name list, each-optional-absent, both-present-and-carried, and missing-required-raises. Pure in-memory column lists; deterministic.
- `tests/test_normalize_le.py` (parity test) — `pd.testing.assert_frame_equal` between the default standard source and an explicit full-column source confirms byte-identical output. This is the load-bearing parity guarantee for the change.
- `tests/test_normalize_le_header.py` — flat LE84Data-style sheet (header index 0, no YTD/YTG, no KEY) imports to the full 26-column `TARGET_COLUMNS` (AC-6).
- `evidence/regression-testing/parity-le-aop-suite.md` — 100 passed across LE + AOP suites; AOP unchanged.
- `evidence/qa-gates/coverage-delta.md` — changed modules at 100% line; documents the whole-suite branch movement as added branches, not a changed-line regression.

### Quality assessment prompts

- **Determinism:** No clock/RNG/network; workbooks via `io.BytesIO`; no temp files.
- **Isolation:** Each test targets one behavior with its own fresh inputs.
- **Speed:** Targeted subset 8.07s for 102 tests; whole suite 26.04s.
- **Diagnostics:** `pytest.raises(match="PPG")` and `assert_frame_equal` give precise failure output.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff contains only column constants, resolution logic, and tests. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess use in the delta. |
| Input validation at boundaries | ✅ PASS | `resolve_le_columns` requires the must-have set and raises a clear, column-naming error when a required column is absent. |
| Error handling remains explicit | ✅ PASS | `ValueError` for missing required columns; `logger.warning` for extras; no broad catch. |
| Configuration / path handling is safe | N/A | No path or configuration handling changed; the loader receives an already-resolved workbook buffer. |

---

## Research Log

No external research required. All conclusions are grounded in the branch diff, the repository rule files, the executor evidence artifacts, and independent toolchain re-runs. A grep across `src/` confirmed that no production code reads source `YTD/YTG` or source `Super Category`: `mix_lookups._LE_DROP` operates on the normalized output (where `Super Category` is derived from `PPG`), and `normalize()` line 270 sets output `Super Category` from `PPG`.

---

## Verdict

The #57 change is a focused, well-tested correction that aligns the protected LE loader with the existing schema-loader and AOP conventions for required-versus-output columns. The toolchain is clean, the parity invariant is explicitly verified, AOP and CI workflows are untouched, no suppressions were added, and the sole external `EXPECTED_COLUMNS` consumer remains self-consistent under the 23-column redefinition. There are no blocking or major findings; the two recorded findings are a Nit (test file size at 499/500) and an Info (intentional `EXPECTED_COLUMNS` alias). The change is ready for normal PR flow.
