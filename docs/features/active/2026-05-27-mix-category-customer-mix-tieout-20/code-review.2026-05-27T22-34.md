# Code Review: mix-category-customer-mix-tieout (#20)

**Review Date:** 2026-05-27
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`
**Feature Folder Selection Rule:** Folder name suffix `-20` matches issue #20 and the branch name `fix/mix-category-customer-mix-tieout-20`.
**Base Branch:** `main` (commit `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`)
**Head Branch:** `fix/mix-category-customer-mix-tieout-20` (commit `98399b6b61efae4eb4fa9784925a8975dcb356ca`)
**Review Type:** Initial review

---

## Executive Summary

The branch corrects the issue #20 mix tie-out defect at its source. `build_mix_2_category`, `build_mix_3_customer`, and `build_mix_4_country` now aggregate the unfiltered `mix_base` at their own granularity (`{Customer, Country}`, `{Country}`, and an all-rows synthetic key respectively), while the rollup-subtraction target remains the prior finer layer's summed `Calc Net Price Impact`. The unused `unstack_to_long` helper and its `_STAGE_SCENARIOS` constant were removed from `src/_mix_rollups_helpers.py`, simplifying the shared reshape body. `src/mix_pipeline_run.py` was rewired to pass `mix_base` to the three builders. `mix_1_sku` is unchanged. `tests/mix_bottomsup_fixtures.py::build_chain` was updated as a cross-feature reconciliation with the merged PR #22.

The implementation is small, focused, and well-typed. The Python toolchain (Black, Ruff, Pyright, Pytest with branch coverage) runs clean in a single pass and produces 100% line/branch coverage on all three changed source files. The reviewer reran the end-to-end pipeline against the confidential workbook and independently confirmed the `nrr_summary` `check` column resolves to `CHECK` (no `ERROR` token present), satisfying AC7. The BottomsUp test suite (19 tests) passes, validating the cross-feature reconciliation.

**What changed:**
Three production files (`src/mix_rollups.py`, `src/_mix_rollups_helpers.py`, `src/mix_pipeline_run.py`) and two test files (`tests/test_mix_rollups.py`, `tests/mix_bottomsup_fixtures.py`). Output table schemas are unchanged; only the previously-incorrect category/customer/country mix values change. No CLI, dependency, or schema changes.

**Top 3 risks:**
1. `tests/test_mix_rollups.py` is 562 lines, 62 over the 500-line file-size limit; the limit explicitly applies to test code and no listed exception applies.
2. The end-to-end and per-layer tie-out evidence depends on a confidential, gitignored workbook. CI cannot rerun those checks; trust is anchored on the reviewer-reproduced `CHECK` result plus the unit-level single-scenario retention and NPI-minus-rollup identity tests, which are reproducible.
3. The country layer adds a synthetic `_all` key to the `mix_base` copy before staging and drops it after. The implementation copies the frame and drops the column on the stage output, so the source frame is not mutated; this was verified by inspection but is worth a maintainer comment in future refactors if more layers adopt the pattern.

**PR readiness recommendation:** **Needs Revision** — Split `tests/test_mix_rollups.py` to bring every file under the 500-line limit, then re-run the Python toolchain. All other findings are non-blocking.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocker | `tests/test_mix_rollups.py` | whole file (562 lines) | Test file exceeds the 500-line limit by 62 lines. `general-code-change.md` explicitly states the limit applies to "production code, test code, or reusable script file"; none of the documented exceptions (throwaway scripts, raw text fixtures, Markdown) apply. | Extract the issue #20 single-scenario retention and NPI-minus-rollup identity tests into a sibling module (e.g. `tests/test_mix_rollups_tieout.py`), or factor the shared fixtures into a `tests/_mix_rollups_fixtures.py` helper module. Re-run Black, Ruff, Pyright, Pytest. | The 500-line limit is a hard cap on cohesive maintainability; the violation is mechanical to fix without touching production behavior or coverage. | `wc -l tests/test_mix_rollups.py` returns 562; git baseline at merge-base is 338 lines. |
| Info | `src/mix_rollups.py` | `build_mix_4_country` (lines 203-236) | The country builder mutates a `mix_base.copy()` by adding a `_all = "all"` column to drive the shared stage, then drops it on the stage output. The source frame is not mutated (the copy is local), and the synthetic key is removed before the result is returned, but the inline comment ("Drop the synthetic key after staging") is on the post-stage line rather than the pre-copy intent. | Optional: add a one-line meta-what comment above the `base_with_all = mix_base.copy()` line stating the purpose ("Collapse to a single all-rows group via a synthetic key so the shared stage can be reused without a separate all-rows code path"). | Improves intent-comment alignment for future maintainers; no behavior change. | Inspection of `src/mix_rollups.py` lines 225-232. |
| Info | `src/_mix_rollups_helpers.py` | docstring + import block | Moving `pandas` to `TYPE_CHECKING` and removing `unstack_to_long`/`_STAGE_SCENARIOS` is a clean reduction; the module dropped from 49 to 30 covered statements. | None — record only. | Confirms dead code was removed rather than dormant, and the module remains import-cycle-free. | `git diff` for `src/_mix_rollups_helpers.py`; reviewer coverage rerun shows 30 statements. |
| Info | `tests/mix_bottomsup_fixtures.py` | `build_chain` (lines ~280-290) | Cross-feature reconciliation correctly passes `mix_base` to the changed builders, with an inline comment naming issue #20. The 19 BottomsUp tests pass under reviewer rerun. | None. | Demonstrates the cross-feature edge was handled deliberately rather than incidentally. | `poetry run pytest -k "bottomsup or BottomsUp"` → 19 passed. |

No Major or Minor findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The fix targets the root cause precisely: each coarser layer now sources volume/revenue from the unfiltered `mix_base` at its own granularity, which is the smallest change that satisfies the NPI-minus-rollup identity and retains single-scenario volume.
- Removing `unstack_to_long` and `_STAGE_SCENARIOS` eliminates a fragile per-row reconstruction loop and a constant whose only consumer disappeared. Coverage of `_mix_rollups_helpers.py` dropped from 49 to 30 statements with no behavior loss.
- The country builder reuses the shared `build_mix_stage` body via a synthetic `_all` key rather than adding a parallel all-rows code path. The synthetic key is dropped before the result is returned and the input frame is not mutated (a local `.copy()` is used).
- Module docstrings were updated to describe the unfiltered-`mix_base` sourcing decision and explicitly call out issue #20, which gives future maintainers a clear motivation pointer.
- All builders remain pure (I/O-free); `run_transforms` performs no I/O.

#### Typing and API notes

- Builder signatures take `mix_base: pd.DataFrame` plus the rollup target as keyword-positional arguments with explicit types; `build_mix_rollup_4` continues to return `float`. No `Any` is introduced.
- Pyright runs clean across all five changed files (reviewer rerun: 0 errors, 0 warnings, 0 informations).
- No new public Python API surface was added; the builders' callers (`run_transforms`, `tests`) were updated in lockstep.

#### Error handling and logging

- No new error-handling code is needed for this value-correcting fix. The builders fail fast on missing columns via pandas `KeyError`, matching the existing pattern.
- No `print` statements or ad-hoc logging were added. No suppressions (`# noqa`, `# type: ignore`) were introduced.

