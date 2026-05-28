---
name: mix-builder-signature-mix-base
description: issue #20 changed the coarser mix-builder signatures to take mix_base; callers/fixtures written against the old prior-layer signature break with "No group keys passed"
metadata:
  type: project
---

Issue #20 changed `build_mix_2_category`, `build_mix_3_customer`, and
`build_mix_4_country` (in `src/mix_rollups.py`) so their first positional
argument is now the unfiltered `mix_base` instead of the prior mix layer
(`mix_1_sku` / `mix_2_category` / `mix_3_customer`). The rollup-target argument
(`mix_rollup_N`) is unchanged.

**Why:** the coarser layers must aggregate the unfiltered `mix_base` at their own
granularity to retain single-scenario lines the SKU-layer nonzero-Lbs filter
drops; re-aggregating the filtered prior layer understated category/customer mix
and made the `nrr_summary` `Check` resolve to "ERROR".

**How to apply:** any caller or test fixture that builds the mix chain must pass
`mix_base` (not the prior layer) to these three builders. A stale caller using
the old signature fails with `ValueError: No group keys passed!` raised from
`build_mix_stage` in `src/_mix_rollups_helpers.py`, because a wide stacked prior-
layer frame lacks the long-form `Attribute`/`AOP`/`LE`/`Diff` columns the groupby
needs. During issue #20 execution, PR #22 (BottomsUp) merged in with
`tests/mix_bottomsup_fixtures.py::build_chain` using the old signatures and had to
be reconciled. The production runner is `src/mix_pipeline_run.py::run_transforms`.
`unstack_to_long` was removed from `src/_mix_rollups_helpers.py` as part of #20.
