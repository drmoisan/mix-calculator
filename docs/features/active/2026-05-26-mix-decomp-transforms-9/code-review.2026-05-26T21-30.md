# Code Review — mix-decomp-transforms (Issue #9)

- Timestamp: 2026-05-26T21-30
- Reviewer: feature-review agent
- Base: `main` @ `4c1e8faf8166c2ff1da680fb83dd3c4998adc187`
- Head: `feature/mix-decomp-transforms-9` @ `2932427f0dc91f59c03553c8b393dce0c79c2dc1`
- Scope: full feature-vs-base branch diff (Python: 10 new `src/` modules, 8 new test modules)

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: review-artifact MCP template tools are not
> available; this artifact uses the canonical headings directly.

## Executive Summary

The change adds a pure-transform Python/pandas pipeline that reproduces the
"LE v AOP Gross to Net Decomp" Power Query model over the loaded `aop`/`LE`
SQLite tables, plus a `mix-pipeline` CLI that runs imports and transforms
end-to-end. The implementation follows the repository's design principles:
pure transforms separated from I/O, all reads/writes routed through
`src.pandas_io`, loaders reused rather than duplicated, and modules decomposed
to stay under the 500-line limit. Typing is strict (Pyright 0/0), docstrings and
intent comments meet the self-explanatory-commenting policy, and the toolchain
passes cleanly with 100% line and branch coverage. No Blocking or Major findings
were identified. The findings below are Minor/Informational observations that do
not block merge.

Typed-Python review: all public functions carry complete parameter and return
type hints; `pandas`/`sqlite3` are imported under `TYPE_CHECKING` where only used
for annotations; no `Any` escape hatches and no suppressions were introduced.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | src/mix_pipeline.py | `_print_summary` (lines 227-246) | The `con` parameter is accepted but unused; the docstring states it is "retained for a consistent boundary signature." | Drop the unused parameter or compute row counts from the live connection so the parameter earns its place. | An unused parameter is a small readability/maintenance cost; the row counts are already derived from the in-memory frames. | `src/mix_pipeline.py:227-246` |
| Minor | tests/test_mix_lookups.py | fixture rows (e.g. lines 39, 54, 206) | The test fixture key `"SKU Descripiton"` is misspelled (also present in `test_mix_pivots.py`, `test_mix_q1.py`). | Correct the spelling to `"SKU Description"` if the production code consumes that column; if the column is intentionally unused by the unit under test, leave a comment noting the placeholder. | A misspelled column key in fixtures can mask a real column-name mismatch if the code later reads it; consistency aids maintenance. | `tests/test_mix_lookups.py:39,54,206`; `tests/test_mix_pivots.py`; `tests/test_mix_q1.py` |
| Informational | quality-tiers.yml | new entries block | The spec called for "seven new T2 entries"; ten were added because two helper modules and `mix_pipeline_run` were split out for the 500-line limit. | None required; the additional classifications are correct and consistent with the stated rationale. | The count deviation is benign and improves classification coverage. | `git diff quality-tiers.yml` |
| Informational | src/mix_rollups.py, src/mix_rate_impacts.py | module docstrings | The deliberate M-source deviations (`Customer Mix` vs M-source "Category Mix"; scalar `mix_rollup_4` subtraction) are documented in code as required by the spec. | None; this satisfies the spec's "document in code" requirement. | Confirms the spec's M-source-deviation documentation requirement is met. | `src/mix_rollups.py:15-18`; spec.md "M-source deviations" |

## Strengths Observed

- Separation of concerns: pure transforms (`mix_transforms`, `mix_lookups`,
  `mix_rate_impacts`, `mix_rollups`, `mix_q1`) contain no I/O; `mix_pipeline.main`
  is the sole I/O owner and orchestrates only.
- Divide-by-zero guards in `calc_ratios` use a strict `> 0` denominator test,
  matching the Power Query `CalcRatios` semantics described in the spec.
- Reuse of `pandas_io`, `etl_columns`, and the existing loaders avoids
  duplicated ingestion logic.
- Module decomposition (`_mix_transforms_helpers`, `_mix_rollups_helpers`,
  `mix_pipeline_run`) keeps every file under the 500-line limit while preserving
  cohesive module purpose.
- Error handling at the CLI boundary maps loader `ValueError`s to a clean
  non-zero exit with an operator message, consistent with the fail-fast policy.

## No-Blocker Statement

No Blocking findings. The two Minor findings are non-blocking quality
observations and may be addressed at the author's discretion.
