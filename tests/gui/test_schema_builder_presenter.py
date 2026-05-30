"""Unit tests for :class:`SchemaBuilderPresenter` (Feature D, AC4 + AC5).

These tests exercise the schema-builder presenter with a fake view and a fake
schema service, with no ``QApplication`` and no disk/network. They verify that
the presenter assembles a valid schema from the view's edits and saves it,
renders a preview by applying the in-progress schema through the service loader,
validates runtime formula entry through Feature C (accepting valid expressions,
rejecting syntax errors, disallowed constructs, and unknown columns inline), and
surfaces a model :class:`~src.schema_model.SchemaValidationError` as an error.
"""

from __future__ import annotations

import pytest

from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
from tests.gui.fakes.fake_services import FakeSchemaService
from tests.gui.fakes.fake_views import FakeSchemaBuilderView


def _configure_valid_keyable_view(view: FakeSchemaBuilderView) -> None:
    """Populate a fake builder view with a valid, loader-ready schema.

    The columns include the KEY components (``Customer``, ``SKU #``, ``Type``)
    the schema loader rebuilds the key from, plus a numeric ``Sales`` measure.

    Args:
        view: The fake view to configure.

    Returns:
        ``None``.
    """
    view.identity = ("keyable", "1.0", "test schema")
    view.columns = [
        ("Customer", "dimension", True, ()),
        ("SKU #", "dimension", True, ()),
        ("Type", "dimension", True, ()),
        ("Sales", "measure", True, ()),
    ]
    view.key = (("Customer", "SKU #", "Type"), False)
    view.dedup = ("none", None)
    view.derived = []


def test_save_assembles_and_persists_valid_schema() -> None:
    """save assembles a valid schema from the view and persists it."""
    # Arrange
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    _configure_valid_keyable_view(view)
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
    _configure_valid_keyable_view(view)
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
    _configure_valid_keyable_view(view)
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
    _configure_valid_keyable_view(view)
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
    _configure_valid_keyable_view(view)
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
    _configure_valid_keyable_view(view)
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
    from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition

    schema = SchemaDefinition(
        name="stored",
        version="2.0",
        columns=(ColumnSpec(canonical_name="Customer", role="dimension"),),
        key=KeySpec(columns=("Customer",)),
    )
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"stored": schema})
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    presenter.load_existing("stored")

    # Assert: identity and columns were rendered from the loaded schema.
    assert view.identity_set[-1] == ("stored", "2.0", "")
    assert view.columns_set[-1] == [("Customer", "dimension", True, ())]


def test_update_preview_surfaces_loader_error() -> None:
    """update_preview surfaces a loader error when the schema cannot load rows."""
    # Arrange: a valid keyable schema, but a sample row missing the KEY components
    # so the loader's column resolution fails with a ValueError.
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    _configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(view, service)

    # Act: sample lacks the required SKU #/Type columns the schema declares.
    rendered = presenter.update_preview([{"Customer": "A"}])

    # Assert: load failed and the error surfaced; no preview rendered.
    assert rendered is False
    assert view.errors
    assert view.previews == []


def test_injected_evaluator_is_used() -> None:
    """An injected FormulaEvaluator is used for formula validation."""
    # Arrange: inject the default evaluator explicitly to cover that branch.
    from src.schema_formula import FormulaEvaluator

    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    _configure_valid_keyable_view(view)
    presenter = SchemaBuilderPresenter(
        view, service, formula_evaluator=FormulaEvaluator()
    )

    # Act
    valid = presenter.validate_formula("Sales + 1")

    # Assert
    assert valid is True
