"""Unit tests for :mod:`src.mix_nrr_summary` (issue #15).

Covers ``build_nrr_summary`` block by block with fabricated inputs only (no temp
files, no network, no real source values): the attribute-summary measures and
the per-Lb / All-in-TS% derivations (AC2), the Net-Revenue Realization block
(AC3), the Net Pricing Breakdown column totals (AC4), the Mix Breakdown column
totals including the deliberate ``Customer Mix`` column mapping (AC5), and the
reconciliation ``Check`` for both the ``"CHECK"`` and ``"ERROR"`` paths (AC6).
The division-by-zero / empty-input edges of the per-Lb and ``%`` derivations are
exercised by a zero-total fixture. Arrange-Act-Assert; fabricated data only.

The pinned ``check`` representation (single-field): the reconciliation ``Check``
row carries its result only in the ``check`` column (``"CHECK"`` / ``"ERROR"``);
its ``value`` and ``pct`` cells stay ``None``. Every other row has ``check`` set
to ``None``.
"""

from __future__ import annotations

import math
from typing import cast

import pandas as pd

from src.mix_nrr_summary import NRR_SUMMARY_COLUMNS, build_nrr_summary


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _cell(summary: pd.DataFrame, metric: str, column: str) -> object:
    """Return the single ``column`` cell for the row labeled ``metric``."""
    selected = summary[summary["metric"] == metric]
    return selected.iloc[0][column]


def _is_empty(value: object) -> bool:
    """Return whether a tidy-table cell is empty (``None`` or a float ``NaN``).

    The builder returns ``None`` for undefined numeric cells; pandas coerces
    those to ``NaN`` (an ``np.float64``, which subclasses ``float``) inside the
    float columns and keeps ``None`` in the object-typed ``check`` column. This
    helper covers both representations without invoking the typed ``pd.isna``
    overload on an ``object`` argument.

    Args:
        value: The cell value returned by :func:`_cell`.

    Returns:
        ``True`` when the cell is ``None`` or a float ``NaN``; ``False``
        otherwise.
    """
    if value is None:
        return True
    return isinstance(value, float) and math.isnan(value)


def _aop_vs_le_fixture() -> pd.DataFrame:
    """Build a fabricated AopVsLe frame with reconciling round-number totals.

    The three measure attributes use values chosen so the realization Price/Mix
    is exactly 10 (NR$) and 0.10 (%NR), which the reconciling pricing/mix
    fixtures below tie out to a ``"CHECK"`` result:

    - ``Net-Revenue $``: AOP 100, LE 130, Diff 30.
    - ``Lbs``: AOP 10, LE 12, Diff 2 (so NetRevPerLb.AOP = 10).
    - ``Gross Sales``: AOP 200, LE 260, Diff 60 (so All-in-TS% is well defined).

    Two rows per attribute (split across SKUs) confirm the SUMIF-by-Attribute
    sums aggregate rather than read a single row.
    """
    rows: list[dict[str, object]] = []
    # Split each attribute total across two fabricated SKUs to exercise the sum.
    attribute_splits: dict[str, list[tuple[float, float]]] = {
        "Net-Revenue $": [(60.0, 80.0), (40.0, 50.0)],
        "Lbs": [(6.0, 7.0), (4.0, 5.0)],
        "Gross Sales": [(120.0, 160.0), (80.0, 100.0)],
    }
    # Emit one AopVsLe row per (attribute, SKU split) with AOP, LE, and Diff.
    for attribute, splits in attribute_splits.items():
        for index, (aop, le) in enumerate(splits):
            rows.append(
                {
                    "Customer": "Acme Foods",
                    "SKU #": f"SKU-00{index + 1}",
                    "Attribute": attribute,
                    "AOP": aop,
                    "LE": le,
                    "Diff": le - aop,
                    "Classification": "normal",
                }
            )
    return pd.DataFrame(rows)


