"""Unit tests for :mod:`src.mix_q1`.

Covers ``build_q1_results_by_sku`` with a fabricated raw-LE fixture: the
``Q1 = Jan + Feb + Mar`` aggregation, the pivot of the GtN measures, the
pre-negation ``Net Rev`` subtraction, the ``$`` renames, and the appended ratio
columns. Arrange-Act-Assert; fabricated data only.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from src.mix_q1 import build_q1_results_by_sku


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _le_raw_q1_rows() -> pd.DataFrame:
    """Build a fabricated raw-LE frame with monthly columns for one SKU."""
    base = {
        "Customer": "Acme Foods",
        "SKU Descripiton": "Widget A",
        "SKU #": "SKU-001",
    }
    # Each GtN label carries a Jan/Feb/Mar profile summing to a known Q1 value.
    labels = [
        ("Gross Sales", 30.0, 30.0, 40.0),  # Q1 = 100
        ("Lbs", 3.0, 3.0, 4.0),  # Q1 = 10
        ("Off Invoice", 1.0, 2.0, 2.0),  # Q1 = 5
        ("Trade", 0.5, 0.5, 1.0),  # Q1 = 2
        ("Non-Trade", 0.4, 0.3, 0.3),  # Q1 = 1
    ]
    return pd.DataFrame(
        [
            {**base, "GtN Mapping": label, "Jan": jan, "Feb": feb, "Mar": mar}
            for label, jan, feb, mar in labels
        ]
    )


def test_q1_aggregates_jan_feb_mar() -> None:
    """Q1 sums the Jan/Feb/Mar months for each GtN measure."""
    # Arrange
    le_raw = _le_raw_q1_rows()

    # Act
    result = build_q1_results_by_sku(le_raw)
    row = result.iloc[0]

    # Assert: Gross Sales Q1 = 30 + 30 + 40 = 100; Lbs Q1 = 10.
    assert _f(row["Gross Sales"]) == 100.0
    assert _f(row["Lbs"]) == 10.0


def test_q1_pivots_gtn_measures_into_columns() -> None:
    """Each GtN label becomes its own measure column after the pivot."""
    # Arrange
    le_raw = _le_raw_q1_rows()

    # Act
    result = build_q1_results_by_sku(le_raw)

    # Assert: the renamed "$" deduction columns are present.
    for column in (
        "Gross Sales",
        "Lbs",
        "Off Invoice $",
        "Trade Spend $",
        "Non-Trade $",
    ):
        assert column in result.columns


def test_q1_net_rev_uses_pre_negation_subtraction() -> None:
    """Net Rev subtracts the (positive) deductions from gross sales."""
    # Arrange
    le_raw = _le_raw_q1_rows()

    # Act
    result = build_q1_results_by_sku(le_raw)
    row = result.iloc[0]

    # Assert: Net Rev = 100 - 5 - 1 - 2 = 92.
    assert _f(row["Net Rev"]) == 92.0
    assert _f(row["Net-Revenue $"]) == 92.0


def test_q1_appends_ratio_columns() -> None:
    """The eight ratio columns are appended to the Q1 table."""
    # Arrange
    le_raw = _le_raw_q1_rows()

    # Act
    result = build_q1_results_by_sku(le_raw)
    row = result.iloc[0]

    # Assert: Net Rev Per Lb = 92 / 10 = 9.2; ratio columns present.
    assert _f(row["Net Rev Per Lb"]) == 9.2
    assert "Gross Sales Per Lb" in result.columns
    assert "OI %GS" in result.columns


def test_q1_missing_gtn_label_filled_zero() -> None:
    """A GtN label absent from the source quarter is created as a zero measure."""
    # Arrange: drop the Trade rows so Trade Spend $ must be zero-filled.
    le_raw = _le_raw_q1_rows()
    le_raw = le_raw[le_raw["GtN Mapping"] != "Trade"].copy()

    # Act
    result = build_q1_results_by_sku(le_raw)
    row = result.iloc[0]

    # Assert: Trade Spend $ is zero; Net Rev = 100 - 5 - 1 - 0 = 94.
    assert _f(row["Trade Spend $"]) == 0.0
    assert _f(row["Net Rev"]) == 94.0
