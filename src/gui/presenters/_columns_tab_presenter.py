"""Presenter for the Columns-tab drag-and-drop redesign (Decision 4/6).

This presenter drives a passive :class:`ColumnsTabViewProtocol`. It pre-populates
each required/optional canonical row with its best fuzzy source-column match from
the masked preview slice, persists each match onto the column's
:class:`~src.schema_model.ColumnSpec` aliases (so the mapping survives save/reload,
Decision 6), tracks consumed source columns so one source cannot match two rows,
supports manual re-assignment through the ``assign_column`` seam, and orchestrates
the pure dtype check against the masked preview slice for each matched column.

Responsibilities:
    - ``prepopulate``: fuzzy-match each row to the closest source column, consume
      it, persist the alias, and run the dtype check.
    - ``assign_column``: handle a manual drop, releasing any prior assignment.
    - ``clear_row``: release a row's source back into the pool.

Scope boundaries:
    - No Qt import. Fuzzy matching reuses Feature B helpers; the dtype check reuses
      :mod:`src.dtype_check`. The presenter performs no I/O; it reads only the
      masked preview slice held on the state.
"""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from src.dtype_check import check_dtype
from src.etl_columns import normalize_name

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui._columns_tab_protocol import ColumnsTabViewProtocol
    from src.gui.presenters._schema_builder_state import SchemaBuilderState

__all__ = ["ColumnsTabPresenter"]

# Minimum normalized similarity for a fuzzy pre-population bind. A row whose best
# source candidate scores below this is left unassigned for the user to resolve.
_PREPOPULATE_THRESHOLD = 0.6


