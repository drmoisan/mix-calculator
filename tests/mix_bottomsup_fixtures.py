"""Fabricated fixtures and the real-chain runner for the BottomsUp mix tests.

Holds the fabricated ``Mix_Base`` builders and the chain runner that produces the
BottomsUp builder inputs (``mix_0_detail``, ``mix_1_sku``, ``mix_2_category``,
``mix_3_customer``) by running the real rollup builders, so the test module in
``tests/test_mix_bottomsup.py`` stays under the 500-line file limit. This mirrors
the established ``tests/aop_fixtures.py`` / ``tests/le_fixtures.py`` convention.

All data here is fabricated (``SKU-001``..``SKU-005``, ``Widget`` descriptions,
``Category X``/``Category Y``, ``Acme Foods``, ``US``); no confidential source
value appears. No temp files; all DataFrames are constructed in memory.
"""

from __future__ import annotations

import pandas as pd

from src.mix_rollups import (
    build_mix_0_detail,
    build_mix_1_sku,
    build_mix_2_category,
    build_mix_3_customer,
    build_mix_rollup_1,
    build_mix_rollup_2,
    build_mix_rollup_3,
)

# Expected output column orders, verbatim from the spec Data & State section, used
# by the column-presence tests. Kept here (alongside the fixtures) so the test
# module stays under the 500-line limit. The eight shared derived columns are the
# same tail on all three tables.
_DERIVED_TAIL = [
    "Share - AOP",
    "Share - LE",
    "Share Shift",
    "Mix Rate",
    "New Contribution",
    "Disco Contribution",
    "Normal Contribution",
    "SKU Mix",
]
SKU_BOTTOMSUP_COLUMNS = [
    "Customer",
    "SKU #",
    "SKU Description",
    "Category",
    "Country",
    "Classification",
    "Lbs - AOP",
    "Lbs - LE",
    "Net Rev Per Lb - AOP",
    "Net Rev Per Lb - LE",
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
    *_DERIVED_TAIL,
]
CATEGORY_BOTTOMSUP_COLUMNS = [
    "CustCatCountry",
    "Customer",
    "Category",
    "Country",
    "Lbs - AOP",
    "Lbs - LE",
    "Net-Revenue $ - AOP",
    "Net-Revenue $ - LE",
    "Net Rev Per Lb - AOP",
    "Net Rev Per Lb - LE",
    "Classification",
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
    *_DERIVED_TAIL,
]
CUSTOMER_BOTTOMSUP_COLUMNS = [
    "CustCountry",
    "Customer",
    "Country",
    "Lbs - AOP",
    "Lbs - LE",
    "Net-Revenue $ - AOP",
    "Net-Revenue $ - LE",
    "Net Rev Per Lb - AOP",
    "Net Rev Per Lb - LE",
    "Classification",
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
    *_DERIVED_TAIL,
]


def mix_base_rows(
    customer: str,
    sku: str,
    category: str,
    country: str,
    *,
    lbs_aop: float,
    lbs_le: float,
    net_rev_aop: float,
    net_rev_le: float,
    classification: str,
) -> list[dict[str, object]]:
    """Build all six measure Mix_Base rows for one customer-SKU pair.

    Mirrors the fixture pattern in ``tests/test_mix_rollups.py`` but accepts an
    explicit ``classification`` so a single fixture can span every contribution
    branch. Gross Sales and the three negated deduction columns are derived so that
    ``Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $``
    holds for both scenarios, matching the pivot-stage invariant ``add_ratios``
    relies on. Fabricated data only.

    Args:
        customer: The customer name (fabricated).
        sku: The SKU identifier (fabricated, e.g. ``"SKU-001"``).
        category: The category name (fabricated).
        country: The country (``"US"``/``"Canada"`` are not secret).
        lbs_aop: AOP-scenario Lbs for the pair.
        lbs_le: LE-scenario Lbs for the pair.
        net_rev_aop: AOP-scenario net revenue for the pair.
        net_rev_le: LE-scenario net revenue for the pair.
        classification: The lowercase Classification token to stamp on every row.

    Returns:
        A list of six row dicts (one per measure attribute) suitable for assembling
        into a ``Mix_Base`` DataFrame.
    """

    def _measures(net_rev: float, lbs: float) -> list[tuple[str, float]]:
        # Gross sales is net revenue grossed up by the total deduction fraction;
        # each deduction is a fixed share of gross, stored negative.
        gross = net_rev / 0.8
        return [
            ("Gross Sales", gross),
            ("Lbs", lbs),
            ("Off Invoice $", -0.10 * gross),
            ("Trade Spend $", -0.06 * gross),
            ("Non-Trade $", -0.04 * gross),
            ("Net-Revenue $", net_rev),
        ]

    aop_measures = dict(_measures(net_rev_aop, lbs_aop))
    le_measures = dict(_measures(net_rev_le, lbs_le))
    rows: list[dict[str, object]] = []
    # Each measure becomes one classified Mix_Base row with AOP, LE, and Diff.
    for attribute in aop_measures:
        aop = aop_measures[attribute]
        le = le_measures[attribute]
        rows.append(
            {
                "Customer": customer,
                "SKU #": sku,
                "SKU Description": f"Widget {sku[-1]}",
                "Category": category,
                "Country": country,
                "Attribute": attribute,
                "AOP": aop,
                "LE": le,
                "Diff": le - aop,
                "Classification": classification,
            }
        )
    return rows


