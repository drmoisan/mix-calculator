"""Core unit tests for :class:`SchemaBuilderPresenter` (Feature D, AC4 + AC5).

These tests exercise the schema-builder presenter with a fake view and a fake
schema service, with no ``QApplication`` and no disk/network. They verify that
the presenter assembles a valid schema from the view's edits and saves it,
renders a preview by applying the in-progress schema through the service loader,
validates runtime formula entry through Feature C (accepting valid expressions,
rejecting syntax errors, disallowed constructs, and unknown columns inline), and
surfaces a model :class:`~src.schema_model.SchemaValidationError` as an error.

Seeding / new-from-template tests live in
``test_schema_builder_presenter_seeding``; the two shared helpers live in
``tests.gui._schema_builder_presenter_fixtures``.
"""

from __future__ import annotations

import pytest

from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
from tests.gui._schema_builder_presenter_fixtures import (
    configure_valid_keyable_view,
    stored_schema_with_structured_key_and_aggregate,
)
from tests.gui.fakes.fake_services import FakeSchemaService
from tests.gui.fakes.fake_views import FakeSchemaBuilderView


def test_save_assembles_and_persists_valid_schema() -> None:
    """save assembles a valid schema from the view and persists it."""
    # Arrange
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    saved = presenter.save()

    # Assert: a single schema with the entered identity/columns was saved.
    assert saved is True
    assert len(service.saved) == 1
    assert service.saved[0].name == "keyable"
    assert tuple(c.canonical_name for c in service.saved[0].columns) == (
        "Customer",
        "SKU #",
        "Type",
        "Sales",
    )


def test_save_surfaces_validation_error_for_invalid_schema() -> None:
    """save surfaces the model validation error for a structurally invalid state."""
    # Arrange: empty name violates SchemaDefinition.name non-empty invariant.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    view.identity = ("", "1.0", "")
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    saved = presenter.save()

    # Assert: rejected, nothing persisted, error surfaced.
    assert saved is False
    assert service.saved == []
    assert view.errors


def test_update_preview_applies_schema_through_loader() -> None:
    """update_preview renders rows produced by the service loader."""
    # Arrange: a valid keyable schema and a couple of sample rows.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(view, service)
    sample = [
        {"Customer": "A", "SKU #": 1, "Type": "X", "Sales": 10.0},
        {"Customer": "B", "SKU #": 2, "Type": "Y", "Sales": 20.0},
    ]

    # Act
    rendered = presenter.update_preview(sample)

    # Assert: two preview rows were pushed to the view.
    assert rendered is True
    assert len(view.previews[-1]) == 2


def test_update_preview_surfaces_validation_error() -> None:
    """update_preview surfaces a structural error and renders no preview."""
    # Arrange: an empty key violates KeySpec; assembly must fail before loading.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    view.key = ((), False)
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    rendered = presenter.update_preview([{"Customer": "A"}])

    # Assert
    assert rendered is False
    assert view.errors
    assert view.previews == []


def test_validate_formula_accepts_valid_expression() -> None:
    """validate_formula accepts a valid expression and clears the error."""
    # Arrange: Sales is a known column, so a Sales-based formula is valid.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    valid = presenter.validate_formula("Sales * 2")

    # Assert
    assert valid is True
    assert view.clear_formula_calls >= 1
    assert view.formula_errors == []


@pytest.mark.parametrize(
    ("expression", "fragment"),
    [
        ("Sales * (", "syntax"),
        ("Sales.real", "disallowed construct"),
        ("Unknown_Column + 1", "unknown column"),
    ],
)
def test_validate_formula_rejects_bad_expressions(
    expression: str, fragment: str
) -> None:
    """validate_formula rejects bad expressions inline with a descriptive message.

    Covers a syntax error, a disallowed construct, and an unknown-column
    reference, each surfaced through ``show_formula_error``.
    """
    # Arrange
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    valid = presenter.validate_formula(expression)

    # Assert: rejected with a message that names the failure class.
    assert valid is False
    assert view.formula_errors
    assert fragment in view.formula_errors[-1].lower()


