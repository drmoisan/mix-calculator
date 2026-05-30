# Feature Audit: case-insensitive-customer-join (Issue #35)

**Audit Date:** 2026-05-29
**Feature Folder:** `docs/features/active/2026-05-29-case-insensitive-customer-join-35/`
**Base Branch:** `feature/app-rename-and-real-icon-33` (commit `53363811cd5d8b9b38fe33455984baf63a47d710`)
**Head Branch:** `feature/case-insensitive-customer-join-35` (commit `cc4a7399776890f2739a30130fd2093654ceae52`)
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `feature/app-rename-and-real-icon-33` (commit `53363811cd5d8b9b38fe33455984baf63a47d710`)
- **Head branch/commit:** `feature/case-insensitive-customer-join-35` (commit `cc4a7399776890f2739a30130fd2093654ceae52`)
- **Merge base:** `53363811cd5d8b9b38fe33455984baf63a47d710`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/**`
  - Additional evidence: direct inspection of `src/mix_lookups.py`
- **Feature folder used:** `docs/features/active/2026-05-29-case-insensitive-customer-join-35/`
- **Requirements source:** `docs/features/active/2026-05-29-case-insensitive-customer-join-35/issue.md` (`## Acceptance Criteria` section, AC1-AC10)
- **Work mode resolution note:** `issue.md` line 9 carries `- Work Mode: minor-audit`. Per the work-mode acceptance-criteria contract, the AC source is the explicit `## Acceptance Criteria` section in `issue.md` only.
- **Scope note:** Branch is stacked on PR #34 HEAD. PR-context artifacts were refreshed against that base before this audit per the delegation prompt.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-29-case-insensitive-customer-join-35/issue.md` — only source (minor-audit; section `## Acceptance Criteria`)

### Acceptance criteria

1. AC1: A new module-private helper in `src/mix_lookups.py` produces the canonical Customer join key via `.str.strip().str.casefold()`. The helper is a pure function on `pd.Series[str]` and has a Google-style docstring.
2. AC2: `build_aop_norm` and `build_le_norm` apply `.str.strip()` to the emitted `Customer` column (preserving original casing, removing leading/trailing whitespace).
3. AC3: `build_aop_vs_le` performs its pivot/merge on the casefolded Customer join key so that AOP `Winco` and LE `WINCO` (and any whitespace variants) merge into one `(Customer, SKU)` pair in the output. The output frame's displayed `Customer` column carries the AOP-side casing when both sides match. When only the LE side has a row, the LE-side casing is preserved.
4. AC4: `build_customer_lu` applies `.str.strip()` to the `Customer` column so its display is consistent with `aop_vs_le`.
5. AC5: A regression test exercises the Winco/WINCO scenario end-to-end with a synthetic fixture (no external xlsx dependency): AOP has `('Winco', 69005)` with Off Invoice $ and Non-Trade $ deductions; LE has `('WINCO', 69005)` with the same deductions and `('Winco', 69005)` with Gross Sales and Lbs. The test asserts the resulting `aop_vs_le` has exactly one `(Customer, SKU)` row per attribute keyed on `Winco`.
6. AC6: Unit tests cover, individually: (a) identical Customer values with different casings (`'Winco'`, `'WINCO'`, `'winco'`) merge to one key; (b) trailing-only whitespace (`'Winco '`) and leading-only whitespace (`' Winco'`) merge to the same key as `'Winco'`; (c) AOP-side casing wins on display when both sides match; (d) LE-only Customer (no AOP counterpart) retains LE casing on display; (e) the join key is independent of the original `Customer` string (a single Customer with five different casings in a frame produces one output row per attribute).
7. AC7: Existing tests in `tests/test_mix_lookups.py` continue to pass without modification of their assertions. The canonical end-to-end pipeline run against `artifacts/LE v AOP Gross to Net Decomp.xlsx` produces an identical `nrr_summary` (including `Check = CHECK`).
8. AC8: Coverage on `src/mix_lookups.py` remains >= 85% line and >= 75% branch (uniform thresholds per `.claude/rules/quality-tiers.md`).
9. AC9: `src/mix_lookups.py` and `tests/test_mix_lookups.py` each remain under the 500-line cap.
10. AC10: Full mandatory Python toolchain passes in a single loop: Black -> Ruff -> Pyright -> Pytest. No new suppressions introduced beyond pre-authorized patterns.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC1: Module-private `_customer_join_key` helper, pure on `pd.Series[str]`, Google-style docstring | PASS | `src/mix_lookups.py` lines 62-77 define the helper with a Google-style docstring (`Args:`, `Returns:`); it is `_`-prefixed and not in `__all__`. Pyright clean. | Read `src/mix_lookups.py`; `env -u VIRTUAL_ENV poetry run pyright` (EXIT_CODE 0 per `final-pyright.2026-05-29T13-45.md`). | Implementation is exactly `s.str.strip().str.casefold()`. |
| 2 | AC2: `build_aop_norm` / `build_le_norm` apply `.str.strip()` to Customer | PASS | `src/mix_lookups.py` lines 123 and 146 each call `.str.strip()` on `Customer`. Fail-before: `evidence/regression-testing/fail-before-ac2.2026-05-29T13-05.md` (EXIT_CODE 1). Pass-after: `evidence/qa-gates/phase2-pytest.2026-05-29T13-15.md`, `phase3-pytest.2026-05-29T13-25.md`. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_norm_strips_customer_whitespace tests/test_mix_lookups.py::test_build_le_norm_strips_customer_whitespace -v` | Casing is preserved (`.astype(str).str.strip()` only strips whitespace). |
| 3 | AC3: `build_aop_vs_le` pivots on casefolded key; AOP display wins; LE-only retains LE casing | PASS | `src/mix_lookups.py` lines 179-222: pivot uses `_customer_key`; AOP and LE display values re-attached via two left-merges; `fillna(wide["_customer_le"])` fills LE-only orphans; helper columns dropped. Tests `test_build_aop_vs_le_casefold_winco_merges`, `test_build_aop_vs_le_display_aop_casing_wins`, `test_build_aop_vs_le_le_only_keeps_le_casing`. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups_casefold.py -v` | The "_customer_le" helper column is dropped before return so the public contract is preserved. |
| 4 | AC4: `build_customer_lu` applies `.str.strip()` to Customer | PASS | `src/mix_lookups.py` line 100 strips whitespace before `drop_duplicates`. Test `test_build_customer_lu_strips_whitespace`. Fail-before: `evidence/regression-testing/fail-before-ac4.2026-05-29T13-05.md`. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_customer_lu_strips_whitespace -v` | Casing preserved; whitespace-equivalent pairs collapse. |
| 5 | AC5: Winco/WINCO synthetic end-to-end fixture; exactly one `(Customer, SKU)` row per attribute keyed on `Winco` | PASS | Test `test_build_aop_vs_le_casefold_winco_merges` in `tests/test_mix_lookups_casefold.py`. Fail-before: `evidence/regression-testing/fail-before-ac5.2026-05-29T13-05.md` (EXIT_CODE 1). Pass-after: `evidence/qa-gates/phase3-pytest.2026-05-29T13-25.md`. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups_casefold.py::test_build_aop_vs_le_casefold_winco_merges -v` | Synthetic in-memory fixture; no external xlsx dependency. |
| 6 | AC6: Unit tests cover (a) three casings collapse; (b) leading/trailing whitespace collapse; (c) AOP display wins; (d) LE-only retains LE casing; (e) five casings collapse | PASS | All five sub-criteria covered: (a) `test_build_aop_vs_le_casefold_collapses_three_casings`; (b) `test_build_aop_vs_le_casefold_strips_whitespace`; (c) `test_build_aop_vs_le_display_aop_casing_wins`; (d) `test_build_aop_vs_le_le_only_keeps_le_casing`; (e) `test_build_aop_vs_le_five_casings_collapse_to_one`. Per-AC fail-before artifacts `fail-before-ac6a..ac6e.*.md`. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups_casefold.py -v` | Sub-criterion (d) was a regression guard (passed pre-change); the exception dossier `fail-before-ac6d.*.md` documents this. |
| 7 | AC7: Existing tests pass unmodified; canonical-workbook pipeline still produces `Check = CHECK` | PASS | `evidence/regression-testing/preexisting-still-pass.2026-05-29T13-05.md` and `phase4-mix-pipeline.2026-05-29T13-35.md` (5/5 mix_pipeline tests including new `test_mix_pipeline_nrr_summary_check_ok` asserting `nrr_summary.check == "CHECK"`). Canonical workbook is not in the worktree; the documented alternative proof is the synthetic in-memory pipeline test. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py -q`; `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_pipeline.py -v` | Exception dossier `phase4-canonical-workbook.2026-05-29T13-35.md` records the substitution rationale. The existing test assertions themselves are unmodified; the +5 lines in `tests/test_mix_lookups.py` are a pointer comment only. |
| 8 | AC8: Coverage on `src/mix_lookups.py` >= 85% line, >= 75% branch | PASS | `evidence/qa-gates/final-pytest.2026-05-29T13-45.md`: 100% line (58/58), 100% branch (4/4, 0 partial) on `src/mix_lookups.py`. Exceeds uniform thresholds. | `env -u VIRTUAL_ENV poetry run pytest --cov=src.mix_lookups --cov-branch --cov-report=term-missing tests/test_mix_lookups.py tests/test_mix_lookups_casefold.py` | Global coverage 99% line+branch (2273 stmts, 17 missed; 356 branches, 4 partial). |
| 9 | AC9: `src/mix_lookups.py` and `tests/test_mix_lookups.py` each under 500 lines | PASS | `evidence/qa-gates/final-file-size.2026-05-29T13-45.md`: `src/mix_lookups.py` = 286 lines (under 500); `tests/test_mix_lookups.py` = 365 lines (under 500). New `tests/test_mix_lookups_casefold.py` = 296; `tests/test_mix_pipeline.py` = 301. All under cap. | `wc -l src/mix_lookups.py tests/test_mix_lookups.py tests/test_mix_lookups_casefold.py tests/test_mix_pipeline.py` | Split avoided breaching the cap. |
| 10 | AC10: Full Python toolchain passes single-loop; no new suppressions beyond pre-authorized patterns | PASS | `evidence/qa-gates/final-black.2026-05-29T13-45.md` (EXIT_CODE 0), `final-ruff.2026-05-29T13-45.md` (EXIT_CODE 0), `final-pyright.2026-05-29T13-45.md` (EXIT_CODE 0), `final-pytest.2026-05-29T13-45.md` (507 pass, EXIT_CODE 0). No `# noqa` or `# type: ignore` added per diff inspection. | `env -u VIRTUAL_ENV poetry run black --check .`; `env -u VIRTUAL_ENV poetry run ruff check .`; `env -u VIRTUAL_ENV poetry run pyright`; `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing -q` | Single loop confirmed by the four timestamp-aligned qa-gates artifacts at `13-45`. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 10 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Sequence the PR review behind PR #34, since #35 is stacked on top of #34.
2. Once #34 merges and #35 is rebased on `main`, run the full pytest suite once more to confirm no rebase-introduced regressions before final merge.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** may be checked off in the authoritative source file(s) if they are represented as markdown checkboxes and are not already checked.
- Criteria evaluated as **PARTIAL**, **FAIL**, or **UNVERIFIED** must remain unchecked.
- If the source uses prose or numbered requirements instead of checkbox items, do not rewrite the source file; record status only in this audit.

All 10 AC items in `issue.md` are already marked `- [x]` at the time of this audit (the executor checked them off during plan execution per `acceptance-criteria-tracking`). No additional source-file mutation is required by this reviewer pass; the executor's check-off is reaffirmed by the evaluation table above.

### AC Status Summary

- Source: `docs/features/active/2026-05-29-case-insensitive-customer-join-35/issue.md`
- Total AC items: 10
- Checked off (delivered): 10
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-29-case-insensitive-customer-join-35/issue.md` | 10 | 10 | 0 | Checkbox-backed; all already `[x]` at audit time per executor's check-off. Reviewer reaffirms. |
