# Final QA — Coverage Delta (P3-T5, AC-Toolchain, CF1 cycle 3, #74)

Timestamp: 2026-06-17T13-40

| Metric | Baseline (P0-T6, pre-revert) | Post-change (P3-T4) | Delta |
|---|---|---|---|
| Line coverage | 98.27% | 98.27% | 0.00 |
| Branch coverage | 93.88% | 93.88% | 0.00 |
| Tests passed | 1058 | 1058 | 0 |

Thresholds: line >= 85% (met), branch >= 75% (met).

Changed-lines regression: none. This cycle reverts a single JSON line in
`src/schemas/default_aop.schema.json` (`"version": "3.0"` -> `"version": "2.0"`) and changes
no production logic. No Python source line changed, so there are no changed production lines to
regress. Coverage is unchanged from baseline. AC-Toolchain satisfied.
