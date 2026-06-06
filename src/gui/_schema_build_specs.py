"""Per-tab caller-spec assembly for the schema builder open path.

This helper carries the source-specific inputs the per-tab "Build/Edit schema"
button supplies when opening the schema builder (Decision 7): the required and
optional column specs, the default key pattern, and the masked preview slice for
the active source. Keeping the spec bundle and the provider contract here keeps
:mod:`src.gui._schema_wiring` under the repository's 500-line cap.

Responsibilities:
    - ``CallerBuildSpec``: a pure value object bundling the four caller inputs.
    - ``BuildSpecProvider``: the protocol the composition root implements to map
      a source key (``"LE"``, ``"aop"``, ``"sku_lu"``) to its build spec.

Scope boundaries:
    - Pure data plus a provider contract. No Qt import, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.schema_model import ColumnSpec

__all__ = [
    "BuildSpecProvider",
    "CallerBuildSpec",
]


@dataclass(frozen=True)
class CallerBuildSpec:
    """The per-source inputs the per-tab build button supplies to the builder.

    Purpose:
        Bundle the source-specific required/optional specs, default key pattern,
        and masked preview slice so the wiring can seed the schema-builder
        presenter from one value rather than four loose parameters (Decision 7).

    Attributes:
        required_specs: The source's required column specs, in display order.
        optional_specs: The source's optional column specs, in display order.
        default_key_pattern: The source's default key pattern string parsed into
            structured key parts by the presenter, or ``None`` when none.
        preview_slice: The masked preview slice the builder reads for the
            draggable token pool and the dtype check, or ``None`` when none.

    Constraints:
        The ``preview_slice`` must contain only synthetic/masked content; no real
        workbook values or proprietary source column names.
    """

    required_specs: tuple[ColumnSpec, ...] = ()
    optional_specs: tuple[ColumnSpec, ...] = ()
    default_key_pattern: str | None = None
    preview_slice: PreviewSlice | None = field(default=None)


@runtime_checkable
class BuildSpecProvider(Protocol):
    """Contract mapping a source key to its per-tab :class:`CallerBuildSpec`.

    Purpose:
        Let the composition root supply, per source key, the required/optional
        specs and masked preview slice the per-tab build button passes to the
        builder, without the wiring module importing the concrete source widgets.

    Responsibilities:
        Return the :class:`CallerBuildSpec` for a given source key. It performs no
        side effects; it only assembles the source-specific spec bundle.

    Usage:
        The composition root implements this (or supplies a callable equivalent)
        and passes it to :func:`src.gui._schema_wiring.wire_build_schema_buttons`.
    """

    def build_spec_for(self, key: str) -> CallerBuildSpec:
        """Return the build spec for one source key.

        Args:
            key: The source key (``"LE"``, ``"aop"``, or ``"sku_lu"``).

        Returns:
            The :class:`CallerBuildSpec` carrying that source's required/optional
            specs, default key pattern, and masked preview slice.
        """
        ...
