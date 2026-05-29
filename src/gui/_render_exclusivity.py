"""Composition-root helper that wires the Render-tab checkboxes.

The three per-input Render-tab checkboxes (LE, AOP, SKU_LU) share one preview
surface, so only one render selection is meaningful at a time. This module wires
both behaviors that govern those checkboxes at the composition root:

    - Preview-clear: on a ``toggled(False)`` transition only, invoke the owning
      presenter's clear-preview callback so unchecking the active box clears the
      shared preview surface.
    - Single-selection (mutual exclusion): on a check-to-``True`` transition,
      uncheck the other boxes with their signals blocked.

Mutual exclusion uses ``blockSignals`` re-entrancy guards rather than a
:class:`QButtonGroup` because the zero-checked state must remain reachable and
the displaced boxes must not emit the ``toggled(False)`` signal that the
preview-clear closure listens for.

Public surface:
    - :func:`wire_render_checkboxes` — the single composition-root entry point.
      It wires the preview-clear closures first, then delegates mutual exclusion
      to :func:`wire_render_exclusivity` on the same box list.
    - :func:`wire_render_exclusivity` — the pure exclusivity guard, retained as a
      public symbol so it stays independently unit-testable.

The module contains no domain or preview logic; it performs Qt signal wiring
only. The exclusivity closures are no-ops on a ``toggled(False)`` transition so
the preview-clear path remains the sole handler of unchecks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PySide6.QtWidgets import QCheckBox

__all__ = ["wire_render_checkboxes", "wire_render_exclusivity"]


def wire_render_checkboxes(
    checkboxes: Sequence[QCheckBox],
    clear_callbacks: Sequence[Callable[[], None]],
) -> None:
    """Wire preview-clear and single-selection across the Render-tab checkboxes.

    This is the single composition-root entry point for Render-tab checkbox
    behavior. It first connects each checkbox to a closure that invokes the
    positionally-aligned clear-preview callback on a ``toggled(False)``
    transition, then delegates mutual exclusion to
    :func:`wire_render_exclusivity` over the same box list. Wiring preview-clear
    before exclusivity ensures the displaced unchecks performed by the
    exclusivity guard (which block signals) never reach the clear-preview
    closures, so the newly-checked widget's preview survives.

    Args:
        checkboxes: The Render-tab checkboxes to coordinate. The order is not
            significant for exclusivity, but each box is paired positionally
            with the matching entry in ``clear_callbacks``.
        clear_callbacks: The per-checkbox clear-preview callbacks, aligned
            positionally with ``checkboxes``. Each callback is invoked with no
            arguments when its checkbox transitions to unchecked.

    Returns:
        ``None``.

    Raises:
        ValueError: If ``checkboxes`` and ``clear_callbacks`` differ in length,
            because the positional pairing would otherwise be ambiguous.

    Side effects:
        Connects a ``toggled`` slot on every checkbox: one preview-clear closure
        per box, plus the exclusivity slot installed by
        :func:`wire_render_exclusivity`.
    """
    boxes = list(checkboxes)
    callbacks = list(clear_callbacks)
    # Fail fast on a misaligned pairing: a length mismatch means some checkbox
    # would have no clear callback (or vice versa), which is a wiring error.
    if len(boxes) != len(callbacks):
        msg = (
            "checkboxes and clear_callbacks must be the same length; "
            f"got {len(boxes)} checkboxes and {len(callbacks)} callbacks"
        )
        raise ValueError(msg)

    # Connect each checkbox to a preview-clear closure that fires only on an
    # uncheck, preserving the existing "if not checked: clear" semantics that
    # previously lived inline in app.py.
    for box, callback in zip(boxes, callbacks, strict=True):
        box.toggled.connect(_make_preview_clear(callback))

    # Delegate single-selection to the retained pure exclusivity helper. It is
    # wired after the preview-clear closures so the displaced unchecks it
    # performs (with signals blocked) never trigger a clear-preview.
    wire_render_exclusivity(boxes)


def _make_preview_clear(clear_callback: Callable[[], None]) -> Callable[[bool], None]:
    """Build the ``toggled`` slot that clears the preview on an uncheck.

    Args:
        clear_callback: The zero-argument callback invoked when the owning
            checkbox transitions to unchecked.

    Returns:
        A callable taking the new checked state; it invokes ``clear_callback``
        only on a ``toggled(False)`` transition.
    """

    def _on_toggled(checked: bool) -> None:
        """Invoke the clear-preview callback when the checkbox is unchecked.

        Args:
            checked: The new checked state emitted by the owning checkbox.

        Returns:
            ``None``.

        Side effects:
            Calls ``clear_callback`` on ``checked is False`` only; a no-op on a
            check-to-``True`` transition.
        """
        # Clearing fires only on an uncheck; checking is handled by the
        # exclusivity guard and the widget's own render-tab path.
        if not checked:
            clear_callback()

    return _on_toggled


def wire_render_exclusivity(checkboxes: Sequence[QCheckBox]) -> None:
    """Wire single-selection behavior across the given Render-tab checkboxes.

    For each checkbox, connect its ``toggled`` signal to a closure that, on a
    check-to-``True`` transition only, unchecks every other checkbox in the
    sequence. Each displaced uncheck is wrapped in ``blockSignals(True)`` /
    ``blockSignals(False)`` spanning exactly the ``setChecked(False)`` call so
    the displaced box emits no ``toggled`` signal. This suppresses the existing
    composition-root preview-clear closure and the widget-internal render
    handler for the displaced boxes, leaving the newly-checked widget's preview
    intact.

    Args:
        checkboxes: The Render-tab checkboxes to coordinate. The order is not
            significant; each box is made exclusive against all the others.

    Returns:
        ``None``.

    Side effects:
        Connects a ``toggled`` slot on every checkbox in ``checkboxes``. The
        closure mutates the checked state of the other boxes (with their
        signals blocked) only on a check-to-``True`` transition; it is a no-op
        on a ``toggled(False)`` transition so the zero-checked state stays
        reachable.
    """
    # Snapshot the coordinated set once so each closure captures a stable list;
    # the per-checkbox closure compares identity to skip the box that toggled.
    boxes = list(checkboxes)

    def _make_exclusive_handler(source: QCheckBox) -> Callable[[bool], None]:
        """Build the ``toggled`` slot enforcing exclusivity for one checkbox.

        Args:
            source: The checkbox whose ``toggled`` signal this slot handles.

        Returns:
            A callable taking the new checked state and unchecking the other
            boxes on a check-to-``True`` transition.
        """

        def _on_toggled(checked: bool) -> None:
            """Uncheck the other boxes when ``source`` transitions to checked.

            Args:
                checked: The new checked state emitted by ``source``.

            Returns:
                ``None``.

            Side effects:
                On ``checked is True`` only, sets every other box unchecked
                with its signals blocked so no displaced ``toggled`` fires. A
                no-op on ``checked is False`` so the existing clear-preview
                path remains the sole uncheck handler.
            """
            # Exclusivity fires only on a check-to-True transition; an uncheck
            # is left entirely to the existing clear-preview closure.
            if not checked:
                return
            # Uncheck every box except the one that was just checked. Block the
            # displaced box's signals across exactly the setChecked call so it
            # emits no toggled(False) that would clear the new preview.
            for other in boxes:
                if other is source:
                    continue
                other.blockSignals(True)
                other.setChecked(False)
                other.blockSignals(False)

        return _on_toggled

    # Connect each checkbox to its own exclusivity slot so any box that becomes
    # checked displaces the others.
    for box in boxes:
        box.toggled.connect(_make_exclusive_handler(box))
