# AC verification — Issue #35

Timestamp: 2026-05-29T13-45
AC source: `docs/features/active/2026-05-29-case-insensitive-customer-join-35/issue.md` (`## Acceptance Criteria`)

| AC | Status | Evidence |
|----|--------|----------|
| AC1: Module-private `_customer_join_key` helper, pure on `pd.Series[str]`, Google-style docstring | PASS | `src/mix_lookups.py` lines 62-79 (helper). Phase 3 P3-T1 implementation; Pyright clean in `evidence/qa-gates/final-pyright.2026-05-29T13-45.md`. |
| AC2: `build_aop_norm` / `build_le_norm` apply `.str.strip()` to Customer | PASS | Fail-before: `evidence/regression-testing/fail-before-ac2.2026-05-29T13-05.md`. Pass-after: `evidence/qa-gates/phase2-pytest.2026-05-29T13-15.md` and `evidence/qa-gates/phase3-pytest.2026-05-29T13-25.md`. Tests `test_build_aop_norm_strips_customer_whitespace`, `test_build_le_norm_strips_customer_whitespace`. |
| AC3: `build_aop_vs_le` pivots on casefolded key; AOP-side casing wins on display; LE-side casing preserved on LE-only orphans | PASS | Phase 3 P3-T1 implementation. Fail-before: `fail-before-ac5.*.md`, `fail-before-ac6a..ac6e.*.md`. Pass-after: `evidence/qa-gates/phase3-pytest.2026-05-29T13-25.md`. |
| AC4: `build_customer_lu` applies `.str.strip()` to Customer | PASS | Fail-before: `evidence/regression-testing/fail-before-ac4.2026-05-29T13-05.md`. Pass-after: `evidence/qa-gates/phase2-pytest.2026-05-29T13-15.md`. Test `test_build_customer_lu_strips_whitespace`. |
| AC5: Synthetic Winco/WINCO Off-Invoice + Non-Trade end-to-end fixture; exactly one `(Customer, SKU)` row per attribute keyed on `Winco` | PASS | Fail-before: `evidence/regression-testing/fail-before-ac5.2026-05-29T13-05.md`. Pass-after: `evidence/qa-gates/phase3-pytest.2026-05-29T13-25.md`. Test `test_build_aop_vs_le_casefold_winco_merges`. |
| AC6a: Three casings collapse to one key | PASS | `fail-before-ac6a.*.md` + `phase3-pytest.*.md`. Test `test_build_aop_vs_le_casefold_collapses_three_casings`. |
| AC6b: Leading/trailing whitespace merges | PASS | `fail-before-ac6b.*.md` + `phase3-pytest.*.md`. Test `test_build_aop_vs_le_casefold_strips_whitespace`. |
| AC6c: AOP-side casing wins on display | PASS | `fail-before-ac6c.*.md` + `phase3-pytest.*.md`. Test `test_build_aop_vs_le_display_aop_casing_wins`. |
| AC6d: LE-only retains LE casing on display | PASS | Fail-before exception dossier `fail-before-ac6d.*.md` (test passes pre-change as a regression guard); pass-after `phase3-pytest.*.md`. Test `test_build_aop_vs_le_le_only_keeps_le_casing`. |
| AC6e: Five casings collapse to one row | PASS | `fail-before-ac6e.*.md` + `phase3-pytest.*.md`. Test `test_build_aop_vs_le_five_casings_collapse_to_one`. |
| AC7: Existing tests pass unmodified; canonical-workbook pipeline still produces `Check = CHECK` | PASS | `evidence/qa-gates/phase4-mix-pipeline.2026-05-29T13-35.md` (5/5 mix_pipeline tests pass; new `test_mix_pipeline_nrr_summary_check_ok` asserts `nrr_summary.check == "CHECK"`). Canonical workbook itself is not in the worktree; exception dossier `evidence/qa-gates/phase4-canonical-workbook.2026-05-29T13-35.md` records the alternative proof. |
| AC8: `src/mix_lookups.py` line >= 85%, branch >= 75% | PASS | `evidence/qa-gates/final-pytest.2026-05-29T13-45.md`: 100% line, 100% branch on `src/mix_lookups.py`. |
| AC9: `src/mix_lookups.py` and `tests/test_mix_lookups.py` each under 500-line cap | PASS | `evidence/qa-gates/final-file-size.2026-05-29T13-45.md`: 286 + 365 lines. Case-insensitive tests live in the new `tests/test_mix_lookups_casefold.py` (296 lines) to keep both files under the cap. |
| AC10: Full Python toolchain clean in a single loop; no new suppressions | PASS | `evidence/qa-gates/final-black.*.md`, `final-ruff.*.md`, `final-pyright.*.md`, `final-pytest.*.md` (all EXIT_CODE 0). No `# noqa` or `# type: ignore` added. |

Summary: All 10 acceptance criteria PASS. Every row carries a canonical evidence path under `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/`.
