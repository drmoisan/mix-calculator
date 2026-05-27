# Feature Audit — mix-decomp-transforms (Issue #9)

- Timestamp: 2026-05-26T21-30
- Reviewer: feature-review agent
- Work mode: `full-feature`

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: feature-audit MCP template tool is not
> available; this artifact uses the canonical headings directly.

## Scope and Baseline

- Base branch (resolved): `main` @ `4c1e8faf8166c2ff1da680fb83dd3c4998adc187`
- Head: `feature/mix-decomp-transforms-9` @ `2932427f0dc91f59c03553c8b393dce0c79c2dc1`
- Range: `4c1e8faf8166c2ff1da680fb83dd3c4998adc187..2932427f0dc91f59c03553c8b393dce0c79c2dc1`
- AC sources (full-feature): `user-story.md` (## Acceptance Criteria) and
  `spec.md` (## Definition of Done).
- Evidence: live toolchain run on HEAD (Black 0, Ruff 0, Pyright 0/0, Pytest 185
  passed / 100% line / 100% branch); source inspection of the new modules; diff
  scans for confidentiality, file size, and evidence-location compliance.

## Acceptance Criteria Inventory

From `user-story.md` (10 criteria):

1. Python transformation pipeline reproduces the Power Query queries and persists each derived table to SQLite.
2. All nineteen derived tables are persisted (enumerated list).
3. Single CLI entry point (`mix-pipeline`) runs both ETL imports and the transform pipeline end-to-end, reusing the loaders.
4. `SKU_LU` loaded via `--skulu-input`/`--skulu-sheet`, renaming `International`->`Country`, mapping `0`->`US`, `1`->`Canada`.
5. Helper transforms (`CalcRatios`, `ClassifyTable`, `StackPivot`, `AddRatios`, `FillZeroWithAvg`, `NegateColumn`) implemented as pure, independently tested, no I/O.
6. Classification matches Power Query: SKU-level then customer-SKU level, exact zero tests.
7. Mix decomposition rollups tie out within `1e-9` (ratio) / exactly (integer).
8. `Mix-3-Customer` uses `Customer Mix`; `Mix-4-Country` subtracts scalar `mix_rollup_4`.
9. No real customer/SKU/category/price/discount values; only fabricated values.
10. No file exceeds 500 lines.
11. Toolchain passes single clean run: Black, Ruff, Pyright (strict), Pytest >= 85% line / >= 75% branch.

(Note: the user-story list contains 10 numbered checkbox items; the toolchain
item is item 10 in that file. Numbering above expands the enumerated derived
tables and toolchain for clarity. The Definition of Done in `spec.md` carries 13
overlapping checkboxes plus 6 seeded test-condition items.)

## Acceptance Criteria Evaluation

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Pipeline reproduces PQ queries, persists derived tables | PASS | `mix_pipeline.main` + `mix_pipeline_run.run_transforms` build and persist all derived tables via `pandas_io.write_table`; `test_mix_pipeline.py` exercises the end-to-end path (185 tests pass). |
| 2 | All nineteen derived tables persisted | PASS | `mix_pipeline` persists `le_wide, aop_wide, customer_lu, aop_norm, le_norm, aop_vs_le, mix_base` (7) + `run_transforms` returns `rate_impacts, mix_rollup_1, mix_1_sku, mix_rollup_2, mix_2_category, mix_rollup_3, mix_3_customer, mix_rollup_4, mix_4_country, mix_0_detail, q1_results_by_sku` (11); `sku_lu` persisted by `load_skulu.persist_skulu` in the import step = 19 total. |
| 3 | Single CLI reuses loaders end-to-end | PASS | `mix_pipeline._import_sources` reuses `normalize_le`, `load_aop`, `load_skulu`; `build_parser` exposes `mix-pipeline` with `--input`/`--output`. No duplicated ingestion. |
| 4 | `SKU_LU` load + rename + country mapping | PASS | `load_skulu.load_skulu` renames `International`->`Country`, casts to text, maps `{"0":"US","1":"Canada"}`; `--skulu-input` defaults to `--input`, `--skulu-sheet` defaults `"SKU_LU"`; `test_load_skulu.py` covers rename/map/casts. |
| 5 | Six helper transforms pure, tested, no I/O | PASS | `negate_column`, `calc_ratios`, `classify_table`, `stack_pivot`, `add_ratios`, `fill_zero_with_avg` in `mix_transforms`/`_mix_transforms_helpers` with no I/O; `test_mix_transforms.py` covers each (100% coverage). |
| 6 | Two-level classification, exact zero tests | PASS | `classify_table` applies SKU-level (inactive/eliminated/new/exists) then customer-SKU level (inactive/normal/lost distribution/new distribution); `test_mix_transforms.py` exercises every branch including exact-zero cases. |
| 7 | Rollups tie out (1e-9 ratio / exact integer) | PASS | `test_mix_rollups.py` (338 lines, sum-of-detail == rollup assertions); spec tie-out tolerance documented; 100% coverage on the rollup chain. |
| 8 | `Customer Mix` label; scalar `mix_rollup_4` subtraction | PASS | `mix_rollups` module docstring and `build_mix_3_customer`/`build_mix_4_country` document and implement the deviation; `mix_rollup_4` computed as scalar `float` and broadcast-subtracted. |
| 9 | No confidential values; only fabricated | PASS | Only fabricated literals present (Acme Foods, Globex Market, SKU-001/002/003, Widget A/B, Category X/Y); no price/discount literals; see policy-audit Confidentiality section. |
| 10 | No file exceeds 500 lines | PASS | Largest file 388 lines (`_mix_transforms_helpers.py`); all 18 changed Python files <= 388. |
| 11 | Toolchain passes single clean run + coverage | PASS | Verified live on HEAD: Black exit 0, Ruff exit 0, Pyright 0/0/0, Pytest 185 passed, 100% line / 100% branch. |

Spec Definition-of-Done items map to the same evidence above (acceptance
criteria mapped to tests, edge cases covered, docs updated incl. README,
toolchain pass, end-to-end CLI, helpers pure/tested, rollups tie out, 500-line
limit, coverage, no confidential values, seven+ new T2 entries). All evaluate
PASS. The six seeded test-condition items in `spec.md` are covered by
`test_mix_transforms.py`, `test_mix_rollups.py`, and `test_mix_pipeline.py`.

## Summary

All acceptance criteria evaluate PASS. The feature is functionally complete
relative to the baseline, the toolchain passes cleanly, coverage exceeds the
uniform 85%/75% thresholds (100%/100%), and the hard confidentiality constraint
is satisfied. No criterion is PARTIAL, FAIL, or UNVERIFIED. No remediation is
triggered by the acceptance-criteria evaluation.

## Acceptance Criteria Check-off

All criteria in `user-story.md` and `spec.md` were already checked `[x]` by the
executor. This review independently verified each as PASS; no source-file
checkbox changes were required (all already reflect delivered, verified work).
No phantom criteria were added.

### Acceptance Criteria Status

- Source: `docs/features/active/2026-05-26-mix-decomp-transforms-9/user-story.md`, `docs/features/active/2026-05-26-mix-decomp-transforms-9/spec.md`
- Total AC items: 10 (user-story) + 13 DoD + 6 seeded conditions (spec) = 29
- Checked off (delivered): 29
- Remaining (unchecked): 0
- Items remaining: none

Note: `issue.md` retains a separate "## Acceptance Criteria (early draft)"
section with unchecked boxes. For `full-feature` work mode, `issue.md` is not an
authoritative AC source, so those draft boxes are intentionally left unchanged.
