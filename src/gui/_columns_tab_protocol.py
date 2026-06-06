"""View-protocol seam for the Columns tab drag-and-drop redesign (research G).

This module declares the ``typing.Protocol`` the Columns-tab presenter drives. The
drag-and-drop assignment is expressed as a single ``assign_column`` seam method so
presenter tests never simulate Qt drag events: the Qt widget translates a drop
gesture into one ``assign_column`` call, and the presenter test drives that method
directly. Pool and row setters let the presenter push the draggable source-column
pool and the required/optional rows (with expected dtype and pass/fail state).

Responsibilities:
    - Declare ``ColumnsTabViewProtocol`` with the assignment seam and the pool,
      row, and dtype-indicator setters.

Scope boundaries:
    - No Qt import, no Qt types. Structural and ``@runtime_checkable`` so the Qt
      widget and a test fake both satisfy it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["ColumnsTabViewProtocol"]


@runtime_checkable
class ColumnsTabViewProtocol(Protocol):
    """Contract for the Columns-tab drag-and-drop view.

    Purpose:
        The view that renders the draggable source-column token pool, the
        required/optional canonical rows (with name, description, expected dtype),
        and per-row pass/fail dtype indicators, and reports drop gestures as
        ``assign_column`` calls.

    Responsibilities:
        Render the pool and rows the presenter pushes; reflect assignments and the
        dtype-check state; report each drop as a single ``assign_column`` call. It
        holds no logic; the ``ColumnsTabPresenter`` drives it. All data is plain
        Python; no Qt types appear in the contract.

    Usage:
        The presenter calls the setters as the pool/rows change; the Qt widget (or
        a test fake) implements the contract and invokes ``assign_column`` on drop.
    """

    def assign_column(self, source_column: str, target_canonical: str) -> None:
        """Report that ``source_column`` was dropped onto ``target_canonical``.

        This is the single drag-and-drop seam: the Qt widget calls it once per
        drop, and presenter tests call it directly without simulating a drag.

        Args:
            source_column: The dragged source column name.
            target_canonical: The canonical row the source was dropped onto.

        Returns:
            ``None``.

        Side effects:
            Routed by the presenter to update the assignment and consumed pool.
        """
        ...

    def set_source_pool(self, columns: list[str]) -> None:
        """Render the draggable source-column token pool.

        Args:
            columns: The unconsumed source column names, in source order.

        Returns:
            ``None``.

        Side effects:
            Updates the view's token pool.
        """
        ...

    def set_rows(self, rows: list[tuple[str, str, str | None]]) -> None:
        """Render the required/optional canonical rows.

        Args:
            rows: One ``(canonical_name, description, expected_dtype)`` tuple per
                row, in display order; ``expected_dtype`` is a dtype vocabulary
                value or ``None``.

        Returns:
            ``None``.

        Side effects:
            Updates the view's row table.
        """
        ...

    def set_assignment(self, target_canonical: str, source_column: str | None) -> None:
        """Reflect the source column assigned to one row (or cleared).

        Args:
            target_canonical: The canonical row whose assignment changed.
            source_column: The newly-assigned source column, or ``None`` when the
                row was cleared.

        Returns:
            ``None``.

        Side effects:
            Updates the view's assignment display for ``target_canonical``.
        """
        ...

    def set_dtype_indicator(
        self, target_canonical: str, coercible: bool, failing_example: str | None
    ) -> None:
        """Reflect the dtype-check result for one row.

        Args:
            target_canonical: The canonical row whose dtype state changed.
            coercible: ``True`` when the matched source values coerce to the
                expected dtype (green check); ``False`` otherwise (red X).
            failing_example: A masked example value that failed to coerce when
                ``coercible`` is ``False``; ``None`` when coercible.

        Returns:
            ``None``.

        Side effects:
            Updates the view's per-row dtype indicator.
        """
        ...
