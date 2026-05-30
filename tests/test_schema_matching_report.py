"""Unit tests for the typed MismatchReport and its renderer (AC5, AC6).

These tests verify that :func:`src.schema_matching.build_mismatch_report`
produces a structured report whose unmatched required columns carry their
declared aliases and closest actual candidates (descending similarity, capped at
N), that unrecognized actual columns are listed, and that
:meth:`src.schema_matching.MismatchReport.render` returns a non-empty string
naming each unmatched required column.

All schemas are built from in-process Feature A model objects; there is no
filesystem, network, or temp-file usage.
"""

from __future__ import annotations

from src.schema_matching import (
    DEFAULT_MAX_CANDIDATES,
    build_mismatch_report,
)
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition


def _schema_with_columns(columns: tuple[ColumnSpec, ...]) -> SchemaDefinition:
    """Build a minimal valid schema whose key references the first column.

    Args:
        columns: The column specs to include, in declaration order.

    Returns:
        A constructed :class:`SchemaDefinition` whose key names the first column,
        satisfying the model's structural invariants.
    """
    # The key must name a declared column; use the first one to keep the fixture
    # minimal while staying valid.
    return SchemaDefinition(
        name="test-schema",
        version="1",
        columns=columns,
        key=KeySpec(columns=(columns[0].canonical_name,)),
    )


def test_unmatched_required_column_lists_aliases_and_candidates() -> None:
    """An unmatched required column carries its aliases and ranked candidates."""
    # Arrange: a required column with aliases and no plausible actual header,
    # plus an actual header that is a weak near-miss.
    schema = _schema_with_columns(
        (
            ColumnSpec(
                canonical_name="net sales",
                role="measure",
                aliases=("net_sales", "netsales"),
            ),
        )
    )
    actual = ["region label"]

    # Act: a strict threshold guarantees the near-miss does not bind.
    report = build_mismatch_report(actual, schema, threshold=1.0)

    # Assert: the unmatched column reports its canonical name, declared aliases,
    # and at least one ranked candidate.
    assert len(report.unmatched_required) == 1
    column = report.unmatched_required[0]
    assert column.canonical_name == "net sales"
    assert column.aliases == ("net_sales", "netsales")
    assert len(column.candidates) >= 1
    assert column.candidates[0].actual_name == "region label"


def test_candidates_are_sorted_descending_and_capped_at_max() -> None:
    """Closest candidates are ordered by descending score and capped at N."""
    # Arrange: more actual headers than the candidate cap so the cap is exercised.
    schema = _schema_with_columns(
        (ColumnSpec(canonical_name="region", role="dimension"),)
    )
    actual = ["regiom", "regon", "rgn", "totally different", "another label"]

    # Act: a strict threshold keeps every header unmatched so all are ranked.
    report = build_mismatch_report(actual, schema, threshold=1.0)

    # Assert: candidate count is capped and scores are non-increasing.
    column = report.unmatched_required[0]
    assert len(column.candidates) == DEFAULT_MAX_CANDIDATES
    scores = [candidate.score for candidate in column.candidates]
    assert scores == sorted(scores, reverse=True)


def test_unrecognized_actual_columns_are_listed() -> None:
    """Actual headers that no required column claimed are reported."""
    # Arrange: one required column that binds, plus two extra headers.
    schema = _schema_with_columns((ColumnSpec(canonical_name="sku", role="dimension"),))
    actual = ["SKU", "Mystery", "Another Extra"]

    # Act
    report = build_mismatch_report(actual, schema)

    # Assert: sku bound (no unmatched required); the extras are unrecognized.
    assert report.unmatched_required == ()
    assert report.unrecognized_actual == ("Mystery", "Another Extra")


def test_render_names_each_unmatched_required_column() -> None:
    """render() returns a non-empty string naming each unmatched column."""
    # Arrange: two unmatched required columns and one unrecognized header.
    schema = _schema_with_columns(
        (
            ColumnSpec(canonical_name="net sales", role="measure"),
            ColumnSpec(canonical_name="gross sales", role="measure"),
        )
    )
    actual = ["unrelated header"]

    # Act
    report = build_mismatch_report(actual, schema, threshold=1.0)
    rendered = report.render()

    # Assert: the rendered text names each unmatched required column and the
    # unrecognized header.
    assert rendered
    assert "net sales" in rendered
    assert "gross sales" in rendered
    assert "unrelated header" in rendered


def test_render_all_matched_returns_confirmation_line() -> None:
    """render() returns a confirmation when nothing is unmatched."""
    # Arrange: a single required column that binds exactly, no extras.
    schema = _schema_with_columns((ColumnSpec(canonical_name="sku", role="dimension"),))
    actual = ["SKU"]

    # Act
    report = build_mismatch_report(actual, schema)
    rendered = report.render()

    # Assert: empty report renders a short all-matched confirmation.
    assert report.unmatched_required == ()
    assert report.unrecognized_actual == ()
    assert "All required columns matched" in rendered


def test_unmatched_column_with_no_aliases_renders_without_alias_text() -> None:
    """A column without aliases renders cleanly without an alias fragment."""
    # Arrange: a required column declaring no aliases.
    schema = _schema_with_columns(
        (ColumnSpec(canonical_name="quarter", role="dimension"),)
    )
    actual = ["unrelated"]

    # Act
    report = build_mismatch_report(actual, schema, threshold=1.0)
    rendered = report.render()

    # Assert: the column is named, and no "aliases:" fragment appears.
    assert "quarter" in rendered
    assert "aliases:" not in rendered