def mix_base_fixture() -> pd.DataFrame:
    """Build a fabricated Mix_Base spanning every contribution branch.

    One customer in one country, with five SKUs across two categories so that each
    contribution branch is exercised: normal SKUs, a new-distribution SKU (zero AOP
    Lbs), and a lost-distribution SKU (zero LE Lbs). Each new/lost SKU shares its
    category with a normal SKU so the SKU-level rollup subtotal is nonzero.
    Fabricated data only.

    Returns:
        A ``Mix_Base`` DataFrame with the classified measure rows for all five SKUs.
    """
    rows: list[dict[str, object]] = []
    # Normal SKU in Category X: both scenarios have volume.
    rows += mix_base_rows(
        "Acme Foods",
        "SKU-001",
        "Category X",
        "US",
        lbs_aop=10.0,
        lbs_le=12.0,
        net_rev_aop=90.0,
        net_rev_le=120.0,
        classification="normal",
    )
    # Second normal SKU in Category X so the (Customer, Category) rollup subtotal
    # the SKU BottomsUp share divides by is nonzero for the new SKU too.
    rows += mix_base_rows(
        "Acme Foods",
        "SKU-002",
        "Category X",
        "US",
        lbs_aop=8.0,
        lbs_le=9.0,
        net_rev_aop=64.0,
        net_rev_le=81.0,
        classification="normal",
    )
    # New-distribution SKU in Category X: zero AOP Lbs, nonzero LE Lbs.
    rows += mix_base_rows(
        "Acme Foods",
        "SKU-003",
        "Category X",
        "US",
        lbs_aop=0.0,
        lbs_le=6.0,
        net_rev_aop=0.0,
        net_rev_le=54.0,
        classification="new distribution",
    )
    # Lost-distribution SKU in Category Y: nonzero AOP Lbs, zero LE Lbs. A second
    # normal SKU shares Category Y so the AOP subtotal for the lost SKU is nonzero.
    rows += mix_base_rows(
        "Acme Foods",
        "SKU-004",
        "Category Y",
        "US",
        lbs_aop=5.0,
        lbs_le=0.0,
        net_rev_aop=40.0,
        net_rev_le=0.0,
        classification="lost distribution",
    )
    # SKU-005's AOP per-Lb rate (70/7 = 10.0) differs from SKU-004's (40/5 = 8.0)
    # so the Category Y blended rate differs from the lost SKU's own rate, giving a
    # nonzero Disco Contribution for SKU-004.
    rows += mix_base_rows(
        "Acme Foods",
        "SKU-005",
        "Category Y",
        "US",
        lbs_aop=7.0,
        lbs_le=8.0,
        net_rev_aop=70.0,
        net_rev_le=88.0,
        classification="normal",
    )
    return pd.DataFrame(rows)


def rate_impacts_fixture() -> pd.DataFrame:
    """Build a fabricated rate-impacts table covering the fixture's groups.

    Returns:
        A rate-impacts DataFrame with one row per ``(Customer, Country, Category)``
        group present in :func:`mix_base_fixture`.
    """
    return pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Acme Foods"],
            "Country": ["US", "US"],
            "Category": ["Category X", "Category Y"],
            "Calc Net Price Impact": [12.0, 8.0],
        }
    )


def build_chain() -> dict[str, pd.DataFrame]:
    """Run the real builder chain to produce the BottomsUp builder inputs.

    Builds ``mix_base`` from the fabricated fixture and chains the existing rollup
    builders to produce ``mix_0_detail``, ``mix_1_sku``, ``mix_2_category``, and
    ``mix_3_customer`` rather than constructing mock frames that duplicate builder
    logic. No temp files; all in-memory.

    Returns:
        A mapping keyed by table name (``mix_base``, ``mix_0_detail``,
        ``mix_1_sku``, ``mix_2_category``, ``mix_3_customer``).
    """
    mix_base = mix_base_fixture()
    rollup_1 = build_mix_rollup_1(rate_impacts_fixture())
    mix_1_sku = build_mix_1_sku(mix_base, rollup_1)
    rollup_2 = build_mix_rollup_2(mix_1_sku)
    # The coarser layers aggregate the unfiltered mix_base at their own
    # granularity (issue #20); the rollup targets remain the prior finer layer.
    mix_2_category = build_mix_2_category(mix_base, rollup_2)
    rollup_3 = build_mix_rollup_3(mix_2_category)
    mix_3_customer = build_mix_3_customer(mix_base, rollup_3)
    mix_0_detail = build_mix_0_detail(mix_base)
    return {
        "mix_base": mix_base,
        "mix_0_detail": mix_0_detail,
        "mix_1_sku": mix_1_sku,
        "mix_2_category": mix_2_category,
        "mix_3_customer": mix_3_customer,
    }
