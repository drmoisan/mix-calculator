# QA Gate — Acceptance Criteria Checkoff (AC1–AC14)

Timestamp: 2026-05-27T20-52
AC source files (full-feature mode): `spec.md` and `user-story.md`.

| AC | Description | Verifying test / artifact | Plan task | Status |
|---|---|---|---|---|
| AC1 | SKU table columns and grain | `test_build_mix_2_sku_bottomsup_columns_present`, `test_build_mix_2_sku_bottomsup_row_count_matches_detail` | P2-T4 | VERIFIED |
| AC2 | SKU normal tie-out | `test_build_mix_2_sku_bottomsup_normal_sku_mix_tieout` | P2-T5 | VERIFIED |
| AC3 | New Contribution branch | `test_build_mix_2_sku_bottomsup_new_contribution_active_when_new` | P2-T5 | VERIFIED |
| AC4 | Disco Contribution branch | `test_build_mix_2_sku_bottomsup_disco_contribution_active_when_lost` | P2-T5 | VERIFIED |
| AC5 | Zero-subtotal share guard | `test_build_mix_2_sku_bottomsup_zero_lbs_subtotal_share_is_zero` | P2-T5 | VERIFIED |
| AC6 | Classification join | `test_build_mix_2_sku_bottomsup_classification_joined_correctly` | P2-T5 | VERIFIED |
| AC7 | Category table columns and grain | `test_build_mix_3_category_bottomsup_columns_present`, `test_build_mix_3_category_bottomsup_row_count_matches_distinct_keys` | P2-T6 | VERIFIED |
| AC8 | Category tie-out | `test_build_mix_3_category_bottomsup_sku_mix_tieout` | P2-T6 | VERIFIED |
| AC9 | Customer table columns and grain | `test_build_mix_4_customer_bottomsup_columns_present`, `test_build_mix_4_customer_bottomsup_row_count_matches_distinct_keys` | P2-T6 | VERIFIED |
| AC10 | Customer tie-out | `test_build_mix_4_customer_bottomsup_sku_mix_tieout` | P2-T6 | VERIFIED |
| AC11 | SKU Mix identity (property) | `test_build_contribution_columns_sku_mix_equals_sum` (hypothesis) | P1-T3 | VERIFIED |
| AC12 | Pipeline persistence | `test_mix_pipeline_end_to_end` via extended `_DERIVED_TABLES` | P3-T3 | VERIFIED |
| AC13 | Confidentiality | `confidentiality-review.2026-05-27T20-52.md` | P5-T7 | VERIFIED |
| AC14 | Toolchain and limits | `black-final`, `ruff-final`, `pyright-final`, `pytest-coverage-final`, `coverage-delta`, `file-size-check` (all 2026-05-27T20-52) | P5-T1..T6 | VERIFIED |

Output Summary: All 14 acceptance criteria (AC1–AC14) are verified by passing tests
and recorded QA-gate artifacts. AC1–AC13 checked off in both `spec.md` and
`user-story.md`; AC14 (toolchain/limits) checked off in both. No unverified AC remains.
EXIT_CODE: 0
