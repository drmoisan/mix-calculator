"""Unit tests for the non-raising column probe and the resolver regression.

These tests verify that :func:`src.etl_column_probe.probe_columns` performs the
same position + fuzzy resolution as the production resolver but returns partial
results without raising, and that :func:`src.etl_columns.resolve_columns` retains
its raising contract unchanged (AC1).
"""

from __future__ import annotations

import pytest

from src.etl_column_probe import ProbeResult, probe_columns
from src.etl_columns import resolve_columns


def test_probe_fully_matched_set_has_no_unmatched() -> None:
    """A fully resolvable set binds every expected column with no leftovers."""
    # Arrange: actual headers carry typographic variants of the expected names.
    actual = ["SKU #", "Region Name", "Net Sales"]
    expected = ["sku", "region name", "net sales"]

    # Act
    result = probe_columns(actual, expected)

    # Assert: every expected column is matched; nothing is left unmatched.
    assert isinstance(result, ProbeResult)
    assert result.matched == {
        "sku": "SKU #",
        "region name": "Region Name",
        "net sales": "Net Sales",
    }
    assert result.unmatched_expected == []
    assert result.unmatched_actual == []


def test_probe_partial_match_returns_unmatched_without_raising() -> None:
    """A partially resolvable set returns the bound subset plus the gaps."""
    # Arrange: "region" resolves; "quarter" has no plausible actual header.
    actual = ["Region", "Totally Unrelated Label"]
    expected = ["region", "quarter"]

    # Act
    result = probe_columns(actual, expected)

    # Assert: region bound; quarter reported unmatched; the unrelated header is
    # reported as an unmatched actual column — and nothing raised.
    assert result.matched == {"region": "Region"}
    assert result.unmatched_expected == ["quarter"]
    assert result.unmatched_actual == ["Totally Unrelated Label"]


def test_probe_all_unmatched_set() -> None:
    """When nothing resolves, all expected and all actual are unmatched."""
    # Arrange: actual headers share no normalized similarity with expected.
    actual = ["aaaaaa", "bbbbbb"]
    expected = ["zzzzzz", "yyyyyy"]

    # Act
    result = probe_columns(actual, expected)

    # Assert
    assert result.matched == {}
    assert result.unmatched_expected == ["zzzzzz", "yyyyyy"]
    assert result.unmatched_actual == ["aaaaaa", "bbbbbb"]


def test_probe_extra_actual_columns_reported_as_unmatched_actual() -> None:
    """Unrecognized actual columns are reported in unmatched_actual."""
    # Arrange: one extra actual header beyond the single expected column.
    actual = ["SKU", "Mystery Column", "Another Extra"]
    expected = ["sku"]

    # Act
    result = probe_columns(actual, expected)

    # Assert: sku bound; the two extras are returned in source order.
    assert result.matched == {"sku": "SKU"}
    assert result.unmatched_expected == []
    assert result.unmatched_actual == ["Mystery Column", "Another Extra"]


def test_probe_threshold_boundary_excludes_below_threshold_match() -> None:
    """A near-miss below the threshold is not bound; above-threshold binds."""
    # Arrange: a header whose normalized similarity to the expected name is
    # high but not exact. A very high threshold should reject the fuzzy bind.
    actual = ["Regino"]
    expected = ["region"]

    # Act: a threshold of 1.0 forbids any non-exact match.
    strict = probe_columns(actual, expected, threshold=1.0)
    # Act: a permissive threshold accepts the near-miss as a fuzzy match.
    lenient = probe_columns(actual, expected, threshold=0.5)

    # Assert: strict leaves the column unmatched; lenient binds it.
    assert strict.matched == {}
    assert strict.unmatched_expected == ["region"]
    assert strict.unmatched_actual == ["Regino"]
    assert lenient.matched == {"region": "Regino"}
    assert lenient.unmatched_expected == []


def test_probe_never_raises_on_mismatch() -> None:
    """probe_columns returns a result rather than raising on a mismatch."""
    # Arrange: a required-style expected column with no candidate header.
    actual = ["irrelevant"]
    expected = ["net sales", "gross sales"]

    # Act + Assert: the call completes and yields a ProbeResult, never raising.
    result = probe_columns(actual, expected)
    assert isinstance(result, ProbeResult)
    assert set(result.unmatched_expected) == {"net sales", "gross sales"}


def test_probe_matches_resolver_on_position_pass_input() -> None:
    """Parity: probe bindings equal resolve_columns on a position-pass input.

    A fully in-order input is resolved entirely by the position pass; the probe
    must bind the identical expected->actual pairs and report the same extras.
    """
    # Arrange: in-order headers plus one spare column the resolver returns as an
    # extra and the probe returns as an unmatched actual.
    actual = ["SKU #", "Region", "Spare Column"]
    expected = ["sku", "region"]

    # Act: resolve_columns succeeds (no raise) so the inputs are fully resolvable.
    resolve_mapping, resolve_extras = resolve_columns(actual, expected)
    probe_result = probe_columns(actual, expected)

    # Assert: byte-equal matched mapping and matching unmatched-actual sets.
    assert probe_result.matched == resolve_mapping
    assert set(probe_result.unmatched_actual) == set(resolve_extras)
    assert probe_result.unmatched_expected == []


def test_probe_matches_resolver_on_fuzzy_pass_input() -> None:
    """Parity: probe bindings equal resolve_columns on a fuzzy-pass input.

    A typo/variant actual name above the threshold is bound only by the fuzzy
    pass. The locally reimplemented fuzzy helper must select the same actual
    header the resolver's private helper selects.
    """
    # Arrange: "Regin" is a typo variant of "region" that clears the default
    # threshold, exercising the fuzzy pass rather than the position pass.
    actual = ["Regin", "Net Sales", "Unrelated Extra"]
    expected = ["region", "net sales"]

    # Act: resolve_columns does not raise, confirming the input is resolvable.
    resolve_mapping, resolve_extras = resolve_columns(actual, expected)
    probe_result = probe_columns(actual, expected)

    # Assert: the fuzzy-bound mapping matches and the extras agree.
    assert probe_result.matched == resolve_mapping
    assert set(probe_result.unmatched_actual) == set(resolve_extras)
    assert probe_result.unmatched_expected == []


def test_resolve_columns_raises_on_unresolvable_required_column() -> None:
    """Regression: resolve_columns still raises ValueError when unresolvable."""
    # Arrange: an expected column with no plausible actual header.
    actual = ["irrelevant header"]
    expected = ["net sales"]

    # Act + Assert: the raising contract is preserved and the message names the
    # unmatched required column (AC1).
    with pytest.raises(ValueError, match="net sales"):
        resolve_columns(actual, expected)


def test_resolve_columns_returns_mapping_and_extras_when_resolvable() -> None:
    """Regression: resolve_columns returns the same (mapping, extras) shape."""
    # Arrange
    actual = ["SKU #", "Region", "Spare Column"]
    expected = ["sku", "region"]

    # Act
    mapping, extras = resolve_columns(actual, expected)

    # Assert: bound mapping plus the unclaimed extra in source order.
    assert mapping == {"sku": "SKU #", "region": "Region"}
    assert extras == ["Spare Column"]
