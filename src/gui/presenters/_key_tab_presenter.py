"""Presenter for the Key-tab drag-and-drop redesign (Decision 2).

This presenter drives a passive :class:`KeyTabViewProtocol`. It manages the ordered
key-part state on the shared :class:`SchemaBuilderState` (column-ref vs literal-text
"Generic Text" parts), parses a caller-supplied default key pattern into structured
parts, supports reordering, assembles the parts into a structured
:class:`~src.schema_model.KeySpec` for saving, and enforces the model invariant that
a key must contain at least one column-ref part.

Responsibilities:
    - ``add_part``/``add_column``/``add_generic_text``: append ordered parts.
    - ``reorder``: reorder the parts by a permutation.
    - ``load_default_pattern``: parse a default pattern into ordered parts.
    - ``build_key``: assemble the parts into a validated ``KeySpec`` (raising on an
      all-literal key).

Scope boundaries:
    - No Qt import. Pattern parsing reuses
      :func:`~src.gui.presenters._schema_builder_state.parse_key_pattern`. The
      presenter performs no I/O.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.presenters._schema_builder_state import parse_key_pattern
from src.schema_model import KeySpec, column_ref, literal_text

if TYPE_CHECKING:
    from src.gui._key_tab_protocol import KeyTabViewProtocol
    from src.gui.presenters._schema_builder_state import SchemaBuilderState
    from src.schema_model import KeyPart

__all__ = ["KeyTabPresenter"]


class KeyTabPresenter:
    """Coordinate ordered key-part composition and assembly (Decision 2).

    Purpose:
        Drive the Key tab: maintain the ordered key parts, parse a default
        pattern, support reordering, and assemble a structured key for saving while
        enforcing the at-least-one-column-ref invariant.

    Responsibilities:
        Append column-ref and literal-text parts in order; reorder parts; parse a
        default pattern into parts; assemble a :class:`KeySpec`. It imports no Qt
        and performs no I/O.

    Usage:
        Construct with a :class:`KeyTabViewProtocol` view and the shared
        :class:`SchemaBuilderState`. Route the view's ``add_key_part`` drops to
        :meth:`add_part`; call :meth:`build_key` to assemble for saving.

    Attributes:
        _view: The Key-tab view this presenter drives.
        _state: The shared in-progress builder state holding ``key_parts``.
    """

    def __init__(self, view: KeyTabViewProtocol, state: SchemaBuilderState) -> None:
        """Initialize the presenter with its view and shared state.

        Args:
            view: The passive Key-tab view to drive.
            state: The shared in-progress builder state.
        """
        self._view = view
        self._state = state

    def add_part(self, kind: str, value: str) -> None:
        """Append a key part of the given kind and render the composition.

        Args:
            kind: The part kind: ``"column-ref"`` or ``"literal-text"``.
            value: The referenced column name (column-ref) or the literal string
                (literal-text).

        Returns:
            ``None``.

        Side effects:
            Appends a :class:`KeyPart` to the state and re-renders the parts.

        Raises:
            SchemaValidationError: If a ``column-ref`` part is constructed with an
                empty value (propagated from :class:`KeyPart`).
        """
        # Build the appropriate structured part; column-ref construction validates
        # a non-empty column name, literal-text accepts any string (Generic Text).
        part = column_ref(value) if kind == "column-ref" else literal_text(value)
        self._state.key_parts.append(part)
        self._render()

    def add_column(self, column_name: str) -> None:
        """Append a column-ref part for ``column_name``.

        Args:
            column_name: The canonical column name to reference.

        Returns:
            ``None``.

        Side effects:
            Appends a column-ref part and re-renders.
        """
        self.add_part("column-ref", column_name)

    def add_generic_text(self, value: str) -> None:
        """Append a repeatable literal-text ("Generic Text") part.

        Generic Text is the only token placeable multiple times; each call adds a
        distinct literal part carrying its own value (Decision 2).

        Args:
            value: The literal string the Generic-Text part contributes.

        Returns:
            ``None``.

        Side effects:
            Appends a literal-text part and re-renders.
        """
        self.add_part("literal-text", value)

    def reorder(self, order: list[int]) -> None:
        """Reorder the key parts by a permutation of their current indices.

        Args:
            order: The new ordering as a permutation of ``range(len(parts))``.

        Returns:
            ``None``.

        Side effects:
            Replaces the state's key-part order and re-renders.

        Raises:
            IndexError: If ``order`` references an index outside the current parts.
        """
        # Rebuild the parts list in the requested order; an out-of-range index
        # raises IndexError so a malformed permutation fails fast.
        self._state.key_parts = [self._state.key_parts[index] for index in order]
        self._render()

    def load_default_pattern(self, pattern: str) -> None:
        """Parse a default key pattern into ordered parts and render them.

        Args:
            pattern: The default key pattern, for example ``"{Customer}-{SKU #}"``.

        Returns:
            ``None``.

        Side effects:
            Replaces the state's key parts with the parsed parts and re-renders.

        Raises:
            SchemaValidationError: If the pattern contains an empty ``{}`` token.
        """
        self._state.key_parts = parse_key_pattern(pattern)
        self._render()

    def build_key(self) -> KeySpec:
        """Assemble the ordered parts into a validated :class:`KeySpec`.

        Returns:
            The assembled :class:`KeySpec` carrying the ordered parts and the
            state's SKU-coercion flag.

        Raises:
            SchemaValidationError: If the parts are empty or contain no column-ref
                part (an all-literal key references no column), propagated from
                :class:`KeySpec`.
        """
        # KeySpec.__post_init__ enforces the at-least-one-column-ref invariant, so
        # an all-literal composition surfaces a validation error here rather than
        # silently producing an invalid key.
        return KeySpec(
            parts=tuple(self._state.key_parts),
            sku_coercion=self._state.sku_coercion,
        )

    @property
    def parts(self) -> list[KeyPart]:
        """Return the current ordered key parts (test/inspection seam).

        Returns:
            The state's ordered :class:`KeyPart` list.
        """
        return self._state.key_parts

    def _render(self) -> None:
        """Push the ordered key parts to the view.

        Returns:
            ``None``.

        Side effects:
            Calls ``view.set_parts`` with the current ordered parts.
        """
        self._view.set_parts([(p.kind, p.value) for p in self._state.key_parts])
