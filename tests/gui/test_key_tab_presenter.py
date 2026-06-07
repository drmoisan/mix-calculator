"""Unit tests for :class:`KeyTabPresenter` (Decision 2).

These tests exercise the Key-tab presenter with a fake view and a shared
:class:`SchemaBuilderState`, with no ``QApplication`` and no I/O. They verify that
parts maintain insertion/reorder order, that Generic Text is repeatable, that a
default key pattern parses into ordered parts, that composed parts assemble and
round-trip through serialization, and that an all-literal key (no column-ref) is
rejected on assembly.
"""

from __future__ import annotations

import pytest

from src.gui.presenters._key_tab_presenter import KeyTabPresenter
from src.gui.presenters._schema_builder_state import SchemaBuilderState
from src.schema_model import SchemaValidationError


class FakeKeyTabView:
    """Records the calls the Key-tab presenter makes.

    Attributes:
        parts_set: Each ``set_parts`` argument, in order.
    """

    def __init__(self) -> None:
        """Initialize empty call records."""
        self.parts_set: list[list[tuple[str, str]]] = []

    def add_key_part(self, kind: str, value: str) -> None:
        """No-op add seam (the widget calls this; the presenter routes it)."""
        del kind, value

    def set_parts(self, parts: list[tuple[str, str]]) -> None:
        """Record a parts render call."""
        self.parts_set.append(list(parts))

    def reorder_parts(self, order: list[int]) -> None:
        """No-op reorder seam."""
        del order


def test_parts_maintain_insertion_order() -> None:
    """Added parts maintain their insertion order."""
    # Arrange
    view = FakeKeyTabView()
    state = SchemaBuilderState()
    presenter = KeyTabPresenter(view, state)

    # Act: add a column, a literal, then another column.
    presenter.add_column("Customer")
    presenter.add_generic_text("-")
    presenter.add_column("SKU #")

    # Assert: the parts are in insertion order with the correct kinds.
    assert [(p.kind, p.value) for p in presenter.parts] == [
        ("column-ref", "Customer"),
        ("literal-text", "-"),
        ("column-ref", "SKU #"),
    ]


def test_generic_text_is_repeatable_with_own_values() -> None:
    """Generic Text can be placed multiple times, each with its own value."""
    # Arrange
    view = FakeKeyTabView()
    state = SchemaBuilderState()
    presenter = KeyTabPresenter(view, state)

    # Act: a column with two distinct literal segments around it.
    presenter.add_generic_text("PRE-")
    presenter.add_column("Customer")
    presenter.add_generic_text("-POST")

    # Assert: both literals are present with their own values.
    literals = [p.value for p in presenter.parts if p.kind == "literal-text"]
    assert literals == ["PRE-", "-POST"]


def test_reorder_reorders_parts() -> None:
    """reorder applies a permutation to the parts."""
    # Arrange: three parts in order.
    view = FakeKeyTabView()
    state = SchemaBuilderState()
    presenter = KeyTabPresenter(view, state)
    presenter.add_column("Customer")
    presenter.add_generic_text("-")
    presenter.add_column("SKU #")

    # Act: move the second column to the front.
    presenter.reorder([2, 0, 1])

    # Assert
    assert [(p.kind, p.value) for p in presenter.parts] == [
        ("column-ref", "SKU #"),
        ("column-ref", "Customer"),
        ("literal-text", "-"),
    ]


def test_default_pattern_parses_into_ordered_parts() -> None:
    """A default key pattern parses into ordered column and literal parts."""
    # Arrange
    view = FakeKeyTabView()
    state = SchemaBuilderState()
    presenter = KeyTabPresenter(view, state)

    # Act
    presenter.load_default_pattern("{Customer}-{SKU #}")

    # Assert
    assert [(p.kind, p.value) for p in presenter.parts] == [
        ("column-ref", "Customer"),
        ("literal-text", "-"),
        ("column-ref", "SKU #"),
    ]


def test_build_key_round_trips_through_serialization() -> None:
    """Composed parts assemble into a key that round-trips through serialization."""
    # Arrange: compose a key with a literal segment, embed it in a schema, and
    # round-trip the schema through the public serialization API.
    from src.schema_model import ColumnSpec, SchemaDefinition
    from src.schema_serialization import schema_from_json, schema_to_json

    view = FakeKeyTabView()
    state = SchemaBuilderState()
    presenter = KeyTabPresenter(view, state)
    presenter.add_column("Customer")
    presenter.add_generic_text("-")
    presenter.add_column("SKU #")

    # Act: assemble the key into a schema, serialize, and parse back.
    key = presenter.build_key()
    schema = SchemaDefinition(
        name="s",
        version="2.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
        ),
        key=key,
    )
    reloaded = schema_from_json(schema_to_json(schema))

    # Assert: the key parts preserve order and kinds across the round-trip.
    assert [(part.kind, part.value) for part in reloaded.key.parts] == [
        ("column-ref", "Customer"),
        ("literal-text", "-"),
        ("column-ref", "SKU #"),
    ]


def test_build_key_rejects_all_literal_key() -> None:
    """An all-literal key (no column-ref) is rejected on assembly."""
    # Arrange: only literal parts, no column reference.
    view = FakeKeyTabView()
    state = SchemaBuilderState()
    presenter = KeyTabPresenter(view, state)
    presenter.add_generic_text("ABC")
    presenter.add_generic_text("DEF")

    # Act / Assert: assembly raises the model invariant error.
    with pytest.raises(SchemaValidationError):
        presenter.build_key()
