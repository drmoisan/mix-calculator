"""Tests for the derived-expression bracket format helper (AC-4, D-1).

These tests verify the display/storage translation isolated in
:mod:`src.gui.widgets._schema_builder_derived_format`: ``[Name]`` display form
maps to ``col("Name")`` stored form and back, names with spaces round-trip, and
the stripped output is valid input to the existing
:class:`~src.schema_formula.FormulaEvaluator` (proving the grammar is unchanged,
D-1). All values are synthetic.
"""

from __future__ import annotations

from src.gui.widgets._schema_builder_derived_format import (
    add_brackets,
    strip_brackets,
)
from src.schema_formula import FormulaEvaluator


def test_strip_brackets_converts_to_col_call() -> None:
    """AC-4: a ``[Name]`` reference strips to the ``col("Name")`` stored form."""
    # Arrange / Act
    stored = strip_brackets("[Revenue] + [Units]")

    # Assert
    assert stored == 'col("Revenue") + col("Units")'


def test_add_brackets_converts_known_col_calls() -> None:
    """AC-4: a known ``col("Name")`` reference re-brackets to ``[Name]``."""
    # Arrange / Act
    display = add_brackets('col("Revenue") + col("Units")', ["Revenue", "Units"])

    # Assert
    assert display == "[Revenue] + [Units]"


def test_strip_brackets_handles_names_with_spaces() -> None:
    """AC-4: names with spaces strip to quoted ``col("...")`` correctly."""
    # Arrange / Act
    stored = strip_brackets("[col a], [col b]")

    # Assert: each bracketed name becomes a quoted col() call; the comma separator
    # stays outside the brackets/calls.
    assert stored == 'col("col a"), col("col b")'


def test_add_brackets_handles_names_with_spaces() -> None:
    """AC-4: known quoted ``col("col a")`` references re-bracket with spaces."""
    # Arrange / Act
    display = add_brackets('col("col a"), col("col b")', ["col a", "col b"])

    # Assert
    assert display == "[col a], [col b]"


def test_bracket_round_trip_is_idempotent_for_known_names() -> None:
    """AC-4: strip then add (and back) round-trips known references exactly."""
    # Arrange
    known = ["col a", "col b"]
    display = "[col a], [col b]"

    # Act: display -> stored -> display.
    stored = strip_brackets(display)
    round_tripped = add_brackets(stored, known)

    # Assert: the round-trip reproduces the original display form.
    assert round_tripped == display
    # Assert: stripping the round-tripped display reproduces the stored form
    # (idempotence of strip on an already-display value).
    assert strip_brackets(round_tripped) == stored


def test_add_brackets_leaves_unknown_references_unchanged() -> None:
    """AC-4: a ``col(...)`` naming an undeclared column is not re-bracketed."""
    # Arrange / Act: only "Revenue" is declared; "Mystery" must stay as col().
    display = add_brackets('col("Revenue") + col("Mystery")', ["Revenue"])

    # Assert
    assert display == '[Revenue] + col("Mystery")'


def test_stripped_output_validates_under_existing_evaluator() -> None:
    """AC-4/D-1: stripped bracket output is valid input to FormulaEvaluator.

    Proves the formula grammar is unchanged: the bracketed display form never
    reaches the evaluator; only the stripped ``col("Name")`` form does, and it
    validates against the declared names.
    """
    # Arrange
    evaluator = FormulaEvaluator()
    declared = ["Off Invoice $", "Units"]

    # Act: strip a bracketed display expression to its stored form.
    stored = strip_brackets("safe_div([Off Invoice $], [Units])")

    # Assert: the stored form is exactly the quoted col() form...
    assert stored == 'safe_div(col("Off Invoice $"), col("Units"))'
    # ...and it validates under the existing evaluator without raising.
    evaluator.validate(stored, declared)


def test_strip_brackets_passes_through_already_stored_form() -> None:
    """AC-4: an expression with no brackets is returned unchanged by strip."""
    # Arrange / Act
    stored = strip_brackets('col("Revenue") + 1')

    # Assert
    assert stored == 'col("Revenue") + 1'
