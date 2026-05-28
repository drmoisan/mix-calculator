"""Transform-chain runner for the mix-pipeline orchestration.

This module factors the topological run of evaluation steps 9-19 out of
:mod:`src.mix_pipeline` so the CLI entry module stays under the 500-line limit.
``run_transforms`` calls the pure ``src.mix_*`` builders in dependency order and
returns the derived tables (including the ``mix_rollup_4`` scalar wrapped as a
single-row table) keyed by their snake_case SQLite table names. It performs no
I/O; the caller owns the connection and the writes.

All function and table names here are schema, not secret; only the source data
values are confidential and never appear in this module.
"""

from __future__ import annotations

import pandas as pd

from src.mix_bottomsup import (
    build_mix_2_sku_bottomsup,
    build_mix_3_category_bottomsup,
    build_mix_4_customer_bottomsup,
)
from src.mix_nrr_summary import build_nrr_summary
from src.mix_q1 import build_q1_results_by_sku
from src.mix_rate_impacts import build_rate_impacts
from src.mix_rollups import (
    build_mix_0_detail,
    build_mix_1_sku,
    build_mix_2_category,
    build_mix_3_customer,
    build_mix_4_country,
    build_mix_rollup_1,
    build_mix_rollup_2,
    build_mix_rollup_3,
    build_mix_rollup_4,
)

__all__ = ["run_transforms"]


def run_transforms(
    aop_vs_le: pd.DataFrame,
    sku_lu: pd.DataFrame,
    mix_base: pd.DataFrame,
    le_raw: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Run evaluation steps 9-19 and return the derived tables.

    Calls the pure rate-impact, rollup, detail, and Q1 builders in dependency
    order. ``mix_rollup_4`` is a scalar ``float`` and is wrapped as a single-row,
    single-column ``{value: float}`` table so it can be persisted alongside the
    DataFrame-valued tables.

    Args:
        aop_vs_le: The classified comparison frame (steps 7) used by the rate
            impacts.
        sku_lu: The SKU lookup frame used to enrich the rate impacts.
        mix_base: The enriched mix base (step 8) feeding the rollup chain and the
            detail table.
        le_raw: The raw ``LE`` frame feeding the Q1 results.

    Returns:
        A mapping of snake_case table name to the derived DataFrame, in
        evaluation order, covering ``rate_impacts``, ``mix_rollup_1``,
        ``mix_1_sku``, ``mix_rollup_2``, ``mix_2_category``, ``mix_rollup_3``,
        ``mix_3_customer``, ``mix_rollup_4`` (single-row), ``mix_4_country``,
        ``mix_0_detail``, the three BottomsUp tables (``mix_2_sku_bottomsup``,
        ``mix_3_category_bottomsup``, ``mix_4_customer_bottomsup``),
        ``q1_results_by_sku``, and ``nrr_summary`` (the final derived summary
        table, issue #15).
    """
    # Step 9: rate impacts for the normal lines.
    rate_impacts = build_rate_impacts(aop_vs_le, sku_lu)

    # Steps 10-17: the rollup chain. Each coarser mix layer aggregates the
    # unfiltered mix_base at its own granularity (issue #20), while each rollup
    # target remains the summed prior finer layer so the mix column stays
    # (this layer's recomputed NPI) - (sum of finer-layer NPI).
    mix_rollup_1 = build_mix_rollup_1(rate_impacts)
    mix_1_sku = build_mix_1_sku(mix_base, mix_rollup_1)
    mix_rollup_2 = build_mix_rollup_2(mix_1_sku)
    mix_2_category = build_mix_2_category(mix_base, mix_rollup_2)
    mix_rollup_3 = build_mix_rollup_3(mix_2_category)
    mix_3_customer = build_mix_3_customer(mix_base, mix_rollup_3)
    mix_rollup_4_value = build_mix_rollup_4(mix_3_customer)
    mix_4_country = build_mix_4_country(mix_base, mix_rollup_4_value)

    # Step 18: the row-level detail table (depends on mix_base, not the chain).
    mix_0_detail = build_mix_0_detail(mix_base)

    # Step 18b: the three BottomsUp tables, derived from the detail row set plus the
    # already-computed rollup chain. The SKU table also needs mix_base to recover
    # Classification (dropped from mix_0_detail upstream); the category/customer
    # tables re-derive Classification from their aggregated Lbs.
    mix_2_sku_bottomsup = build_mix_2_sku_bottomsup(mix_0_detail, mix_base, mix_1_sku)
    mix_3_category_bottomsup = build_mix_3_category_bottomsup(
        mix_0_detail, mix_2_category
    )
    mix_4_customer_bottomsup = build_mix_4_customer_bottomsup(
        mix_0_detail, mix_3_customer
    )

    # Step 19: the Q1 results-by-SKU table (separate path over the raw LE months).
    q1_results = build_q1_results_by_sku(le_raw)

    # Final summary step (issue #15): the NRR summary ties the AOP-vs-LE net
    # revenue change to its volume/pricing/mix drivers from the frames computed
    # above. It is pure and appended as the last derived table.
    nrr_summary = build_nrr_summary(
        aop_vs_le,
        rate_impacts,
        mix_1_sku,
        mix_2_category,
        mix_3_customer,
        mix_4_country,
    )

    # Wrap the scalar rollup as a single-row table so it persists like the rest.
    mix_rollup_4_table = pd.DataFrame({"value": [mix_rollup_4_value]})

    return {
        "rate_impacts": rate_impacts,
        "mix_rollup_1": mix_rollup_1,
        "mix_1_sku": mix_1_sku,
        "mix_rollup_2": mix_rollup_2,
        "mix_2_category": mix_2_category,
        "mix_rollup_3": mix_rollup_3,
        "mix_3_customer": mix_3_customer,
        "mix_rollup_4": mix_rollup_4_table,
        "mix_4_country": mix_4_country,
        "mix_0_detail": mix_0_detail,
        "mix_2_sku_bottomsup": mix_2_sku_bottomsup,
        "mix_3_category_bottomsup": mix_3_category_bottomsup,
        "mix_4_customer_bottomsup": mix_4_customer_bottomsup,
        "q1_results_by_sku": q1_results,
        "nrr_summary": nrr_summary,
    }
