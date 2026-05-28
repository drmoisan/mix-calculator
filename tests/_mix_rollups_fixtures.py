"""Shared Mix_Base / rate-impacts fixture helpers for the mix-rollup test suite.

Imported by `tests/test_mix_rollups.py` and `tests/test_mix_rollups_tieout.py`;
not itself a pytest module.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

__all__ = [
    "_f",
    "_mix_base_rows",
    "_mix_base_fixture",
    "_rate_impacts_fixture",
    "_single_scenario_mix_base_fixture",
    "_unfiltered_group_lbs_le",
]


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _mix_base_rows(
    customer: str,
    sku: str,
    category: str,
    country: str,
    *,
    lbs_aop: float,
    lbs_le: float,
    net_rev_aop: float,
    net_rev_le: float,
) -> list[dict[str, object]]:
    """Build all six measure Mix_Base rows for one customer-SKU pair.

    Gross Sales and the three (negated) deduction columns are derived so that
    ``Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $``
    holds for both scenarios, matching the pivot-stage invariant ``add_ratios``
    relies on. The deductions are a fixed fraction of gross sales.
    """

    def _measures(net_rev: float, lbs: float) -> list[tuple[str, float]]:
        # Gross sales is net revenue grossed up by the total deduction fraction;
        # each deduction is a fixed share of gross, stored negative.
        gross = net_rev / 0.8
        off_invoice = -0.10 * gross
        trade = -0.06 * gross
        non_trade = -0.04 * gross
        return [
            ("Gross Sales", gross),
            ("Lbs", lbs),
            ("Off Invoice $", off_invoice),
            ("Trade Spend $", trade),
            ("Non-Trade $", non_trade),
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
                "Classification": "normal",
            }
        )
    return rows


def _mix_base_fixture() -> pd.DataFrame:
    """Build a fabricated Mix_Base spanning two categories in two customers."""
    rows: list[dict[str, object]] = []
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-001",
        "Category X",
        "US",
        lbs_aop=10.0,
        lbs_le=12.0,
        net_rev_aop=90.0,
        net_rev_le=120.0,
    )
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-002",
        "Category Y",
        "US",
        lbs_aop=8.0,
        lbs_le=9.0,
        net_rev_aop=64.0,
        net_rev_le=81.0,
    )
    rows += _mix_base_rows(
        "Globex Market",
        "SKU-003",
        "Category X",
        "Canada",
        lbs_aop=5.0,
        lbs_le=6.0,
        net_rev_aop=40.0,
        net_rev_le=54.0,
    )
    return pd.DataFrame(rows)


def _rate_impacts_fixture() -> pd.DataFrame:
    """Build a fabricated rate-impacts table for the rollup-1 grouping test."""
    return pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Acme Foods", "Globex Market"],
            "Country": ["US", "US", "Canada"],
            "Category": ["Category X", "Category Y", "Category X"],
            "Calc Net Price Impact": [12.0, 8.0, 6.0],
        }
    )


def _single_scenario_mix_base_fixture() -> pd.DataFrame:
    """Build a Mix_Base with single-scenario lines that the SKU filter drops.

    The fabricated frame puts three SKU lines inside one ``{Customer, Country}``
    group (``Acme Foods`` / ``US``):

    - a normal two-scenario line with nonzero AOP and LE Lbs (survives the SKU
      filter on its own);
    - a SKU that is new in LE (``lbs_aop=0`` / nonzero ``lbs_le``), which the
      ``build_mix_stage`` nonzero-Lbs filter removes at the SKU layer; and
    - a SKU dropped in LE (nonzero ``lbs_aop`` / ``lbs_le=0``), likewise removed
      at the SKU layer.

    Because each coarser layer must re-aggregate the unfiltered ``mix_base`` at
    its own granularity, the LE volume of the new-in-LE line and the AOP volume
    of the dropped-in-LE line must still reach the ``{Customer, Country}`` group
    total. A normal line in a second group (``Globex Market`` / ``Canada``)
    guards against accidental cross-group leakage. Fabricated labels only.
    """
    rows: list[dict[str, object]] = []
    # Normal two-scenario line: nonzero AOP and LE Lbs, survives the SKU filter.
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-001",
        "Category X",
        "US",
        lbs_aop=10.0,
        lbs_le=12.0,
        net_rev_aop=90.0,
        net_rev_le=120.0,
    )
    # SKU new in LE: zero AOP Lbs, nonzero LE Lbs -> dropped by the SKU filter.
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-002",
        "Category Y",
        "US",
        lbs_aop=0.0,
        lbs_le=7.0,
        net_rev_aop=0.0,
        net_rev_le=70.0,
    )
    # SKU dropped in LE: nonzero AOP Lbs, zero LE Lbs -> dropped by the SKU filter.
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-003",
        "Category Z",
        "US",
        lbs_aop=5.0,
        lbs_le=0.0,
        net_rev_aop=40.0,
        net_rev_le=0.0,
    )
    # A normal line in a separate {Customer, Country} group for leakage guarding.
    rows += _mix_base_rows(
        "Globex Market",
        "SKU-004",
        "Category X",
        "Canada",
        lbs_aop=5.0,
        lbs_le=6.0,
        net_rev_aop=40.0,
        net_rev_le=54.0,
    )
    return pd.DataFrame(rows)


def _unfiltered_group_lbs_le(
    mix_base: pd.DataFrame,
    group_keys: list[str],
    group_values: dict[str, str],
) -> float:
    """Sum the unfiltered Mix_Base ``Lbs`` LE measure for one group.

    Directly aggregates the ``Attribute == "Lbs"`` rows of ``mix_base`` over the
    given group (no nonzero-Lbs filter), which is the volume the corrected
    coarser layer must retain at ``group_keys`` granularity.

    Args:
        mix_base: The fabricated Mix_Base frame.
        group_keys: The grouping dimensions (e.g. ``["Customer", "Country"]``).
        group_values: The specific group to total (e.g. ``{"Customer": ...}``).

    Returns:
        The summed LE-scenario ``Lbs`` for the selected group.
    """
    lbs_rows = mix_base[mix_base["Attribute"] == "Lbs"].copy()
    # Narrow to the requested group across every supplied key dimension.
    for key in group_keys:
        lbs_rows = lbs_rows[lbs_rows[key] == group_values[key]]
    return _f(lbs_rows["LE"].sum())
