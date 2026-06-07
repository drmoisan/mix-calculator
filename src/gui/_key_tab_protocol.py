"""View-protocol seam for the Key tab drag-and-drop redesign (research G).

This module declares the ``typing.Protocol`` the Key-tab presenter drives. Key
composition is expressed through seam methods (``add_key_part``, ``reorder_parts``,
``set_parts``) so presenter tests drive ordered key composition without simulating
Qt drag events: the Qt widget translates a column or Generic-Text drop into a single
``add_key_part`` call, and presenter tests call the seam directly.

Responsibilities:
    - Declare ``KeyTabViewProtocol`` with the part-add, reorder, and set methods.

Scope boundaries:
    - No Qt import, no Qt types. Structural and ``@runtime_checkable`` so the Qt
      widget and a test fake both satisfy it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["KeyTabViewProtocol"]


@runtime_checkable
class KeyTabViewProtocol(Protocol):
    """Contract for the Key-tab drag-and-drop view.

    Purpose:
        The view that renders the ordered key-part rows (column-ref and
        literal-text "Generic Text" parts) and reports drop gestures as
        ``add_key_part`` calls.

    Responsibilities:
        Render the ordered parts the presenter pushes; report a column or
        Generic-Text drop as a single ``add_key_part`` call. It holds no logic;
        the ``KeyTabPresenter`` drives it. All data is plain Python; no Qt types
        appear in the contract.

    Usage:
        The presenter calls ``set_parts`` as the composition changes; the Qt widget
        (or a test fake) implements the contract and invokes ``add_key_part`` on a
        drop.
    """

    def add_key_part(self, kind: str, value: str) -> None:
        """Report that a key part was dropped onto the composition.

        Args:
            kind: The part kind: ``"column-ref"`` or ``"literal-text"``.
            value: The referenced column name (column-ref) or the literal string
                (literal-text).

        Returns:
            ``None``.

        Side effects:
            Routed by the presenter to append the part to the ordered key.
        """
        ...

    def set_parts(self, parts: list[tuple[str, str]]) -> None:
        """Render the ordered key parts.

        Args:
            parts: One ``(kind, value)`` tuple per key part, in order.

        Returns:
            ``None``.

        Side effects:
            Replaces the view's key-part rows.
        """
        ...

    def reorder_parts(self, order: list[int]) -> None:
        """Report a user reordering of the key parts.

        Args:
            order: The new ordering as a permutation of the current part indices.

        Returns:
            ``None``.

        Side effects:
            Routed by the presenter to reorder the key parts.
        """
        ...