def _rate_impacts_fixture() -> pd.DataFrame:
    """Build a fabricated rate-impacts frame whose four column totals sum to 7.

    Two rows confirm the pricing block sums each column rather than reading one
    row. Column totals: Gross Pricing 4, OI Rate 1, Promo Rate 1, Non-trade 1.
    """
    return pd.DataFrame(
        {
            "Calc Gross Price Impact on Net": [3.0, 1.0],
            "OI Rate Impact": [0.5, 0.5],
            "Trade Rate Impact": [0.4, 0.6],
            "Non-Trade Rate Impact": [0.7, 0.3],
        }
    )


def _mix_fixtures_reconciling() -> (
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
):
    """Build the four mix-level frames whose column totals sum to 3 (Total Mix).

    Totals: SKU Mix 1, Category Mix 1, Customer Mix 0.5, Country Mix 0.5. The
    customer frame deliberately stores its total in the ``Customer Mix`` column
    (the pipeline's rename of the Excel ``Category Mix`` reference).
    """
    mix_1_sku = pd.DataFrame({"SKU Mix": [0.6, 0.4]})
    mix_2_category = pd.DataFrame({"Category Mix": [0.7, 0.3]})
    mix_3_customer = pd.DataFrame({"Customer Mix": [0.2, 0.3]})
    mix_4_country = pd.DataFrame({"Country Mix": [0.5]})
    return mix_1_sku, mix_2_category, mix_3_customer, mix_4_country


def _build_reconciling_summary() -> pd.DataFrame:
    """Build the summary from the reconciling fixtures (expected ``Check`` pass)."""
    aop_vs_le = _aop_vs_le_fixture()
    rate_impacts = _rate_impacts_fixture()
    mix_1_sku, mix_2_category, mix_3_customer, mix_4_country = (
        _mix_fixtures_reconciling()
    )
    return build_nrr_summary(
        aop_vs_le,
        rate_impacts,
        mix_1_sku,
        mix_2_category,
        mix_3_customer,
        mix_4_country,
    )


def test_output_schema_columns_match() -> None:
    """The result carries exactly the seven tidy long-table columns in order."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # Assert
    assert list(summary.columns) == NRR_SUMMARY_COLUMNS


def test_attribute_summary_core_measures_are_sumif_totals() -> None:
    """Lbs, Gross Sales, and Net-Revenue $ reproduce the SUMIF AOP/LE/Abs sums (AC2)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # Assert: Net-Revenue $ AOP 100, LE 130, Abs 30, % = 30/100.
    assert _f(_cell(summary, "Net-Revenue $", "aop")) == 100.0
    assert _f(_cell(summary, "Net-Revenue $", "le")) == 130.0
    assert _f(_cell(summary, "Net-Revenue $", "value")) == 30.0
    assert abs(_f(_cell(summary, "Net-Revenue $", "pct")) - 0.30) < 1e-9
    # Lbs AOP 10, LE 12, Abs 2.
    assert _f(_cell(summary, "Lbs", "aop")) == 10.0
    assert _f(_cell(summary, "Lbs", "value")) == 2.0


def test_attribute_summary_per_lb_and_ts_derivations() -> None:
    """GS / Lb, Net Rev / Lb, and All in TS% match the hand-computed values (AC2)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # GS / Lb: AOP = 200/10 = 20, LE = 260/12, Abs = LE - AOP.
    gs_per_lb_aop = 200.0 / 10.0
    gs_per_lb_le = 260.0 / 12.0
    assert abs(_f(_cell(summary, "GS / Lb", "aop")) - gs_per_lb_aop) < 1e-9
    assert abs(_f(_cell(summary, "GS / Lb", "le")) - gs_per_lb_le) < 1e-9
    assert (
        abs(_f(_cell(summary, "GS / Lb", "value")) - (gs_per_lb_le - gs_per_lb_aop))
        < 1e-9
    )

    # Net Rev / Lb: AOP = 100/10 = 10, LE = 130/12.
    nr_per_lb_aop = 100.0 / 10.0
    nr_per_lb_le = 130.0 / 12.0
    assert abs(_f(_cell(summary, "Net Rev / Lb", "aop")) - nr_per_lb_aop) < 1e-9
    assert abs(_f(_cell(summary, "Net Rev / Lb", "le")) - nr_per_lb_le) < 1e-9

    # All in TS%: AOP = 1 - 100/200 = 0.5, LE = 1 - 130/260 = 0.5, Abs = 0 bps.
    assert abs(_f(_cell(summary, "All in TS%", "aop")) - 0.5) < 1e-9
    assert abs(_f(_cell(summary, "All in TS%", "le")) - 0.5) < 1e-9
    assert abs(_f(_cell(summary, "All in TS%", "value")) - 0.0) < 1e-9
    # All in TS% carries no % column; the empty numeric cell is stored as NaN.
    assert _is_empty(_cell(summary, "All in TS%", "pct"))


def test_net_revenue_realization_block() -> None:
    """Volume Impact and Price/Mix reproduce the realization arithmetic (AC3)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # Volume Impact = Lbs.Abs (2) * NetRevPerLb.AOP (10) = 20; %NR = 20/100.
    assert abs(_f(_cell(summary, "Volume Impact", "value")) - 20.0) < 1e-9
    assert abs(_f(_cell(summary, "Volume Impact", "pct")) - 0.20) < 1e-9

    # Price/Mix = NetRev.Abs (30) - Volume (20) = 10; %NR = 10/100 = 0.10.
    assert abs(_f(_cell(summary, "Price/Mix", "value")) - 10.0) < 1e-9
    assert abs(_f(_cell(summary, "Price/Mix", "pct")) - 0.10) < 1e-9


