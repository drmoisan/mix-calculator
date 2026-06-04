"""Tests for the pure AOP validation helpers in :mod:`src._load_aop_helpers`.

Covers the corrected per-row total-identity construction
(:func:`build_per_row_checks`) and the end-to-end
:func:`validate_aop` behavior for the partial-year ("8+4") and full-year sheet
shapes, including the genuine-violation negative paths. All values used here are
synthetic; no confidential workbook figures appear (AC-15).
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src._load_aop_helpers import (
    MONTHS,
    QUARTER_COLUMNS,
    YTG_MONTHS,
    build_per_row_checks,
    validate_aop,
)

# Jan..Apr — the complementary months YTD must cover when YTG is present.
_NON_YTG_MONTHS = [month for month in MONTHS if month not in YTG_MONTHS]


def test_build_per_row_checks_ytg_present_splits_year() -> None:
    """With YTG present, YTD covers Jan..Apr and YTG covers May..Dec."""
    # Arrange: a column set that includes the optional YTG column.
    columns = [*MONTHS, "YTD", *QUARTER_COLUMNS, "YTG"]

    # Act
    checks = build_per_row_checks(columns)

    # Assert: YTD is the complementary (non-YTG) months Jan..Apr; YTG is May..Dec.
    assert checks["YTD"] == _NON_YTG_MONTHS
    assert checks["YTD"] == ["Jan", "Feb", "Mar", "Apr"]
    assert checks["YTG"] == YTG_MONTHS
    assert checks["YTG"] == ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def test_build_per_row_checks_ytg_present_includes_quarters() -> None:
    """The quarter identities are present and independent of YTG."""
    # Arrange
    columns = [*MONTHS, "YTD", *QUARTER_COLUMNS, "YTG"]

    # Act
    checks = build_per_row_checks(columns)

    # Assert: each quarter maps to its three constituent months in order.
    assert checks["Q1"] == ["Jan", "Feb", "Mar"]
    assert checks["Q2"] == ["Apr", "May", "Jun"]
    assert checks["Q3"] == ["Jul", "Aug", "Sep"]
    assert checks["Q4"] == ["Oct", "Nov", "Dec"]


def test_build_per_row_checks_ytg_absent_uses_full_year_for_ytd() -> None:
    """With YTG absent, YTD covers the full Jan..Dec year and YTG is not checked."""
    # Arrange: a full-year column set with no YTG column.
    columns = [*MONTHS, "YTD", *QUARTER_COLUMNS]

    # Act
    checks = build_per_row_checks(columns)

    # Assert: YTD spans the full year and no YTG identity is added.
    assert checks["YTD"] == MONTHS
    assert "YTG" not in checks


@given(extra_columns=st.lists(st.sampled_from([*MONTHS, "YTD", *QUARTER_COLUMNS])))
def test_build_per_row_checks_ytd_ytg_partition_property(
    extra_columns: list[str],
) -> None:
    """Property: the YTD/YTG month sets partition the year when YTG is present.

    For any column set, adding YTG makes YTD-months and YTG-months disjoint and
    their union equal to MONTHS; removing YTG makes YTD cover the full year. The
    extra columns are drawn from synthetic, non-YTG labels so the only toggled
    variable is the presence of YTG.
    """
    # Arrange: with-YTG and without-YTG variants of the same synthetic column set.
    with_ytg = [*extra_columns, "YTG"]
    without_ytg = list(extra_columns)

    # Act
    checks_with = build_per_row_checks(with_ytg)
    checks_without = build_per_row_checks(without_ytg)

    # Assert: YTD and YTG partition the calendar year when YTG is present.
    ytd_set = set(checks_with["YTD"])
    ytg_set = set(checks_with["YTG"])
    assert ytd_set.isdisjoint(ytg_set)
    assert ytd_set | ytg_set == set(MONTHS)
    # And YTD covers the full year when YTG is absent.
    assert checks_without["YTD"] == MONTHS
    assert "YTG" not in checks_without


def _synthetic_row(
    *,
    months: list[float],
    ytd: float,
    ytg: float | None,
) -> dict[str, object]:
    """Build a single synthetic AOP row dict for validate_aop tests.

    Args:
        months: The twelve synthetic monthly values, Jan..Dec.
        ytd: The synthetic YTD total to place on the row.
        ytg: The synthetic YTG total, or ``None`` to omit the YTG column.

    Returns:
        A row dict carrying KEY, the twelve months, YTD, the four quarters
        (computed from the months so the quarter identities hold), and YTG when
        provided. All values are synthetic.
    """
    record: dict[str, object] = {"KEY": "k1"}
    # Populate the twelve monthly columns from the synthetic vector.
    for index, month in enumerate(MONTHS):
        record[month] = months[index]
    record["YTD"] = ytd
    # Quarters tie out to their constituent months so only the YTD/YTG identity
    # is the variable under test.
    record["Q1"] = float(sum(months[0:3]))
    record["Q2"] = float(sum(months[3:6]))
    record["Q3"] = float(sum(months[6:9]))
    record["Q4"] = float(sum(months[9:12]))
    if ytg is not None:
        record["YTG"] = ytg
    return record


def test_validate_aop_ytg_present_passes_on_corrected_identity() -> None:
    """A YTG-present row where YTD=sum(Jan..Apr) and YTG=sum(May..Dec) passes."""
    # Arrange: synthetic monthly values; YTD ties to Jan..Apr, YTG to May..Dec.
    months = [float(value) for value in range(1, 13)]
    ytd = float(sum(months[0:4]))
    ytg = float(sum(months[4:12]))
    frame = pd.DataFrame([_synthetic_row(months=months, ytd=ytd, ytg=ytg)])

    # Act / Assert: the corrected identity validates without raising.
    assert validate_aop(frame) is None


def test_validate_aop_full_year_passes_when_ytg_absent() -> None:
    """A full-year row (no YTG) where YTD=sum(Jan..Dec) passes."""
    # Arrange: synthetic monthly values; YTD ties to the full year, no YTG.
    months = [float(value) for value in range(1, 13)]
    ytd = float(sum(months))
    frame = pd.DataFrame([_synthetic_row(months=months, ytd=ytd, ytg=None)])

    # Act / Assert: full-year behavior is unchanged.
    assert validate_aop(frame) is None


def test_validate_aop_ytg_present_raises_on_bad_ytd() -> None:
    """A YTG-present row whose YTD != sum(Jan..Apr) raises ValueError."""
    # Arrange: YTD set to the (wrong) full-year sum so the corrected check fires.
    months = [float(value) for value in range(1, 13)]
    bad_ytd = float(sum(months))  # full-year sum, not sum(Jan..Apr)
    ytg = float(sum(months[4:12]))
    frame = pd.DataFrame([_synthetic_row(months=months, ytd=bad_ytd, ytg=ytg)])

    # Act / Assert: a genuine YTD identity violation still raises.
    with pytest.raises(ValueError, match="YTD"):
        validate_aop(frame)


def test_validate_aop_ytg_present_raises_on_bad_ytg() -> None:
    """A YTG-present row whose YTG != sum(May..Dec) raises ValueError."""
    # Arrange: YTD correct (Jan..Apr) but YTG perturbed beyond tolerance.
    months = [float(value) for value in range(1, 13)]
    ytd = float(sum(months[0:4]))
    bad_ytg = float(sum(months[4:12])) + 5.0
    frame = pd.DataFrame([_synthetic_row(months=months, ytd=ytd, ytg=bad_ytg)])

    # Act / Assert: a genuine YTG identity violation still raises.
    with pytest.raises(ValueError, match="YTG"):
        validate_aop(frame)


def test_validate_aop_full_year_raises_on_bad_ytd() -> None:
    """A full-year row (no YTG) whose YTD != sum(Jan..Dec) raises ValueError."""
    # Arrange: YTD perturbed beyond tolerance with no YTG column present.
    months = [float(value) for value in range(1, 13)]
    bad_ytd = float(sum(months)) + 3.0
    frame = pd.DataFrame([_synthetic_row(months=months, ytd=bad_ytd, ytg=None)])

    # Act / Assert: the full-year identity violation still raises.
    with pytest.raises(ValueError, match="YTD"):
        validate_aop(frame)
