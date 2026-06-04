"""Composition-root wiring for populating each source tab's schema dropdown.

This helper fills each source tab's import-schema dropdown with the schema names
available from the schema service at application startup, so the bundled default
schemas (and any user-saved schemas) are selectable from the per-tab combo (WS2,
issue #48, R-AC-3). It lives in its own module so ``app.py`` stays under the
repository's 500-line file cap (per ``.claude/rules/general-code-change.md``),
following the ``_run_wiring.py`` / ``_schema_wiring.py`` precedent.

Responsibilities:
    - ``populate_schema_lists``: call ``set_schema_list`` on each source view with
      the service's available schema names.

The module performs view population only; it holds no domain, matching, or
transform logic. Schema enumeration flows through the injected service, which
delegates to the union-aware registry seam.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.gui.protocols import SourceSelectionViewProtocol
    from src.gui.services.schema_service import SchemaServiceProtocol

__all__ = ["populate_schema_lists"]


def populate_schema_lists(
    views: Sequence[SourceSelectionViewProtocol],
    service: SchemaServiceProtocol,
) -> None:
    """Populate each source view's schema dropdown with the available names.

    Calls :meth:`SourceSelectionViewProtocol.set_schema_list` on every supplied
    view with the names returned by
    :meth:`SchemaServiceProtocol.list_schema_names`, so each per-tab dropdown
    offers the available schemas (including the bundled defaults) at startup. The
    service is queried once and the same name list is applied to every view to
    keep the dropdowns consistent.

    Args:
        views: The source-selection views whose schema dropdowns are populated,
            in any order (typically the LE, AOP, and SKU-LU source widgets).
        service: The schema service that enumerates the available schema names.

    Returns:
        ``None``.

    Side effects:
        Updates each view's schema dropdown via ``set_schema_list``.
    """
    # Query the available names once so every tab's dropdown is populated from the
    # same list, keeping the per-tab combos consistent at startup.
    names = service.list_schema_names()
    # Apply the same name list to each source view's dropdown so all source tabs
    # offer the available schemas (including the bundled defaults).
    for view in views:
        view.set_schema_list(names)
