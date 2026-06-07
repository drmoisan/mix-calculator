"""Unit tests for find_best_match scoring and selection (AC2, AC3).

These tests verify that :func:`src.schema_matching.find_best_match` scores each
candidate schema by required-column coverage (with alias support), selects the
highest-scoring schema, handles an empty candidate list, and reproduces the
user-story LE-drift scenario (two renamed required columns yield a sub-threshold
score and a report naming the two unmatched columns with closest candidates).

All schemas are in-process Feature A model objects; there is no filesystem,
network, or temp-file usage.
"""

from __future__ import annotations

from src.schema_matching import MatchResult, find_best_match
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref


def _schema(
    name: str,
    version: str,
    columns: tuple[ColumnSpec, ...],
) -> SchemaDefinition:
    """Build a valid schema whose key references the first declared column.

    Args:
        name: The schema identity name.
        version: The schema version string.
        columns: The column specs in declaration order.

    Returns:
        A constructed :class:`SchemaDefinition` satisfying model invariants.
    """
    return SchemaDefinition(
        name=name,
        version=version,
        columns=columns,
        key=KeySpec(parts=tuple(column_ref(_n) for _n in (columns[0].canonical_name,))),
    )


def test_find_best_match_selects_highest_coverage_schema() -> None:
    """The schema covering the most required columns is selected."""
    # Arrange: a two-column schema fully covered by the headers and a three-column
    # schema only partially covered.
    full = _schema(
        "full",
        "1",
        (
            ColumnSpec(canonical_name="sku", role="dimension"),
            ColumnSpec(canonical_name="region", role="dimension"),
        ),
    )
    partial = _schema(
        "partial",
        "1",
        (
            ColumnSpec(canonical_name="sku", role="dimension"),
            ColumnSpec(canonical_name="region", role="dimension"),
            ColumnSpec(canonical_name="net sales", role="measure"),
        ),
    )
    headers = ["SKU", "Region"]

    # Act
    result = find_best_match(headers, [partial, full])

    # Assert: the fully covered schema wins with a score of 1.0.
    assert isinstance(result, MatchResult)
    assert result.schema is full
    assert result.score == 1.0


def test_find_best_match_empty_schema_list_returns_none() -> None:
    """An empty candidate list yields schema=None and score 0.0."""
    # Arrange + Act
    result = find_best_match(["SKU", "Region"], [])

    # Assert: no schema selected and an empty report.
    assert result.schema is None
    assert result.score == 0.0
    assert result.report.unmatched_required == ()


def test_alias_based_matching_counts_toward_coverage() -> None:
    """A header matching only via a declared alias still covers the column."""
    # Arrange: the header "net_sales" matches the canonical "net sales" only
    # because the column declares it as an alias.
    schema = _schema(
        "aliased",
        "1",
        (
            ColumnSpec(
                canonical_name="net sales",
                role="measure",
                aliases=("net_sales",),
            ),
        ),
    )
    headers = ["net_sales"]

    # Act
    result = find_best_match(headers, [schema])

    # Assert: alias resolution drives full coverage.
    assert result.schema is schema
    assert result.score == 1.0


def test_le_drift_scenario_yields_subthreshold_score_and_report() -> None:
    """LE drift: two renamed required columns lower the score and are reported.

    Mirrors the user story: an LE-like schema has two required columns renamed in
    the source beyond the fuzzy threshold, so coverage is partial and the report
    names the two unmatched columns with their closest actual candidates.
    """
    # Arrange: four required columns; two headers match, two are renamed past the
    # threshold so they do not resolve.
    le = _schema(
        "le",
        "1",
        (
            ColumnSpec(canonical_name="sku", role="dimension"),
            ColumnSpec(canonical_name="region", role="dimension"),
            ColumnSpec(canonical_name="net sales", role="measure"),
            ColumnSpec(canonical_name="gross sales", role="measure"),
        ),
    )
    # "revenue" and "turnover" share no normalized similarity with the renamed
    # measure columns, so those two required columns stay unmatched.
    headers = ["SKU", "Region", "revenue", "turnover"]

    # Act
    result = find_best_match(headers, [le])

    # Assert: partial coverage (2 of 4) and a report naming both renamed columns.
    assert result.schema is le
    assert result.score == 0.5
    unmatched_names = {
        column.canonical_name for column in result.report.unmatched_required
    }
    assert unmatched_names == {"net sales", "gross sales"}
    rendered = result.report.render()
    assert "net sales" in rendered
    assert "gross sales" in rendered


def test_tie_break_prefers_newer_version() -> None:
    """Equal coverage resolves to the newer schema version."""
    # Arrange: identical single-column coverage, differing only by version.
    older = _schema("same", "1", (ColumnSpec(canonical_name="sku", role="dimension"),))
    newer = _schema("same", "2", (ColumnSpec(canonical_name="sku", role="dimension"),))
    headers = ["SKU"]

    # Act
    result = find_best_match(headers, [older, newer])

    # Assert: both score 1.0; the newer version is selected.
    assert result.score == 1.0
    assert result.schema is newer


def test_tie_break_prefers_lexicographically_smaller_name() -> None:
    """Equal coverage and version resolve to the smaller schema name."""
    # Arrange: identical coverage and version, differing only by name.
    beta = _schema("beta", "1", (ColumnSpec(canonical_name="sku", role="dimension"),))
    alpha = _schema("alpha", "1", (ColumnSpec(canonical_name="sku", role="dimension"),))
    headers = ["SKU"]

    # Act
    result = find_best_match(headers, [beta, alpha])

    # Assert: the lexicographically smaller name ("alpha") is selected.
    assert result.score == 1.0
    assert result.schema is alpha


def test_tie_break_is_deterministic_across_repeated_calls() -> None:
    """Repeated calls return identical selection for both tie-break pairs (AC3)."""
    # Arrange: a version-tie pair and a name-tie pair scored against the same
    # single-column headers.
    sku = (ColumnSpec(canonical_name="sku", role="dimension"),)
    version_older = _schema("same", "1", sku)
    version_newer = _schema("same", "2", sku)
    name_beta = _schema("beta", "1", sku)
    name_alpha = _schema("alpha", "1", sku)
    headers = ["SKU"]

    # Act: call each pair multiple times to confirm stable, repeatable output.
    version_results = [
        find_best_match(headers, [version_older, version_newer]) for _ in range(5)
    ]
    name_results = [find_best_match(headers, [name_beta, name_alpha]) for _ in range(5)]

    # Assert: every repeated call yields the same version-tie and name-tie winner.
    assert all(result.schema is version_newer for result in version_results)
    assert all(result.schema is name_alpha for result in name_results)