class ColumnsTabPresenter:
    """Coordinate fuzzy pre-population, alias persistence, and the dtype check.

    Purpose:
        Drive the Columns tab: match each canonical row to the closest source
        column, persist the mapping as a column alias, keep the source-column pool
        and consumed set consistent, and push the per-row dtype pass/fail state to
        the view.

    Responsibilities:
        Pre-populate rows by fuzzy match; persist matches onto column aliases;
        consume matched source columns (one source per row); support manual
        reassignment and clearing through the assignment seam; run the pure dtype
        check on the masked preview slice. It imports no Qt and performs no I/O.

    Usage:
        Construct with a :class:`ColumnsTabViewProtocol` view and the shared
        :class:`SchemaBuilderState`. Call :meth:`prepopulate` on open; route the
        view's ``assign_column`` drops to :meth:`assign_column`.

    Attributes:
        _view: The Columns-tab view this presenter drives.
        _state: The shared in-progress builder state (columns, pool, consumed,
            preview slice, dtypes).
    """

    def __init__(self, view: ColumnsTabViewProtocol, state: SchemaBuilderState) -> None:
        """Initialize the presenter with its view and shared state.

        Args:
            view: The passive Columns-tab view to drive.
            state: The shared in-progress builder state.
        """
        self._view = view
        self._state = state

    def prepopulate(self) -> None:
        """Fuzzy-match each row to the closest source column and render the tab.

        For each canonical row, finds the best-scoring unconsumed source column
        (by normalized similarity). When the best score clears the bind threshold,
        the source is consumed, persisted onto the column's aliases (Decision 6),
        and the dtype check runs against the masked preview slice. Rows whose best
        candidate scores too low are left unassigned. Renders the pool and rows.

        Returns:
            ``None``.

        Side effects:
            Mutates the state's ``source_columns`` pool, ``consumed_columns`` map,
            and column aliases; pushes the pool, rows, assignments, and dtype
            indicators to the view.
        """
        # Match required columns first (they appear first in the column rows), so
        # the most important rows claim their best source before optional rows.
        for canonical, _role, _required, _in_output, _aliases in list(
            self._state.columns
        ):
            best = self._best_unconsumed_match(canonical)
            if best is not None:
                self._bind(canonical, best)
        self._render()

    def assign_column(self, source_column: str, target_canonical: str) -> None:
        """Handle a manual drop of ``source_column`` onto ``target_canonical``.

        Releases any source previously assigned to the target and any prior
        assignment of the dropped source (a source is single-use), then binds the
        new pairing, persists the alias, runs the dtype check, and re-renders.

        Args:
            source_column: The dragged source column name.
            target_canonical: The canonical row the source was dropped onto.

        Returns:
            ``None``.

        Side effects:
            Updates the pool, consumed map, and aliases; re-renders the tab.
        """
        # Free the target's current source (if any) so it returns to the pool.
        self._release_target(target_canonical)
        # A source is single-use: if it was consumed by another row, release that
        # row first so the drop does not duplicate the source across two rows.
        self._release_source(source_column)
        self._bind(target_canonical, source_column)
        self._render()

    def clear_row(self, target_canonical: str) -> None:
        """Release a row's assigned source column back into the pool.

        Args:
            target_canonical: The canonical row to clear.

        Returns:
            ``None``.

        Side effects:
            Returns the row's source to the pool, removes its alias, clears its
            dtype state, and re-renders.
        """
        self._release_target(target_canonical)
        self._render()

    def _best_unconsumed_match(self, canonical: str) -> str | None:
        """Return the best-scoring unconsumed source column for a canonical name.

        Args:
            canonical: The canonical column name to match.

        Returns:
            The best unconsumed source column name when its normalized similarity
            clears the bind threshold; otherwise ``None``.
        """
        # Score every unconsumed source column against the canonical name using
        # the same normalized similarity Feature B uses, then take the best.
        target_norm = normalize_name(canonical)
        best_name: str | None = None
        best_score = 0.0
        for source in self._state.source_columns:
            ratio = difflib.SequenceMatcher(
                None, target_norm, normalize_name(source)
            ).ratio()
            # Keep the highest score; ties keep the earlier (source-order) column
            # because only a strictly greater score replaces the current best.
            if ratio > best_score:
                best_score = ratio
                best_name = source
        # Only bind when the best candidate is similar enough; otherwise leave the
        # row unassigned for the user to resolve manually.
        if best_name is not None and best_score >= _PREPOPULATE_THRESHOLD:
            return best_name
        return None

    def _bind(self, canonical: str, source: str) -> None:
        """Bind a source column to a canonical row and persist the alias.

        Args:
            canonical: The canonical row receiving the source.
            source: The source column to consume and persist.

        Returns:
            ``None``.

        Side effects:
            Removes ``source`` from the pool, records it in the consumed map, and
            appends it to the column's aliases (de-duplicated).
        """
        # Consume the source so it cannot match a second row.
        if source in self._state.source_columns:
            self._state.source_columns.remove(source)
        self._state.consumed_columns[canonical] = source
        self._add_alias(canonical, source)

    def _release_target(self, canonical: str) -> None:
        """Release the source currently assigned to a canonical row.

        Args:
            canonical: The canonical row to release.

        Returns:
            ``None``.

        Side effects:
            Returns the source to the pool, removes the consumed entry, and
            removes the persisted alias for the released source.
        """
        source = self._state.consumed_columns.pop(canonical, None)
        # Nothing to release when the row had no assignment.
        if source is None:
            return
        # Return the released source to the pool if it is not already present.
        if source not in self._state.source_columns:
            self._state.source_columns.append(source)
        self._remove_alias(canonical, source)

    def _release_source(self, source: str) -> None:
        """Release whichever row currently consumes ``source`` (single-use).

        Args:
            source: The source column to free from any row that consumes it.

        Returns:
            ``None``.

        Side effects:
            Clears the consuming row's assignment so the source can be reassigned.
        """
        # Find the row (if any) that currently consumes this source and release it
        # so the source is never bound to two rows at once.
        for canonical, consumed in list(self._state.consumed_columns.items()):
            if consumed == source:
                self._release_target(canonical)
                return

    def _add_alias(self, canonical: str, source: str) -> None:
        """Append ``source`` to a column's aliases, de-duplicated.

        Args:
            canonical: The canonical column whose aliases are updated.
            source: The source column name to persist as an alias.

        Returns:
            ``None``.

        Side effects:
            Replaces the column row's alias tuple with one including ``source``.
        """
        self._update_aliases(
            canonical,
            lambda aliases: aliases if source in aliases else (*aliases, source),
        )

    def _remove_alias(self, canonical: str, source: str) -> None:
        """Remove ``source`` from a column's aliases.

        Args:
            canonical: The canonical column whose aliases are updated.
            source: The source column name to remove.

        Returns:
            ``None``.

        Side effects:
            Replaces the column row's alias tuple with one excluding ``source``.
        """
        self._update_aliases(
            canonical,
            lambda aliases: tuple(a for a in aliases if a != source),
        )

    def _update_aliases(
        self,
        canonical: str,
        transform: Callable[[tuple[str, ...]], tuple[str, ...]],
    ) -> None:
        """Apply an alias transform to one column row in place.

        Args:
            canonical: The canonical column whose row is updated.
            transform: A callable mapping the current alias tuple to a new one.

        Returns:
            ``None``.

        Side effects:
            Rewrites the matching column row tuple with the transformed aliases.
        """
        # Rebuild the single matching row tuple with its transformed aliases,
        # leaving every other row untouched and preserving order.
        for index, (name, role, required, in_output, aliases) in enumerate(
            self._state.columns
        ):
            if name == canonical:
                new_aliases = transform(aliases)
                self._state.columns[index] = (
                    name,
                    role,
                    required,
                    in_output,
                    new_aliases,
                )
                return

    def _render(self) -> None:
        """Push the pool, rows, assignments, and dtype indicators to the view.

        Returns:
            ``None``.

        Side effects:
            Calls the view's pool/row/assignment/dtype setters for the current
            state.
        """
        self._view.set_source_pool(list(self._state.source_columns))
        # Render each declared column row with its description (currently blank)
        # and the expected dtype carried on the state.
        rows = [
            (name, "", self._state.column_dtypes.get(name))
            for name, _role, _required, _in_output, _aliases in self._state.columns
        ]
        # Decision 7: derived columns authored on the Derived tab become selectable
        # on the Columns tab, so append them as rows (no source match or dtype).
        rows.extend(
            (derived_name, "derived", self._state.column_dtypes.get(derived_name))
            for derived_name, _expression in self._state.derived
        )
        self._view.set_rows(rows)
        self._render_assignments_and_dtypes()

    def _render_assignments_and_dtypes(self) -> None:
        """Push per-row assignment and dtype-check state to the view.

        Returns:
            ``None``.

        Side effects:
            Calls ``view.set_assignment`` for every row and
            ``view.set_dtype_indicator`` for matched rows with an expected dtype.
        """
        slice_ = self._state.preview_slice
        # Push each row's current assignment, then its dtype indicator when both a
        # source is bound and an expected dtype is declared.
        for canonical, _role, _required, _in_output, _aliases in self._state.columns:
            source = self._state.consumed_columns.get(canonical)
            self._view.set_assignment(canonical, source)
            expected = self._state.column_dtypes.get(canonical)
            # The dtype check runs only when a source is matched, a slice exists,
            # and the column declares an expected type to validate against.
            if source is not None and slice_ is not None and expected is not None:
                result = check_dtype(slice_.column_values(source), expected)
                self._view.set_dtype_indicator(
                    canonical, result.coercible, result.failing_example
                )
