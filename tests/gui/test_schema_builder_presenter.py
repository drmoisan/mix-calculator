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

from typing import TYPE_CHECKING

import pytest

from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
from tests.gui.fakes.fake_services import FakeSchemaService
from tests.gui.fakes.fake_views import FakeSchemaBuilderView

if TYPE_CHECKING:
    from src.schema_model import SchemaDefinition


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


def _stored_schema_with_structured_key_and_aggregate() -> SchemaDefinition:
    """Return a schema with structured key parts, an alias, and aggregate dedup.

    Returns:
        A :class:`SchemaDefinition` whose key interleaves a literal-text part,
        whose ``Customer`` column carries a persisted alias, an ``expected_dtype``,
        and whose dedup mode is ``aggregate`` discriminated by the Key.
    """
    from src.schema_model import (
        ColumnSpec,
        DedupPolicy,
        KeySpec,
        SchemaDefinition,
        column_ref,
        literal_text,
    )

    return SchemaDefinition(
        name="tmpl",
        version="2.0",
        columns=(
            ColumnSpec(
                canonical_name="Customer",
                role="dimension",
                aliases=("cust_col",),
                expected_dtype="string",
            ),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(
            parts=(
                column_ref("Customer"),
                literal_text("-"),
                column_ref("SKU #"),
            )
        ),
        dedup=DedupPolicy(mode="aggregate", discriminator_column="Customer"),
    )


def test_load_existing_renders_structured_key_and_dtypes() -> None:
    """load_existing renders ordered structured key parts and per-column dtypes."""
    # Arrange
    schema = _stored_schema_with_structured_key_and_aggregate()
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
    schema = _stored_schema_with_structured_key_and_aggregate()
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"tmpl": schema})
    presenter = SchemaBuilderPresenter(view, service)
    presenter.load_existing("tmpl")
    # The user changes the description; everything else mirrors the loaded state.
    view.identity = ("tmpl", "2.0", "edited description")
    view.columns = [
        ("Customer", "dimension", True, ("cust_col",)),
        ("SKU #", "dimension", True, ()),
        ("Sales", "measure", True, ()),
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
    _configure_valid_keyable_view(view)
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


def test_new_from_template_seeds_clears_name() -> None:
    """new_from_template mirrors the template but clears the name for save-as."""
    # Arrange
    schema = _stored_schema_with_structured_key_and_aggregate()
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"tmpl": schema})
    presenter = SchemaBuilderPresenter(view, service)

    # Act
    presenter.new_from_template("tmpl")

    # Assert: name is cleared (awaiting save-as) but the specs/key/dedup mirror it.
    assert presenter.state.name == ""
    assert presenter.state.column_dtypes["Customer"] == "string"
    assert presenter.state.dedup_mode == "aggregate"
    assert [(p.kind, p.value) for p in presenter.state.key_parts] == [
        ("column-ref", "Customer"),
        ("literal-text", "-"),
        ("column-ref", "SKU #"),
    ]
    # The template column's persisted alias is carried into the new state.
    assert presenter.state.columns[0][3] == ("cust_col",)


def test_new_from_template_save_as_does_not_overwrite_template() -> None:
    """save-as for a new-from-template schema writes a distinct file."""
    # Arrange: seed from the template, then save under a new name.
    schema = _stored_schema_with_structured_key_and_aggregate()
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"tmpl": schema})
    presenter = SchemaBuilderPresenter(view, service)
    presenter.new_from_template("tmpl")
    # The user names the new schema and saves; the view returns the new name.
    view.identity = ("tmpl_variant", "2.0", "")
    view.columns = [
        ("Customer", "dimension", True, ("cust_col",)),
        ("SKU #", "dimension", True, ()),
        ("Sales", "measure", True, ()),
    ]
    view.key = (("Customer", "SKU #"), False)
    view.dedup = ("aggregate", "Customer")
    view.derived = []

    # Act
    saved = presenter.save()

    # Assert: the saved name differs from the template name (no overwrite).
    assert saved is True
    assert service.saved[-1].name == "tmpl_variant"
    assert service.saved[-1].name != "tmpl"


def test_seed_from_caller_pre_lists_rows_and_parses_key() -> None:
    """seed_from_caller pre-lists required+optional rows and parses the key pattern."""
    # Arrange: caller specs for a source and a default key pattern with a literal.
    from src.schema_model import ColumnSpec

    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    presenter = SchemaBuilderPresenter(view, service)
    required = [
        ColumnSpec(canonical_name="Customer", role="dimension"),
        ColumnSpec(canonical_name="SKU #", role="dimension"),
    ]
    optional = [ColumnSpec(canonical_name="Region", role="dimension", required=False)]

    # Act
    presenter.seed_from_caller(
        required_specs=required,
        optional_specs=optional,
        default_key_pattern="{Customer}-{SKU #}",
    )

    # Assert: required rows precede optional rows in the seeded state.
    names = [row[0] for row in presenter.state.columns]
    assert names == ["Customer", "SKU #", "Region"]
    # The key pattern parsed into ordered parts: column, literal "-", column.
    parts = presenter.state.key_parts
    assert [(p.kind, p.value) for p in parts] == [
        ("column-ref", "Customer"),
        ("literal-text", "-"),
        ("column-ref", "SKU #"),
    ]


def test_seed_from_caller_blank_menu_path_leaves_state_empty() -> None:
    """seed_from_caller with no inputs leaves the state blank (menu path)."""
    # Arrange
    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    presenter = SchemaBuilderPresenter(view, service)

    # Act: the menu path seeds with nothing.
    presenter.seed_from_caller()

    # Assert: no columns, no key parts, no preview slice.
    assert presenter.state.columns == []
    assert presenter.state.key_parts == []
    assert presenter.state.preview_slice is None


def test_seed_from_caller_reads_preview_slice_without_io() -> None:
    """seed_from_caller reads the masked preview slice without invoking any reader.

    The presenter must not perform I/O inside the builder (Decision 5); it reads
    only the supplied slice. The fake service exposes no reader/load API the
    seeding path could call, so a successful seed that populates the source-column
    pool from the slice header verifies the no-I/O contract.
    """
    # Arrange: a masked preview slice with synthetic header and rows.
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.schema_model import ColumnSpec

    view = FakeSchemaBuilderView()
    service = FakeSchemaService()
    presenter = SchemaBuilderPresenter(view, service)
    preview = PreviewSlice(
        header=("col_a", "col_b"),
        rows=(("x1", "y1"), ("x2", "y2")),
    )

    # Act
    presenter.seed_from_caller(
        required_specs=[ColumnSpec(canonical_name="Customer", role="dimension")],
        preview_slice=preview,
    )

    # Assert: the source-column pool came from the slice header; the slice is held.
    assert presenter.state.source_columns == ["col_a", "col_b"]
    assert presenter.state.preview_slice is preview
    # The slice value accessor reads sampled values purely (no reader calls).
    assert preview.column_values("col_a") == ["x1", "x2"]


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
