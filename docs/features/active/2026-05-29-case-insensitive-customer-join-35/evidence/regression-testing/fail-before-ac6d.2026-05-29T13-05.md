# Fail-before — AC6d (LE-only retains LE casing)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py::test_build_aop_vs_le_le_only_keeps_le_casing -v`
EXIT_CODE: 0

WhyFailingRunImpossible: AC6d describes the existing pre-change behavior. With no AOP-side row for the customer, the pre-change literal-Customer pivot already emits the LE-side row keyed on `'WINCO'`, so the test passes today as well. The post-change behavior must continue to satisfy this assertion under the new pivot-then-display strategy.

SearchScope: `tests/test_mix_lookups.py`
SearchPatterns: `test_build_aop_vs_le_le_only_keeps_le_casing`
SearchResult: test passes both pre-change and post-change.

Alternative proof:
- The test is included in the standing regression suite (Phase 1 P1-T10 and Phase 3 P3-T3). Both runs MUST show this test PASS.
- This guards against a regression where the post-change implementation accidentally drops or mis-casing LE-only rows.

Output Summary:
- Test `test_build_aop_vs_le_le_only_keeps_le_casing` PASSES pre-change (1 passed). Recorded as fail-before exception dossier; AC6d is a regression guard for the new implementation rather than a behavior change.
