# Fail-Before — Regression Tests (Issue #37)

Timestamp: 2026-05-29T21-59
Command: env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py::test_zero_volume_deduction_yields_dollar_derived_net_price_impact tests/test_mix_rate_impacts.py::test_single_sku_group_rolls_up_to_category_net_price_impact -p no:cacheprovider
EXIT_CODE: 1
Output Summary:
- Production file src/mix_rate_impacts.py was stashed to its pre-change state (git stash push -- src/mix_rate_impacts.py) so the regression tests run against the carried/summed-ratio code path.
- Result: 2 failed in 0.96s.
- Both AC3/AC4 regression tests fail against pre-change code. The pre-change code reads the carried/summed ratio column `Gross Sales Per Lb - Diff` (and `Net Rev Per Lb - Diff`), which the zero-volume-deduction fixture intentionally omits because the defect is about the recompute-from-dollars path. Failure: `KeyError: 'Gross Sales Per Lb - Diff'`.
- This is the expected [expect-fail] outcome for P1-T8: the pre-change code cannot produce the dollar-derived non-zero `Calc Net Price Impact`; it errors when reaching the carried summed-ratio column. After the production change recomputes the per-Lb/%GS metrics from the additive dollar/volume wide columns, these same tests pass (see pass-after evidence).
- Production change restored immediately after this run via git stash pop.
