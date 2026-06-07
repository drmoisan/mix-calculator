"""Shared fixtures for the SchemaBuilderPresenter test split (Feature D, AC4 + AC5).

This module holds the two helpers shared by the schema-builder presenter test
modules: a fake-view configurator that produces a valid, loader-ready schema, and
a builder for a stored schema with structured key parts, a persisted alias, and
aggregate dedup. Both helpers are imported by
``test_schema_builder_presenter_core`` and ``test_schema_builder_presenter_seeding``
so the split modules stay independent while reusing identical setup. The helpers
perform no I/O and no ``QApplication`` work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schema_model import SchemaDefinition
    from tests.gui.fakes.fake_views import FakeSchemaBuilderView


def configure_valid_keyable_view(view: FakeSchemaBuilderView) -> None:
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
        ("Customer", "dimension", True, True, ()),
        ("SKU #", "dimension", True, True, ()),
        ("Type", "dimension", True, True, ()),
        ("Sales", "measure", True, True, ()),
    ]
    view.key = (("Customer", "SKU #", "Type"), False)
    view.dedup = ("none", None)
    view.derived = []


def stored_schema_with_structured_key_and_aggregate() -> SchemaDefinition:
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
