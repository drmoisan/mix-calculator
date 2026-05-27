"""Unit tests for the pure primitives in :mod:`src.mix_transforms`.

Covers the primitives with Arrange-Act-Assert structure and fabricated data
only: ``negate_column``; ``calc_ratios`` positive and zero-denominator guard
branches; ``classify_table`` every SKU-level and customer-SKU-level branch;
``stack_pivot`` header join and sum aggregation; ``add_ratios`` append-only
invariant; and ``fill_zero_with_avg`` replacement and zero-Lbs-sum edge. The
``pivot_le`` / ``pivot_aop`` tests live in ``test_mix_pivots.py`` to keep each
test file under the 500-line limit. No confidential values appear; SKU codes,
descriptions, and categories are fabricated.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from src.mix_transforms import (
    add_ratios,
    calc_ratios,
    classify_table,
    fill_zero_with_avg,
    negate_column,
    stack_pivot,
)


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


# ---------------------------------------------------------------------------
# negate_column
# ---------------------------------------------------------------------------


def test_negate_column_flips_sign_and_does_not_mutate_input() -> None:
    """negate_column returns a copy with the column negated, leaving input intact."""
    # Arrange
    frame = pd.DataFrame({"a": [1.0, -2.0, 0.0], "b": [9.0, 9.0, 9.0]})

    # Act
    result = negate_column(frame, "a")

    # Assert: column negated in the result, original frame unchanged.
    assert list(result["a"]) == [-1.0, 2.0, 0.0]
    assert list(frame["a"]) == [1.0, -2.0, 0.0]
    assert list(result["b"]) == [9.0, 9.0, 9.0]


# ---------------------------------------------------------------------------
# calc_ratios
# ---------------------------------------------------------------------------


def _measure_frame(
    gross: float, lbs: float, oi: float, trade: float, non_trade: float
) -> pd.DataFrame:
    """Build a one-row measure frame for calc_ratios with a derived net revenue."""
    net_rev = gross + oi + trade + non_trade
    return pd.DataFrame(
        {
            "Gross Sales": [gross],
            "Lbs": [lbs],
            "Off Invoice $": [oi],
            "Trade Spend $": [trade],
            "Non-Trade $": [non_trade],
            "Net-Revenue $": [net_rev],
        }
    )


def test_calc_ratios_positive_values_compute_expected() -> None:
    """calc_ratios computes per-Lb and %GS ratios for positive denominators."""
    # Arrange: gross 100, Lbs 10, deductions already negated.
    frame = _measure_frame(100.0, 10.0, -5.0, -2.0, -1.0)

    # Act
    result = calc_ratios(frame)

    # Assert
    assert _f(result.loc[0, "Gross Sales Per Lb"]) == 10.0
    assert _f(result.loc[0, "OI Per Lb"]) == -0.5
    assert _f(result.loc[0, "Net Rev Per Lb"]) == 9.2
    assert _f(result.loc[0, "OI %GS"]) == -0.05
    assert _f(result.loc[0, "Trade %GS"]) == -0.02
    assert _f(result.loc[0, "Non-Trade %GS"]) == -0.01


def test_calc_ratios_zero_lbs_guard_returns_zero() -> None:
    """A zero Lbs denominator yields 0 for every per-Lb ratio."""
    # Arrange: Lbs is zero so the per-Lb ratios must guard to 0.
    frame = _measure_frame(100.0, 0.0, -5.0, -2.0, -1.0)

    # Act
    result = calc_ratios(frame)

    # Assert
    assert _f(result.loc[0, "Gross Sales Per Lb"]) == 0.0
    assert _f(result.loc[0, "OI Per Lb"]) == 0.0
    assert _f(result.loc[0, "Net Rev Per Lb"]) == 0.0
    # The %GS ratios still compute because Gross Sales is positive.
    assert _f(result.loc[0, "OI %GS"]) == -0.05


def test_calc_ratios_zero_gross_sales_guard_returns_zero() -> None:
    """A zero Gross Sales denominator yields 0 for every %GS ratio."""
    # Arrange: Gross Sales is zero so the %GS ratios must guard to 0.
    frame = _measure_frame(0.0, 10.0, -5.0, -2.0, -1.0)

    # Act
    result = calc_ratios(frame)

    # Assert
    assert _f(result.loc[0, "OI %GS"]) == 0.0
    assert _f(result.loc[0, "Trade %GS"]) == 0.0
    assert _f(result.loc[0, "Non-Trade %GS"]) == 0.0
    # The per-Lb ratios still compute because Lbs is positive.
    assert _f(result.loc[0, "OI Per Lb"]) == -0.5


# ---------------------------------------------------------------------------
# classify_table
# ---------------------------------------------------------------------------


def _lbs_row(customer: str, sku: str, aop: float, le: float) -> dict[str, object]:
    """Build a single Lbs AopVsLe row for classification tests."""
    return {
        "Customer": customer,
        "SKU #": sku,
        "Attribute": "Lbs",
        "AOP": aop,
        "LE": le,
        "Diff": le - aop,
    }


def test_classify_table_sku_level_branches() -> None:
    """Each SKU-level branch (inactive/eliminated/new) resolves correctly."""
    # Arrange: one customer per SKU so the SKU total equals the single Lbs value.
    rows = [
        _lbs_row("Acme Foods", "SKU-001", 0.0, 0.0),  # inactive
        _lbs_row("Acme Foods", "SKU-002", 5.0, 0.0),  # eliminated
        _lbs_row("Acme Foods", "SKU-003", 0.0, 7.0),  # new
    ]
    frame = pd.DataFrame(rows)

    # Act
    result = classify_table(frame)

    # Assert
    by_sku = result.set_index("SKU #")["Classification"]
    assert by_sku.loc["SKU-001"] == "inactive"
    assert by_sku.loc["SKU-002"] == "eliminated"
    assert by_sku.loc["SKU-003"] == "new"


def test_classify_table_customer_sku_branches_for_exists_sku() -> None:
    """An 'exists' SKU refines each customer-SKU branch via level-2 logic."""
    # Arrange: SKU-010 has nonzero AOP and LE totals (exists) across customers,
    # so each customer-SKU pair is refined by its own Lbs values.
    rows = [
        _lbs_row("Acme Foods", "SKU-010", 4.0, 6.0),  # normal
        _lbs_row("Globex Market", "SKU-010", 3.0, 0.0),  # lost distribution
        _lbs_row("Initech Grocers", "SKU-010", 0.0, 2.0),  # new distribution
    ]
    frame = pd.DataFrame(rows)

    # Act
    result = classify_table(frame)

    # Assert
    by_pair = result.set_index(["Customer", "SKU #"])["Classification"]
    assert by_pair.loc["Acme Foods", "SKU-010"] == "normal"
    assert by_pair.loc["Globex Market", "SKU-010"] == "lost distribution"
    assert by_pair.loc["Initech Grocers", "SKU-010"] == "new distribution"


def test_classify_table_customer_sku_inactive_within_exists_sku() -> None:
    """A zero-zero customer-SKU pair under an 'exists' SKU is 'inactive'."""
    # Arrange: SKU-020 exists at the SKU level (one customer carries it), but a
    # second customer has zero AOP and LE for it, so that pair is inactive.
    rows = [
        _lbs_row("Acme Foods", "SKU-020", 4.0, 6.0),  # normal, makes SKU exist
        _lbs_row("Globex Market", "SKU-020", 0.0, 0.0),  # inactive pair
    ]
    frame = pd.DataFrame(rows)

    # Act
    result = classify_table(frame)

    # Assert
    by_pair = result.set_index(["Customer", "SKU #"])["Classification"]
    assert by_pair.loc["Acme Foods", "SKU-020"] == "normal"
    assert by_pair.loc["Globex Market", "SKU-020"] == "inactive"


def test_classify_table_broadcasts_to_non_lbs_rows() -> None:
    """The pair classification is applied to every Attribute row of the pair."""
    # Arrange: one Lbs row drives classification; a Gross Sales row shares it.
    rows = [
        _lbs_row("Acme Foods", "SKU-030", 4.0, 6.0),
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-030",
            "Attribute": "Gross Sales",
            "AOP": 100.0,
            "LE": 120.0,
            "Diff": 20.0,
        },
    ]
    frame = pd.DataFrame(rows)

    # Act
    result = classify_table(frame)

    # Assert: both rows carry the same "normal" classification.
    assert set(result["Classification"]) == {"normal"}


# ---------------------------------------------------------------------------
# stack_pivot
# ---------------------------------------------------------------------------


def test_stack_pivot_joins_header_and_sums() -> None:
    """stack_pivot builds 'Attr - Scenario' headers and sums the value column."""
    # Arrange: two identity-equal rows for one header must sum.
    frame = pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Acme Foods", "Acme Foods"],
            "Attribute": ["Lbs", "Lbs", "Gross Sales"],
            "Scenario": ["AOP", "AOP", "LE"],
            "Value": [3.0, 4.0, 100.0],
        }
    )

    # Act
    result = stack_pivot(frame, ["Attribute", "Scenario"], "Value")

    # Assert: the two Lbs-AOP rows summed to 7; Gross Sales-LE is 100.
    assert "Lbs - AOP" in result.columns
    assert "Gross Sales - LE" in result.columns
    row = result[result["Customer"] == "Acme Foods"].iloc[0]
    assert _f(row["Lbs - AOP"]) == 7.0
    assert _f(row["Gross Sales - LE"]) == 100.0


# ---------------------------------------------------------------------------
# add_ratios
# ---------------------------------------------------------------------------


def _long_scenario_rows() -> pd.DataFrame:
    """Build a long Attribute/Value/Scenario frame for one customer-SKU pair."""
    measures = [
        ("Gross Sales", 100.0),
        ("Lbs", 10.0),
        ("Off Invoice $", -5.0),
        ("Trade Spend $", -2.0),
        ("Non-Trade $", -1.0),
        ("Net-Revenue $", 92.0),
    ]
    records: list[dict[str, object]] = []
    # Emit identical AOP and LE measure rows so both scenarios produce ratios.
    for scenario in ("AOP", "LE"):
        for attribute, value in measures:
            records.append(
                {
                    "Customer": "Acme Foods",
                    "SKU #": "SKU-100",
                    "Attribute": attribute,
                    "Scenario": scenario,
                    "Value": value,
                }
            )
    return pd.DataFrame(records)


def test_add_ratios_appends_only_new_ratio_rows() -> None:
    """add_ratios appends the eight ratio rows per scenario without duplicating."""
    # Arrange
    frame = _long_scenario_rows()
    original_len = len(frame)

    # Act
    result = add_ratios(frame, ["AOP", "LE"])

    # Assert: 8 ratio rows per scenario added; originals preserved exactly once.
    assert len(result) == original_len + 8 * 2
    # No original measure attribute row was duplicated.
    gross_aop = result[
        (result["Attribute"] == "Gross Sales") & (result["Scenario"] == "AOP")
    ]
    assert len(gross_aop) == 1
    # A computed ratio row exists for each scenario.
    rate_rows = result[result["Attribute"] == "Net Rev Per Lb"]
    assert set(rate_rows["Scenario"]) == {"AOP", "LE"}
    assert _f(rate_rows[rate_rows["Scenario"] == "AOP"].iloc[0]["Value"]) == 9.2


def test_add_ratios_skips_absent_scenario() -> None:
    """A scenario with no rows contributes nothing to the appended result."""
    # Arrange: only AOP rows present.
    frame = _long_scenario_rows()
    frame = frame[frame["Scenario"] == "AOP"].copy()
    original_len = len(frame)

    # Act: request LE too, but there are no LE rows to process.
    result = add_ratios(frame, ["AOP", "LE"])

    # Assert: only the eight AOP ratio rows appended.
    assert len(result) == original_len + 8


def test_add_ratios_no_matching_scenarios_returns_copy() -> None:
    """When no requested scenario has rows, the input is returned unchanged."""
    # Arrange: rows exist only for AOP, but only an absent scenario is requested.
    frame = _long_scenario_rows()
    frame = frame[frame["Scenario"] == "AOP"].copy()
    original_len = len(frame)

    # Act: request a scenario with no rows so no ratio frames are produced.
    result = add_ratios(frame, ["LE"])

    # Assert: the result is an unchanged copy of the input.
    assert len(result) == original_len
    assert list(result["Attribute"]) == list(frame["Attribute"])


# ---------------------------------------------------------------------------
# fill_zero_with_avg
# ---------------------------------------------------------------------------


def test_fill_zero_with_avg_replaces_zero_rate() -> None:
    """Zero Net Rev Per Lb values are replaced with the cross-row average rate."""
    # Arrange: avg = sum(net_rev)/sum(lbs) = (90 + 10) / (10 + 0) -> uses all rows.
    frame = pd.DataFrame(
        {
            "Lbs": [10.0, 5.0],
            "Net-Revenue $": [90.0, 10.0],
            "Net Rev Per Lb": [9.0, 0.0],
        }
    )

    # Act
    result = fill_zero_with_avg(frame, "Lbs", "Net-Revenue $", "Net Rev Per Lb")

    # Assert: avg = 100 / 15; the zero row is replaced, the nonzero row kept.
    expected_avg = 100.0 / 15.0
    assert _f(result.loc[0, "Net Rev Per Lb"]) == 9.0
    assert abs(_f(result.loc[1, "Net Rev Per Lb"]) - expected_avg) < 1e-12


def test_fill_zero_with_avg_zero_lbs_sum_uses_zero() -> None:
    """A non-positive Lbs sum yields a zero average (no divide-by-zero)."""
    # Arrange: all Lbs are zero so the average guard returns 0.
    frame = pd.DataFrame(
        {
            "Lbs": [0.0, 0.0],
            "Net-Revenue $": [0.0, 0.0],
            "Net Rev Per Lb": [0.0, 0.0],
        }
    )

    # Act
    result = fill_zero_with_avg(frame, "Lbs", "Net-Revenue $", "Net Rev Per Lb")

    # Assert: zeros replaced by 0.0 (unchanged).
    assert list(result["Net Rev Per Lb"]) == [0.0, 0.0]
