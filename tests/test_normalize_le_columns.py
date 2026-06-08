"""Unit tests for :func:`src._normalize_le_columns.resolve_le_columns`.

These tests exercise the optional-by-name resolution contract directly at the
pure-helper level: ``YTD/YTG`` and source ``Super Category`` are located by name
when present and tolerated when absent, ``KEY`` is located when present, and a
genuinely missing required column raises ``ValueError`` naming it. All fixtures
are in-memory column-name lists; no workbook, temp file, or network is used, per
the repository unit-test policy.
"""

from __future__ import annotations

import pytest

from src._normalize_le_columns import (
    OPTIONAL_BY_NAME,
    REQUIRED_COLUMNS,
    resolve_le_columns,
)


def _full_source_columns() -> list[str]:
    """Return a full LE source header (required + both optionals + KEY).

    Returns:
        The 23 required columns plus ``YTD/YTG``, ``Super Category``, and ``KEY``,
        matching the standard ``LE-8 + 4`` source header (order is not material to
        ``resolve_le_columns`` since it resolves by name).
    """
    return [*REQUIRED_COLUMNS, "YTD/YTG", "Super Category", "KEY"]


def test_required_columns_has_exactly_23_entries() -> None:
    """REQUIRED_COLUMNS holds exactly the 23 must-have source columns."""
    # Act / Assert: 5 text + 12 months + FY + 4 quarters + PPG = 23.
    assert len(REQUIRED_COLUMNS) == 23


def test_optional_by_name_is_ytd_ytg_and_super_category() -> None:
    """OPTIONAL_BY_NAME lists exactly the two intermediate/derived columns."""
    # Act / Assert
    assert OPTIONAL_BY_NAME == ["YTD/YTG", "Super Category"]


def test_ytd_ytg_absent_is_not_required_and_not_in_selection() -> None:
    """A source without YTD/YTG resolves; YTD/YTG is absent from the selection."""
    # Arrange: full source minus the YTD/YTG column.
    actual = [c for c in _full_source_columns() if c != "YTD/YTG"]

    # Act
    selection, key_actual = resolve_le_columns(actual)

    # Assert: resolution succeeds, KEY is located, and no selection entry maps to
    # the canonical "YTD/YTG" name because the source omitted it.
    assert key_actual == "KEY"
    assert "YTD/YTG" not in selection.values()
    # Super Category was present and is therefore carried.
    assert "Super Category" in selection.values()


def test_source_super_category_absent_is_not_required_and_not_in_selection() -> None:
    """A source without Super Category resolves; it is absent from the selection."""
    # Arrange: full source minus the source Super Category column.
    actual = [c for c in _full_source_columns() if c != "Super Category"]

    # Act
    selection, key_actual = resolve_le_columns(actual)

    # Assert: resolution succeeds and no selection entry maps to the canonical
    # "Super Category" name because the source omitted it.
    assert key_actual == "KEY"
    assert "Super Category" not in selection.values()
    # YTD/YTG was present and is therefore carried.
    assert "YTD/YTG" in selection.values()


def test_both_optionals_present_are_located_and_carried_to_canonical_names() -> None:
    """Both optionals present are located and carried under their canonical names."""
    # Arrange: a full source header with both optionals and KEY present.
    actual = _full_source_columns()

    # Act
    selection, key_actual = resolve_le_columns(actual)

    # Assert: every required column plus both optionals and KEY map to their
    # canonical names (this is the standard full-column parity case).
    canonical_names = set(selection.values())
    for required in REQUIRED_COLUMNS:
        assert required in canonical_names
    assert "YTD/YTG" in canonical_names
    assert "Super Category" in canonical_names
    assert key_actual == "KEY"
    assert selection["KEY"] == "KEY"


def test_missing_required_column_raises_value_error_naming_it() -> None:
    """A source missing a required column (PPG) raises ValueError naming PPG."""
    # Arrange: drop the required PPG column from an otherwise full source.
    actual = [c for c in _full_source_columns() if c != "PPG"]

    # Act / Assert: resolution must fail and name the missing must-have column.
    with pytest.raises(ValueError, match="PPG"):
        resolve_le_columns(actual)
