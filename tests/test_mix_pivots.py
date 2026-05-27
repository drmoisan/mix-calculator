"""Unit tests for the ``pivot_le`` and ``pivot_aop`` primitives.

Split from ``test_mix_transforms.py`` to keep each test file under the 500-line
limit. Covers the long-to-wide source-shaping pivots: negation of the three
deduction columns, the ``Net-Revenue $`` derivation, the appended ratio columns,
the AOP percent-type drop and ``LBs`` -> ``Lbs`` rename, the missing-measure
zero-fill branches, and the ``pivot_aop`` ``YTG``-absent ``May..Dec`` fallback.
Fabricated data only; no confidential values appear.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from src.mix_transforms import pivot_aop, pivot_le


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _le_raw_rows() -> pd.DataFrame:
    """Build a raw long LE frame with the five GtN labels for one SKU."""
    base = {
        "Customer": "Acme Foods",
        "Super Category": "Category X",
        "PPG": "PPG-1",
        "SKU Descripiton": "Widget A",
        "SKU #": "SKU-200",
    }
    labels = [
        ("Gross Sales", 100.0),
        ("Lbs", 10.0),
        ("Off Invoice", 5.0),
        ("Trade", 2.0),
        ("Non-Trade", 1.0),
    ]
    return pd.DataFrame(
        [{**base, "GtN Mapping": label, "YTG": value} for label, value in labels]
    )


def test_pivot_le_negates_and_adds_net_revenue() -> None:
    """pivot_le negates deductions, derives net revenue, and melts to long."""
    # Arrange
    le_raw = _le_raw_rows()

    # Act
    long_frame = pivot_le(le_raw)

    # Assert: long-form Attribute/Value with negated deductions and net revenue.
    by_attr = long_frame.set_index("Attribute")["Value"]
    assert _f(by_attr.loc["Gross Sales"]) == 100.0
    assert _f(by_attr.loc["Off Invoice $"]) == -5.0
    assert _f(by_attr.loc["Trade Spend $"]) == -2.0
    assert _f(by_attr.loc["Non-Trade $"]) == -1.0
    # Net revenue = 100 + (-5) + (-2) + (-1) = 92.
    assert _f(by_attr.loc["Net-Revenue $"]) == 92.0
    # Ratios are present and computed.
    assert _f(by_attr.loc["Net Rev Per Lb"]) == 9.2


def _aop_raw_rows(*, include_ytg: bool) -> pd.DataFrame:
    """Build a raw long AOP frame; optionally omit YTG to exercise the fallback."""
    base = {
        "Customer Master": "Master Group",
        "Customer": "Acme Foods",
        "Super Category": "Category X",
        "PPG": "PPG-1",
        "SKU Descripiton": "Widget A",
        "SKU #": "SKU-300",
    }
    # Each type carries a May..Dec monthly profile summing to its YTG value.
    types = [
        ("Gross Sales", 80.0),
        ("LBs", 8.0),
        ("Cases", 4.0),
        ("Off Invoice $", 4.0),
        ("Trade Spend $", 1.6),
        ("Non-Trade $", 0.8),
        ("Off Invoice %", 0.05),
    ]
    months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    records: list[dict[str, object]] = []
    for type_label, ytg in types:
        record: dict[str, object] = {**base, "Type": type_label}
        # Spread the YTG over the eight months so the fallback sum reproduces it.
        for month in months:
            record[month] = ytg / 8.0
        if include_ytg:
            record["YTG"] = ytg
        records.append(record)
    return pd.DataFrame(records)


def test_pivot_aop_drops_percent_and_renames_lbs() -> None:
    """pivot_aop drops percent types, renames LBs, and computes net revenue."""
    # Arrange
    aop_raw = _aop_raw_rows(include_ytg=True)

    # Act
    long_frame = pivot_aop(aop_raw)

    # Assert
    attributes = set(long_frame["Attribute"])
    assert "Off Invoice %" not in attributes
    assert "Lbs" in attributes
    assert "LBs" not in attributes
    by_attr = long_frame.set_index("Attribute")["Value"]
    assert _f(by_attr.loc["Off Invoice $"]) == -4.0
    # Net revenue = 80 + (-4) + (-1.6) + (-0.8) = 73.6.
    assert abs(_f(by_attr.loc["Net-Revenue $"]) - 73.6) < 1e-9


def test_pivot_le_fills_missing_measure_columns_with_zero() -> None:
    """A GtN label missing from the source is created as a zero measure column."""
    # Arrange: omit the Trade label so the Trade Spend $ column must be filled.
    le_raw = _le_raw_rows()
    le_raw = le_raw[le_raw["GtN Mapping"] != "Trade"].copy()

    # Act
    long_frame = pivot_le(le_raw)

    # Assert: Trade Spend $ exists and is zero; net revenue reflects the absence.
    by_attr = long_frame.set_index("Attribute")["Value"]
    assert _f(by_attr.loc["Trade Spend $"]) == 0.0
    # Net revenue = 100 + (-5) + 0 + (-1) = 94.
    assert _f(by_attr.loc["Net-Revenue $"]) == 94.0


def test_pivot_aop_already_named_lbs_and_missing_measure() -> None:
    """pivot_aop handles a source whose Lbs type is already 'Lbs' and a gap."""
    # Arrange: rename LBs to Lbs in the source and drop Non-Trade $ so both the
    # already-named-Lbs branch and the missing-measure fill branch are exercised.
    aop_raw = _aop_raw_rows(include_ytg=True)
    aop_raw["Type"] = aop_raw["Type"].replace({"LBs": "Lbs"})
    aop_raw = aop_raw[aop_raw["Type"] != "Non-Trade $"].copy()

    # Act
    long_frame = pivot_aop(aop_raw)

    # Assert
    by_attr = long_frame.set_index("Attribute")["Value"]
    assert _f(by_attr.loc["Lbs"]) == 8.0
    assert _f(by_attr.loc["Non-Trade $"]) == 0.0
    # Net revenue = 80 + (-4) + (-1.6) + 0 = 74.4.
    assert abs(_f(by_attr.loc["Net-Revenue $"]) - 74.4) < 1e-9


def test_pivot_aop_ytg_absent_falls_back_to_may_dec_sum() -> None:
    """When YTG is absent, pivot_aop derives it by summing May..Dec."""
    # Arrange: no YTG column; the monthly profile reproduces each type's YTG.
    aop_raw = _aop_raw_rows(include_ytg=False)
    assert "YTG" not in aop_raw.columns

    # Act
    long_frame = pivot_aop(aop_raw)

    # Assert: Gross Sales recovered as the May..Dec sum (8 * 10 = 80).
    by_attr = long_frame.set_index("Attribute")["Value"]
    assert abs(_f(by_attr.loc["Gross Sales"]) - 80.0) < 1e-9
    assert abs(_f(by_attr.loc["Net-Revenue $"]) - 73.6) < 1e-9
