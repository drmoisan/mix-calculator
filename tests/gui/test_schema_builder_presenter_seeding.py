"""Seeding / new-from-template tests for :class:`SchemaBuilderPresenter`.

These tests exercise the presenter's seeding entry points (Feature D) with a fake
view and a fake schema service, with no ``QApplication`` and no disk/network. They
verify new-from-template save-as semantics (mirror the template, clear the name,
write a distinct file) and ``seed_from_caller`` behavior (pre-list required and
optional rows, parse a default key pattern, leave the state blank on the menu
path, and read a masked preview slice without performing any I/O).

Core presenter state / edit-load / preview / formula tests live in
``test_schema_builder_presenter_core``; the two shared helpers live in
``tests.gui._schema_builder_presenter_fixtures``.
"""

from __future__ import annotations

from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
from tests.gui._schema_builder_presenter_fixtures import (
    stored_schema_with_structured_key_and_aggregate,
)
from tests.gui.fakes.fake_services import FakeSchemaService
from tests.gui.fakes.fake_views import FakeSchemaBuilderView


def test_new_from_template_seeds_clears_name() -> None:
    """new_from_template mirrors the template but clears the name for save-as."""
    # Arrange
    schema = stored_schema_with_structured_key_and_aggregate()
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
    assert presenter.state.columns[0][4] == ("cust_col",)


def test_new_from_template_save_as_does_not_overwrite_template() -> None:
    """save-as for a new-from-template schema writes a distinct file."""
    # Arrange: seed from the template, then save under a new name.
    schema = stored_schema_with_structured_key_and_aggregate()
    view = FakeSchemaBuilderView()
    service = FakeSchemaService(schemas={"tmpl": schema})
    presenter = SchemaBuilderPresenter(view, service)
    presenter.new_from_template("tmpl")
    # The user names the new schema and saves; the view returns the new name.
    view.identity = ("tmpl_variant", "2.0", "")
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
