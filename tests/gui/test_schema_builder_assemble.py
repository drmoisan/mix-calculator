"""Tests for ``assemble_schema`` forwarding ``in_output`` from builder state (#54).

Verifies that the schema-builder state's 5-tuple column rows
(``(canonical_name, role, required, in_output, aliases)``) forward the
``in_output`` flag into the assembled :class:`~src.schema_model.ColumnSpec`, so a
builder-authored schema can express processing-only columns (in_output=false)
distinct from source-required columns. Pure transform; no Qt, disk, or network.
"""

from __future__ import annotations

from src.gui.presenters._schema_builder_state import (
    SchemaBuilderState,
    assemble_schema,
)
from src.schema_model import column_ref


def test_assemble_schema_forwards_in_output_true_and_false() -> None:
    """assemble_schema maps each row's in_output flag onto its ColumnSpec (AC7)."""
    # Arrange: two rows, one in_output=True and one in_output=False, sharing a key.
    state = SchemaBuilderState(
        name="builder_schema",
        version="1.0",
        columns=[
            ("Customer", "dimension", True, True, ()),
            ("YTD/YTG", "discriminator", False, False, ()),
        ],
        key_parts=[column_ref("Customer")],
    )

    # Act
    schema = assemble_schema(state)

    # Assert: the in_output flag round-trips per row onto the model column specs.
    by_name = {c.canonical_name: c for c in schema.columns}
    assert by_name["Customer"].in_output is True
    assert by_name["YTD/YTG"].in_output is False
    # required is forwarded independently of in_output (source-presence vs output).
    assert by_name["YTD/YTG"].required is False


def test_assemble_schema_default_in_output_true_row() -> None:
    """A row authored with in_output=True yields an output column (AC7)."""
    # Arrange: a single in_output=True column row.
    state = SchemaBuilderState(
        name="s",
        version="1.0",
        columns=[("Sales", "measure", True, True, ())],
        key_parts=[column_ref("Sales")],
    )

    # Act
    schema = assemble_schema(state)

    # Assert: the assembled column carries in_output=True.
    assert schema.columns[0].in_output is True