def test_net_pricing_breakdown_block() -> None:
    """The four pricing column totals and Total Net Pricing match (AC4)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # Column totals: Gross Pricing 4, OI Rate 1, Promo Rate 1, Non-trade 1.
    assert abs(_f(_cell(summary, "Gross Pricing", "value")) - 4.0) < 1e-9
    assert abs(_f(_cell(summary, "OI Rate", "value")) - 1.0) < 1e-9
    # Promo Rate reads the Trade Rate Impact column (0.4 + 0.6 = 1.0).
    assert abs(_f(_cell(summary, "Promo Rate", "value")) - 1.0) < 1e-9
    assert abs(_f(_cell(summary, "Non-trade Rate", "value")) - 1.0) < 1e-9
    # Total Net Pricing = 4 + 1 + 1 + 1 = 7; %NR = 7/100 = 0.07.
    assert abs(_f(_cell(summary, "Total Net Pricing", "value")) - 7.0) < 1e-9
    assert abs(_f(_cell(summary, "Total Net Pricing", "pct")) - 0.07) < 1e-9


def test_mix_breakdown_block_reads_customer_mix_column() -> None:
    """Mix totals match and Customer Mix reads the renamed column (AC5)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    assert abs(_f(_cell(summary, "SKU Mix", "value")) - 1.0) < 1e-9
    assert abs(_f(_cell(summary, "Category Mix", "value")) - 1.0) < 1e-9
    # Customer Mix sums the mix_3_customer["Customer Mix"] column (0.2 + 0.3).
    assert abs(_f(_cell(summary, "Customer Mix", "value")) - 0.5) < 1e-9
    assert abs(_f(_cell(summary, "Country Mix", "value")) - 0.5) < 1e-9
    # Total Mix = 1 + 1 + 0.5 + 0.5 = 3; %NR = 3/100 = 0.03.
    assert abs(_f(_cell(summary, "Total Mix", "value")) - 3.0) < 1e-9
    assert abs(_f(_cell(summary, "Total Mix", "pct")) - 0.03) < 1e-9


def test_customer_mix_requires_customer_mix_column() -> None:
    """The builder reads the customer ``Customer Mix`` column, not ``Category Mix``."""
    # Arrange: a customer frame that carries only the M-source-style "Category Mix"
    # label would raise a KeyError, proving the deliberate rename mapping (AC5).
    aop_vs_le = _aop_vs_le_fixture()
    rate_impacts = _rate_impacts_fixture()
    mix_1_sku, mix_2_category, _customer, mix_4_country = _mix_fixtures_reconciling()
    wrong_customer = pd.DataFrame({"Category Mix": [0.2, 0.3]})

    # Act / Assert: reading the renamed column is required; the wrong label fails.
    try:
        build_nrr_summary(
            aop_vs_le,
            rate_impacts,
            mix_1_sku,
            mix_2_category,
            wrong_customer,
            mix_4_country,
        )
    except KeyError:
        return
    raise AssertionError("expected KeyError when the Customer Mix column is absent")