def test_load_existing_renders_schema_into_view() -> None:
    """load_existing pulls a schema from the service and renders every tab."""
    # Arrange: a service holding one schema under a known name.
    from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref

    schema = SchemaDefinition(
        name="stored",
        version="2.0",
        columns=(ColumnSpec(canonical_name="Customer", role="dimension"),),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
    )
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"stored": schema})
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    presenter.load_existing("stored")

    # Assert: identity and columns were rendered from the loaded schema.
    assert view.identity_set[-1] == ("stored", "2.0", "")
    assert view.columns_set[-1] == [("Customer", "dimension", True, True, ())]


def test_update_preview_surfaces_loader_error() -> None:
    """update_preview surfaces a loader error when the schema cannot load rows."""
    # Arrange: a valid keyable schema, but a sample row missing the KEY components
    # so the loader's column resolution fails with a ValueError.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(view, service)

    # Act: sample lacks the required SKU #/Type columns the schema declares.
    rendered = presenter.update_preview([{"Customer": "A"}])

    # Assert: load failed and the error surfaced; no preview rendered.
    assert rendered is False
    assert view.errors
    assert view.previews == []


def test_load_existing_renders_structured_key_and_dtypes() -> None:
    """load_existing renders ordered structured key parts and per-column dtypes."""
    # Arrange
    schema = stored_schema_with_structured_key_and_aggregate()
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"tmpl": schema})
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    presenter.load_existing("tmpl")

    # Assert: ordered structured key parts pushed to the view (including literal).
    assert view.key_parts_set[-1] == [
        ("column-ref", "Customer"),
        ("literal-text", "-"),
        ("column-ref", "SKU #"),
    ]
    # Per-column expected dtype pushed to the view in declared order.
    assert view.column_dtypes_set[-1] == [
        ("Customer", "string"),
        ("SKU #", None),
        ("Sales", None),
    ]
    # Aggregate dedup mode rendered.
    assert view.dedups_set[-1] == ("aggregate", "Customer")


def test_edit_load_modify_save_round_trips() -> None:
    """Edit flow: load an existing schema, modify it, and save it back."""
    # Arrange: load a stored schema, then set the view to return modified edits.
    schema = stored_schema_with_structured_key_and_aggregate()
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"tmpl": schema})
    presenter = SchemaBuilderPresenter(view, service)
    presenter.load_existing("tmpl")
    # The user changes the description; everything else mirrors the loaded state.
    view.identity = ("tmpl", "2.0", "edited description")
    view.columns = [
        ("Customer", "dimension", True, True, ("cust_col",)),
        ("SKU #", "dimension", True, True, ()),
        ("Sales", "measure", True, True, ()),
    ]
    view.key = (("Customer", "SKU #"), False)
    view.dedup = ("aggregate", "Customer")
    view.derived = []

    # Act
    saved = presenter.save()

    # Assert: the saved schema reflects the modification and aggregate mode.
    assert saved is True
    assert service.saved[-1].description == "edited description"
    assert service.saved[-1].dedup.mode == "aggregate"


def test_save_rejects_unknown_discriminator() -> None:
    """Decision 6: a discriminator that is not a declared column is rejected on save."""
    # Arrange: a valid keyable schema but an aggregate discriminator naming a
    # column the schema never declares.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    view.dedup = ("aggregate", "Nonexistent")
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    saved = presenter.save()

    # Assert: rejected by the model cross-reference; nothing persisted.
    assert saved is False
    assert service.saved == []
    assert view.errors


def test_add_derived_appends_row_in_order() -> None:
    """add_derived appends the derived column to the state in order (Decision 7)."""
    # Arrange
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    presenter = SchemaBuilderPresenter(view, service)

    # Act: add two derived columns in sequence.
    presenter.add_derived("Revenue", "Sales * Units")
    presenter.add_derived("Margin", "Revenue - Cost")

    # Assert: both appear in insertion order.
    assert presenter.state.derived == [
        ("Revenue", "Sales * Units"),
        ("Margin", "Revenue - Cost"),
    ]
    # The view received the re-rendered derived rows.
    assert view.deriveds_set[-1] == [
        ("Revenue", "Sales * Units"),
        ("Margin", "Revenue - Cost"),
    ]


def test_injected_evaluator_is_used() -> None:
    """An injected FormulaEvaluator is used for formula validation."""
    # Arrange: inject the default evaluator explicitly to cover that branch.
    from src.schema_formula import FormulaEvaluator

    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(
        view, service, formula_evaluator=FormulaEvaluator()
    )

    # Act
    valid = presenter.validate_formula("Sales + 1")

    # Assert
    assert valid is True
