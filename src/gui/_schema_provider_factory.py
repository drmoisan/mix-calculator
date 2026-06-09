"""Production :class:`BuildSpecProvider` construction for the composition root.

This factory builds the per-source build-spec provider the per-tab "Build/Edit
schema" button uses to seed the schema builder (Decision 7). It is extracted from
:mod:`src.gui.app` so the composition root stays under the repository's 500-line
cap once the provider is wired.

The provider maps each source key (``"LE"``, ``"aop"``, ``"sku_lu"``) to a
:class:`~src.gui._schema_build_specs.CallerBuildSpec` carrying that source's
required and optional column specs, a default key pattern rendered from the
source schema's structured key, and a confidentiality-masked preview slice
(Decision 5) the builder reads for the draggable token pool and the dtype check.

Responsibilities:
    - ``build_spec_provider``: build the production provider from the schema
      service and a key-to-schema-name mapping.

Scope boundaries:
    - No Qt import. It reads schemas through the injected service and assembles
      pure value objects; the preview slice contains only synthetic/masked content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_build_specs import BuildSpecProvider, CallerBuildSpec
from src.gui.presenters._schema_builder_state import PreviewSlice

if TYPE_CHECKING:
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.schema_model import ColumnSpec, SchemaDefinition

__all__ = [
    "DEFAULT_SOURCE_SCHEMA_NAMES",
    "build_spec_provider",
]

# The bundled default schema each source key seeds its builder from. Each source
# now ships a bundled default (issue #60 Defect 2 added ``default_sku_lu``), so
# the registry auto-discovers all three and the per-tab Build button seeds from them.
DEFAULT_SOURCE_SCHEMA_NAMES: dict[str, str | None] = {
    "LE": "default_le",
    "aop": "default_aop",
    "sku_lu": "default_sku_lu",
}

# A small number of synthetic masked sample rows per preview slice. The values are
# deliberately non-proprietary placeholders so no real workbook content is bundled.
_MASKED_SAMPLE_ROWS = 3


class _SchemaBuildSpecProvider:
    """Map a source key to its :class:`CallerBuildSpec` from the schema service.

    Purpose:
        Implement :class:`~src.gui._schema_build_specs.BuildSpecProvider` for the
        composition root: resolve each source key to its bundled default schema and
        assemble the required/optional specs, default key pattern, and masked
        preview slice the per-tab build button seeds the builder with (Decision 7).

    Responsibilities:
        Load the per-key schema via the service, split its columns into required and
        optional specs, render its structured key into a default pattern, and build
        a synthetic masked preview slice. It performs no Qt work and bundles no real
        workbook content.

    Usage:
        Built by :func:`build_spec_provider` at the composition root and passed to
        :func:`src.gui._schema_wiring.wire_build_schema_buttons`.

    Attributes:
        _service: The schema service used to load each source's schema.
        _schema_names: Mapping of source key to its schema name (or ``None``).
    """

    def __init__(
        self,
        service: SchemaServiceProtocol,
        schema_names: dict[str, str | None],
    ) -> None:
        """Initialize the provider with its service and key-to-schema mapping.

        Args:
            service: The schema service used to load per-source schemas.
            schema_names: Mapping of source key to the schema name to seed from, or
                ``None`` for a source without a bundled default.
        """
        self._service = service
        self._schema_names = schema_names

    def build_spec_for(self, key: str) -> CallerBuildSpec:
        """Return the build spec for one source key.

        Resolves the source key to its bundled schema name; when a name is mapped
        and loadable, splits the schema's columns into required/optional specs,
        renders its default key pattern, and builds a masked preview slice. An
        unmapped key (or a missing schema) yields an empty spec so the builder opens
        blank for that source.

        Args:
            key: The source key (``"LE"``, ``"aop"``, or ``"sku_lu"``).

        Returns:
            The :class:`CallerBuildSpec` for ``key``.
        """
        name = self._schema_names.get(key)
        # An unmapped source (for example sku_lu with no bundled default) opens a
        # blank builder rather than failing the per-tab open path.
        if name is None:
            return CallerBuildSpec()
        # A name that no longer resolves (deleted/renamed schema) also degrades to a
        # blank spec rather than raising in the GUI open path.
        try:
            schema = self._service.load_schema(name)
        except (KeyError, ValueError, FileNotFoundError):
            return CallerBuildSpec()
        return _spec_from_schema(schema)


def build_spec_provider(
    service: SchemaServiceProtocol,
    *,
    schema_names: dict[str, str | None] | None = None,
) -> BuildSpecProvider:
    """Build the production per-source build-spec provider.

    Args:
        service: The schema service the provider loads source schemas through.
        schema_names: Optional override of the key-to-schema-name mapping; defaults
            to :data:`DEFAULT_SOURCE_SCHEMA_NAMES`.

    Returns:
        A :class:`BuildSpecProvider` resolving each source key to its build spec.
    """
    return _SchemaBuildSpecProvider(
        service, schema_names or dict(DEFAULT_SOURCE_SCHEMA_NAMES)
    )


def _spec_from_schema(schema: SchemaDefinition) -> CallerBuildSpec:
    """Assemble a :class:`CallerBuildSpec` from a loaded schema.

    Args:
        schema: The loaded source schema.

    Returns:
        A :class:`CallerBuildSpec` carrying the schema's required/optional specs,
        rendered default key pattern, and a synthetic masked preview slice.
    """
    # Split columns into required and optional, preserving declared order so the
    # Columns tab lists required columns ahead of optional ones.
    required = tuple(column for column in schema.columns if column.required)
    optional = tuple(column for column in schema.columns if not column.required)
    return CallerBuildSpec(
        required_specs=required,
        optional_specs=optional,
        default_key_pattern=_render_key_pattern(schema),
        preview_slice=_masked_preview_slice(schema.columns),
    )


def _render_key_pattern(schema: SchemaDefinition) -> str | None:
    """Render a schema's structured key into a ``{column}`` default key pattern.

    Args:
        schema: The schema whose key is rendered.

    Returns:
        A pattern string where each column-ref part is ``{name}`` and each
        literal-text part is its verbatim value, in order; ``None`` when the key has
        no parts.
    """
    parts = schema.key.parts
    if not parts:
        return None
    # Render each part in order: column-ref parts as {name} tokens, literal-text
    # parts verbatim, so parse_key_pattern reconstructs the same composition.
    rendered = [
        f"{{{part.value}}}" if part.is_column_ref else part.value for part in parts
    ]
    return "".join(rendered)


def _masked_preview_slice(columns: tuple[ColumnSpec, ...]) -> PreviewSlice:
    """Build a synthetic masked preview slice from a schema's columns.

    The header is the schema's canonical column names; the rows are synthetic masked
    placeholders so the draggable token pool and dtype check have content without
    bundling any real workbook values (Decision 5).

    Args:
        columns: The schema's column specs, in declared order.

    Returns:
        A :class:`PreviewSlice` with the canonical names as the header and a few
        masked placeholder rows.
    """
    header = tuple(column.canonical_name for column in columns)
    # Build a handful of synthetic rows; each cell is a masked placeholder keyed to
    # its column index and row number so values are obviously non-proprietary.
    rows = tuple(
        tuple(f"masked_{col_index}_{row_index}" for col_index in range(len(header)))
        for row_index in range(_MASKED_SAMPLE_ROWS)
    )
    return PreviewSlice(header=header, rows=rows)
