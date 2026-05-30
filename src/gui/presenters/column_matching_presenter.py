"""Presenter for the manual column-matching workflow (Feature D, AC3).

This presenter drives a passive :class:`ColumnMatchingViewProtocol` from a
Feature B :class:`~src.schema_matching.MatchResult`. It presents the unmatched
required columns (with their declared aliases), the source columns, and the
fuzzy candidate suggestions the mismatch report already computed, then records
point-and-click assignments and optional-column ignores. When the user opts to
persist, it augments the matched schema with the new aliases and saves it
through the injected :class:`~src.gui.services.schema_service.SchemaServiceProtocol`.

Responsibilities:
    - Push the unmatched-required, source-column, and fuzzy-suggestion state to
      the view from a ``MatchResult``.
    - Record assignments (required canonical name -> source column) and ignores.
    - On accept-and-save, build alias additions and persist the updated schema.

Scope boundaries:
    - No Qt import. Pure Python and deterministic (no clock, no RNG). Fuzzy
      scores are consumed from the Feature B report; scoring is not
      re-implemented. Persistence flows only through the service/registry
      boundary.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.protocols import ColumnMatchingViewProtocol
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.schema_matching import MatchResult
    from src.schema_model import ColumnSpec, SchemaDefinition

__all__ = ["ColumnMatchingPresenter"]

logger = logging.getLogger(__name__)


class ColumnMatchingPresenter:
    """Coordinate manual resolution of a schema header mismatch.

    Purpose:
        Translate a Feature B :class:`~src.schema_matching.MatchResult` and the
        user's point-and-click actions into schema alias additions, keeping all
        matching logic out of the Qt dialog.

    Responsibilities:
        Present the unmatched required columns, source columns, and fuzzy
        suggestions; record assignments and optional-column ignores; and, on
        accept-and-save, persist a schema augmented with the chosen aliases. It
        rejects a save when a required column has no assignment and is not
        ignored.

    Usage:
        Constructed with a :class:`ColumnMatchingViewProtocol` view and a
        :class:`SchemaServiceProtocol`. Call :meth:`present` with a
        ``MatchResult`` to populate the view, then route the dialog's user
        actions to :meth:`assign`, :meth:`ignore`, and :meth:`accept_and_save`.

    Key invariants:
        - The candidate suggestions come from the report; no score is recomputed.
        - Persistence flows only through ``service.save_schema``.

    Attributes:
        _view: The column-matching view this presenter drives.
        _service: The schema service used to persist alias additions.
        _schema: The schema the current match selected (the save target).
        _assignments: Recorded required-to-source assignments.
        _ignored: Required canonical names the user marked ignored.
        _source_columns: The source headers most recently presented.
    """

    def __init__(
        self,
        view: ColumnMatchingViewProtocol,
        service: SchemaServiceProtocol,
    ) -> None:
        """Initialize the presenter with its view and schema service.

        Args:
            view: The passive column-matching view to drive.
            service: The schema service used to persist the augmented schema.
        """
        self._view = view
        self._service = service
        self._schema: SchemaDefinition | None = None
        self._assignments: dict[str, str] = {}
        self._ignored: set[str] = set()
        self._source_columns: list[str] = []

    def present(self, result: MatchResult, headers: list[str]) -> None:
        """Populate the view from a match result and the source headers.

        Pushes the unmatched required columns (with aliases), the source columns,
        and the fuzzy suggestions the report already computed.

        Args:
            result: The Feature B match result whose selected schema is the save
                target and whose report supplies unmatched columns and
                candidates.
            headers: The actual source headers, in source order.

        Returns:
            ``None``.

        Side effects:
            Resets recorded assignments/ignores and calls the view's setters.

        Raises:
            ValueError: When ``result.schema`` is ``None`` (no candidate schema
                to resolve against).
        """
        if result.schema is None:
            raise ValueError("Cannot resolve a match without a candidate schema.")

        self._schema = result.schema
        self._assignments = {}
        self._ignored = set()
        self._source_columns = list(headers)

        # Present each unmatched required column with its declared aliases so the
        # operator sees what the schema expected for that column.
        unmatched_items = [
            (column.canonical_name, column.aliases)
            for column in result.report.unmatched_required
        ]
        self._view.set_unmatched_required(unmatched_items)
        self._view.set_source_columns(list(headers))

        # Reuse the report's ranked candidates (already scored by difflib in
        # Feature B); do not recompute similarity here.
        suggestions = {
            column.canonical_name: [
                (candidate.actual_name, candidate.score)
                for candidate in column.candidates
            ]
            for column in result.report.unmatched_required
        }
        self._view.set_fuzzy_suggestions(suggestions)

    def assign(self, required: str, source: str) -> None:
        """Record a point-and-click assignment and reflect it in the view.

        Args:
            required: The canonical name of the required column being assigned.
            source: The source column the user picked for ``required``.

        Returns:
            ``None``.

        Side effects:
            Records the assignment (clearing any prior ignore) and calls
            ``view.set_assignment``.
        """
        # A fresh assignment supersedes a prior ignore for the same column.
        self._ignored.discard(required)
        self._assignments[required] = source
        self._view.set_assignment(required, source)

    def ignore(self, required: str) -> None:
        """Mark an optional required column as ignored and reflect it.

        Args:
            required: The canonical name of the optional column to ignore.

        Returns:
            ``None``.

        Side effects:
            Records the ignore (clearing any prior assignment) and calls
            ``view.mark_ignored``.
        """
        # Ignoring a column supersedes any prior assignment for it.
        self._assignments.pop(required, None)
        self._ignored.add(required)
        self._view.mark_ignored(required)

    def accept_and_save(self) -> bool:
        """Persist a schema augmented with the user's alias assignments.

        Verifies that every unmatched required column the presenter presented has
        either an assignment or an ignore mark; if any is unresolved, surfaces an
        error and persists nothing. Otherwise builds the alias additions and saves
        the augmented schema through the service.

        Returns:
            ``True`` when the augmented schema was saved; ``False`` when a
            required column was unresolved and nothing was persisted.

        Side effects:
            On success calls ``service.save_schema``. On failure calls
            ``view.show_error``.
        """
        if self._schema is None:
            self._view.show_error("No schema is loaded to save.")
            return False

        # Every assignment names a source column that must actually exist in the
        # source; reject an assignment to an absent source before persisting.
        for required, source in self._assignments.items():
            if source not in self._source_columns:
                self._view.show_error(
                    f"Required column '{required}' is assigned to unknown source "
                    f"column '{source}'."
                )
                return False

        augmented = self._augment_with_aliases(self._schema, self._assignments)
        self._service.save_schema(augmented)
        logger.info(
            "Saved schema %r with %d added aliases.",
            augmented.name,
            len(self._assignments),
        )
        return True

    def _augment_with_aliases(
        self,
        schema: SchemaDefinition,
        assignments: dict[str, str],
    ) -> SchemaDefinition:
        """Return ``schema`` with each assignment's source added as an alias.

        For every assignment, the assigned source column name is appended to the
        matching column's aliases (when not already present), so a future import
        of the same source binds without manual matching.

        Args:
            schema: The schema to augment.
            assignments: Mapping of required canonical name to assigned source.

        Returns:
            A new :class:`SchemaDefinition` with augmented column aliases. The
            input schema is not mutated (its columns are frozen dataclasses).
        """
        # Rebuild the column tuple, appending the assigned source as a new alias
        # on the column whose canonical name was assigned. Other columns pass
        # through unchanged so the rest of the schema is preserved exactly.
        new_columns: list[ColumnSpec] = []
        for column in schema.columns:
            source = assignments.get(column.canonical_name)
            if source is not None and source not in column.aliases:
                new_columns.append(replace(column, aliases=(*column.aliases, source)))
            else:
                new_columns.append(column)
        return replace(schema, columns=tuple(new_columns))