def test_reconciliation_check_passes_when_buildup_ties_out() -> None:
    """The Check row is ``"CHECK"`` and Price / Mix build-up ties out (AC6)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # Build-up NR$ = Total Mix (3) + Total Net Pricing (7) = 10; %NR = 0.10.
    assert abs(_f(_cell(summary, "Price / Mix", "value")) - 10.0) < 1e-9
    assert abs(_f(_cell(summary, "Price / Mix", "pct")) - 0.10) < 1e-9

    # The Check row carries its result only in the check column; the numeric
    # value/pct cells are empty (stored as NaN in the float columns).
    assert _cell(summary, "Check", "check") == "CHECK"
    assert _is_empty(_cell(summary, "Check", "value"))
    assert _is_empty(_cell(summary, "Check", "pct"))


def test_reconciliation_check_errors_when_buildup_diverges() -> None:
    """The Check row is ``"ERROR"`` when the build-up diverges (AC6)."""
    # Arrange: inflate one pricing column so Total Net Pricing no longer ties out
    # to the realization Price/Mix (the build-up NR$ becomes 17, not 10).
    aop_vs_le = _aop_vs_le_fixture()
    diverging_rate_impacts = pd.DataFrame(
        {
            "Calc Gross Price Impact on Net": [10.0, 1.0],
            "OI Rate Impact": [0.5, 0.5],
            "Trade Rate Impact": [0.4, 0.6],
            "Non-Trade Rate Impact": [0.7, 0.3],
        }
    )
    mix_1_sku, mix_2_category, mix_3_customer, mix_4_country = (
        _mix_fixtures_reconciling()
    )

    # Act
    summary = build_nrr_summary(
        aop_vs_le,
        diverging_rate_impacts,
        mix_1_sku,
        mix_2_category,
        mix_3_customer,
        mix_4_country,
    )

    # Assert: the divergence trips the Check to ERROR.
    assert _cell(summary, "Check", "check") == "ERROR"


def test_non_check_rows_have_none_check_cell() -> None:
    """Every non-Check row leaves the check column empty (pinned representation)."""
    # Arrange / Act
    summary = _build_reconciling_summary()

    # Assert: only the single Check row carries a non-None check value.
    non_check = summary[summary["metric"] != "Check"]
    assert non_check["check"].isna().all()


def _zero_total_aop_vs_le_fixture() -> pd.DataFrame:
    """Build an AopVsLe frame whose Lbs and Gross Sales AOP totals are zero.

    Exercises the zero-denominator path of the per-Lb ratios, the All-in-TS%
    derivation, and the realization rate. Net-Revenue $ keeps a nonzero AOP so
    the %NR denominator on the lower blocks remains the targeted guard.
    """
    rows: list[dict[str, object]] = [
        {"Attribute": "Lbs", "AOP": 0.0, "LE": 0.0, "Diff": 0.0},
        {"Attribute": "Gross Sales", "AOP": 0.0, "LE": 0.0, "Diff": 0.0},
        {"Attribute": "Net-Revenue $", "AOP": 100.0, "LE": 130.0, "Diff": 30.0},
    ]
    return pd.DataFrame(rows)


def test_zero_denominator_per_lb_and_ts_yield_none() -> None:
    """Zero Lbs/Gross-Sales totals leave the per-Lb and TS% cells empty (AC8)."""
    # Arrange
    aop_vs_le = _zero_total_aop_vs_le_fixture()
    rate_impacts = _rate_impacts_fixture()
    mix_1_sku, mix_2_category, mix_3_customer, mix_4_country = (
        _mix_fixtures_reconciling()
    )

    # Act
    summary = build_nrr_summary(
        aop_vs_le,
        rate_impacts,
        mix_1_sku,
        mix_2_category,
        mix_3_customer,
        mix_4_country,
    )

    # Assert: GS / Lb and Net Rev / Lb divide by a zero Lbs total -> empty cells
    # (the builder returns None; the float column stores them as NaN).
    assert _is_empty(_cell(summary, "GS / Lb", "aop"))
    assert _is_empty(_cell(summary, "GS / Lb", "value"))
    assert _is_empty(_cell(summary, "Net Rev / Lb", "aop"))
    # All in TS% divides by a zero Gross-Sales total -> empty.
    assert _is_empty(_cell(summary, "All in TS%", "aop"))
    assert _is_empty(_cell(summary, "All in TS%", "value"))
    # Volume Impact uses NetRevPerLb.AOP (NetRev/Lbs) -> zero Lbs -> empty.
    assert _is_empty(_cell(summary, "Volume Impact", "value"))
    assert _is_empty(_cell(summary, "Price/Mix", "value"))


def test_zero_denominator_check_is_error() -> None:
    """An undefined realization Price/Mix cannot reconcile, so Check is ERROR (AC8)."""
    # Arrange
    aop_vs_le = _zero_total_aop_vs_le_fixture()
    rate_impacts = _rate_impacts_fixture()
    mix_1_sku, mix_2_category, mix_3_customer, mix_4_country = (
        _mix_fixtures_reconciling()
    )

    # Act
    summary = build_nrr_summary(
        aop_vs_le,
        rate_impacts,
        mix_1_sku,
        mix_2_category,
        mix_3_customer,
        mix_4_country,
    )

    # Assert: the None realization Price/Mix forces a non-reconciling ERROR.
    assert _cell(summary, "Check", "check") == "ERROR"


def test_zero_net_rev_aop_leaves_buildup_pct_empty() -> None:
    """A zero Net-Revenue AOP makes every %NR (and the build-up %NR) empty (AC8)."""
    # Arrange: a Net-Revenue $ AOP total of zero makes %NR = value/0 undefined for
    # the pricing and mix totals, so the build-up %NR sum is also undefined.
    aop_vs_le = pd.DataFrame(
        [
            {"Attribute": "Lbs", "AOP": 10.0, "LE": 12.0, "Diff": 2.0},
            {"Attribute": "Gross Sales", "AOP": 200.0, "LE": 260.0, "Diff": 60.0},
            {"Attribute": "Net-Revenue $", "AOP": 0.0, "LE": 30.0, "Diff": 30.0},
        ]
    )
    rate_impacts = _rate_impacts_fixture()
    mix_1_sku, mix_2_category, mix_3_customer, mix_4_country = (
        _mix_fixtures_reconciling()
    )

    # Act
    summary = build_nrr_summary(
        aop_vs_le,
        rate_impacts,
        mix_1_sku,
        mix_2_category,
        mix_3_customer,
        mix_4_country,
    )

    # Assert: Total Net Pricing and Total Mix %NR are empty, so the build-up
    # Price / Mix %NR (sum_optional of two None values) is empty as well, and
    # the %NR side of the Check cannot reconcile -> ERROR.
    assert _is_empty(_cell(summary, "Total Net Pricing", "pct"))
    assert _is_empty(_cell(summary, "Total Mix", "pct"))
    assert _is_empty(_cell(summary, "Price / Mix", "pct"))
    assert _cell(summary, "Check", "check") == "ERROR"


def test_empty_mix_frames_sum_to_zero() -> None:
    """Empty mix frames sum to zero totals without raising (AC8 empty-input edge)."""
    # Arrange: empty mix frames (columns present, no rows) sum to 0.0.
    aop_vs_le = _aop_vs_le_fixture()
    rate_impacts = _rate_impacts_fixture()
    empty_sku = pd.DataFrame({"SKU Mix": pd.Series([], dtype="float64")})
    empty_category = pd.DataFrame({"Category Mix": pd.Series([], dtype="float64")})
    empty_customer = pd.DataFrame({"Customer Mix": pd.Series([], dtype="float64")})
    empty_country = pd.DataFrame({"Country Mix": pd.Series([], dtype="float64")})

    # Act
    summary = build_nrr_summary(
        aop_vs_le,
        rate_impacts,
        empty_sku,
        empty_category,
        empty_customer,
        empty_country,
    )

    # Assert: each mix level totals 0 and Total Mix is 0.
    assert _f(_cell(summary, "SKU Mix", "value")) == 0.0
    assert _f(_cell(summary, "Total Mix", "value")) == 0.0