---

## Test Quality Audit

The added tests are the strongest part of this change. They prove the issue #20 regression-fix invariant at the unit level with fabricated inputs, so they are deterministic and reproducible without the confidential workbook.

### Reviewed test and QA artifacts

- `tests/test_mix_rollups.py::test_category_layer_retains_single_scenario_volume` — verifies the `{Customer, Country}` group LE volume equals the unfiltered `mix_base` sum, proving the new-in-LE single-scenario line reaches the category aggregate. Strong regression guard.
- `tests/test_mix_rollups.py::test_customer_layer_retains_single_scenario_volume` — same assertion at `{Country}` granularity for the customer layer.
- `tests/test_mix_rollups.py::test_layer_mix_equals_full_aggregation_minus_rollup` — independently recomputes the expected NPI from the unfiltered `mix_base` and verifies `Category Mix == layer NPI - rollup-2 NPI` and `Customer Mix == layer NPI - rollup-3 NPI` row-by-row. Directly pins AC2.
- `tests/test_mix_rollups.py::test_build_mix_stage_keeps_only_nonzero_lbs_lines` — preserves the stage's nonzero-Lbs filter behavior, ensuring the fix does not silently weaken the filter that the SKU layer relies on.
- `tests/mix_bottomsup_fixtures.py::build_chain` — cross-feature reconciliation; the 19 BottomsUp tests pass with the new `mix_base`-based chain.
- `evidence/qa-gates/pytest-final-reconciled.2026-05-27T22-26.md` — executor pytest run, 220 passed.
- `evidence/qa-gates/coverage-delta.2026-05-27T22-19.md` — 100% line / 100% branch on changed source, no regression.
- `evidence/regression-testing/fail-before.2026-05-27T22-11.md` and `pass-after.2026-05-27T22-17.md` — fail-before/pass-after evidence for the regression tests.
- `evidence/regression-testing/e2e-run.2026-05-27T22-27.md` and `nrr-check.2026-05-27T22-27.md` — end-to-end pipeline run and `nrr_summary` `check = CHECK`; reproduced by the reviewer.
- `evidence/regression-testing/tieout.2026-05-27T22-27.md` — per-layer tie-out evidence (executor). The reviewer attempted an independent tie-out probe against the workbook; the probe's naive column-sum methodology produced a false FAIL on the out-of-scope, known-good SKU layer, indicating the probe is non-authoritative rather than evidence of regression. The executor's documented per-layer mapping (including the AC8 mapping from `mix_3_customer["Customer Mix"]` to the workbook's mislabeled "Category Mix" column per issue #9) is the authoritative source.

### Quality assessment prompts

- **Determinism:** All changed tests use in-memory pandas DataFrames built from fabricated labels (`Acme Foods`, `Globex Market`, `Widget 1/2/3/4`, `Category X/Y/Z`, `US`, `Canada`). No clock, RNG, network, or filesystem dependency.
- **Isolation:** One behavior per test; each rebuilds its own fixture.
- **Speed:** Full 220-test suite runs in 20.48s under reviewer rerun.
- **Diagnostics:** Assertions compare against independently recomputed expected values (e.g. `_unfiltered_group_lbs_le`, `build_mix_stage`), so failures localize to the specific layer/group rather than to a single global tie-out check.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff inspection found no API keys, tokens, or `.env` material. The confidential workbook is referenced only by gitignored filename and is not committed. |
| No unsafe subprocess or command construction | ✅ PASS | No `subprocess`, `os.system`, or shell construction added to changed code. |
| Input validation at boundaries | ✅ PASS | Builders consume the already-validated `mix_base` frame; the pipeline runner remains I/O-free. The CLI surface is unchanged. |
| Error handling remains explicit | ✅ PASS | No broad `except` or silenced exceptions added. The fail-fast pandas semantics are preserved. |
| Configuration / path handling is safe | ✅ PASS | No new configuration keys, paths, or schema entries. |
| Confidentiality of source data | ✅ PASS | Diff inspection of all newly added doc/evidence lines for currency-magnitude figures returned no matches; test fixtures use fabricated labels only; row counts in e2e evidence are structural metadata (table shapes), not confidential derived aggregates. |

---

## Research Log

No external research was required. The fix is supported entirely by the in-repo `issue.md` and `spec.md` root-cause analysis, the executor's evidence under `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/`, the merged PR #22 BottomsUp tests, and the reviewer's reruns of the Python toolchain and the end-to-end pipeline.

---

## Verdict

The change is a correct, focused, well-tested fix for the documented root cause of issue #20, with strong unit-level regression coverage for the single-scenario retention and NPI-minus-rollup identity invariants, and an independently reproduced end-to-end `CHECK` result. The only obstacle to a clean Go is the 562-line `tests/test_mix_rollups.py`, which is 62 lines over the 500-line file-size limit and must be split before merge. Once the file-size violation is resolved this change is ready for normal PR flow with no other open concerns.
