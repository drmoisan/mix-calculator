"""Discriminator-dropdown population for the schema-builder Dedup tab (Decision 6).

This helper isolates the logic that rebuilds the dedup discriminator dropdown so
the :class:`~src.gui.widgets.schema_builder_dialog.SchemaBuilderDialog` stays
under the repository's 500-line cap. The dropdown only ever offers existing
canonical/derived column names plus the ``Key`` sentinel, so a non-existent
column cannot be selected as the discriminator.

Responsibilities:
    - ``populate_discriminator_options``: rebuild a discriminator ``QComboBox``
      from the current canonical and derived names plus the ``Key`` sentinel,
      preserving a still-valid current selection.

Scope boundaries:
    - Thin Qt-combo population. No service, matching, or transform logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6.QtWidgets import QComboBox

    from src.gui.widgets._schema_builder_tabs import DedupTabControls

__all__ = [
    "KEY_DISCRIMINATOR",
    "populate_discriminator_options",
    "read_dedup_controls",
    "select_dedup_discriminator",
]

# Sentinel discriminator value meaning "use the schema Key" (Decision 6). Always
# offered as the default discriminator option.
KEY_DISCRIMINATOR = "Key"


def populate_discriminator_options(
    combo: QComboBox,
    canonical_names: Iterable[str],
    derived_names: Iterable[str],
) -> None:
    """Rebuild the discriminator dropdown from existing columns + the Key.

    Builds the option list from the current canonical and derived names plus the
    ``Key`` sentinel so the dropdown only ever offers existing columns (or the
    Key) as discriminator (Decision 6). A still-valid prior selection is restored
    so a repopulate does not silently drop the user's choice.

    Args:
        combo: The discriminator ``QComboBox`` to repopulate in place.
        canonical_names: The current Columns-tab canonical column names.
        derived_names: The current Derived-tab column names.

    Returns:
        ``None``.

    Side effects:
        Clears and rebuilds ``combo``'s items, preserving the current selection
        when it remains a valid option.
    """
    current = combo.currentText()
    # The Key sentinel leads so it is the default; existing canonical and derived
    # names follow so only real targets appear as discriminator options.
    options = [KEY_DISCRIMINATOR, *canonical_names, *derived_names]
    combo.clear()
    combo.addItems(options)
    # Restore the prior selection when it is still a valid option.
    index = combo.findText(current)
    if index >= 0:
        combo.setCurrentIndex(index)


def select_dedup_discriminator(
    controls: DedupTabControls,
    mode: str,
    discriminator: str | None,
    canonical_names: Iterable[str],
    derived_names: Iterable[str],
) -> None:
    """Populate the dropdown, set the mode, and select a valid discriminator.

    First repopulates the discriminator dropdown from the existing canonical and
    derived names plus the ``Key`` sentinel (Decision 6), then sets the mode and
    selects the discriminator only when it is present in the dropdown, so the
    invariant "discriminator references an existing column (or the Key)" holds. An
    absent or unknown discriminator leaves the current valid selection untouched.

    Args:
        controls: The dedup-tab controls (mode + discriminator combos).
        mode: The dedup mode to select (auto/aggregate/collapse/none).
        discriminator: The discriminator column to select, or ``None``.
        canonical_names: The current canonical column names for the dropdown.
        derived_names: The current derived column names for the dropdown.

    Returns:
        ``None``.

    Side effects:
        Rebuilds the discriminator dropdown, sets the mode, and updates the
        discriminator selection when the value is present.
    """
    populate_discriminator_options(
        controls.discriminator, canonical_names, derived_names
    )
    controls.mode.setCurrentText(mode)
    if discriminator is not None:
        index = controls.discriminator.findText(discriminator)
        if index >= 0:
            controls.discriminator.setCurrentIndex(index)


def read_dedup_controls(controls: DedupTabControls) -> tuple[str, str | None]:
    """Read the dedup mode and discriminator from the controls (D-3).

    Auto mode derives the groupby from column roles and so carries no
    discriminator regardless of the dropdown selection; every other mode reports
    the trimmed discriminator text (or ``None`` when empty).

    Args:
        controls: The dedup-tab controls (mode + discriminator combos).

    Returns:
        A ``(mode, discriminator)`` tuple; the discriminator is ``None`` for
        ``auto`` or when no selectable column is chosen.
    """
    mode = controls.mode.currentText()
    if mode == "auto":
        return (mode, None)
    return (mode, controls.discriminator.currentText().strip() or None)
