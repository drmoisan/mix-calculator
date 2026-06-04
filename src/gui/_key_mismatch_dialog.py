"""Qt KEY-mismatch resolver modal for the GUI import path (WS1a, issue #48).

This module provides the composition-root resolver that the
:class:`~src.gui.pipeline_service.PipelineService` invokes when a source ``KEY``
column diverges from the rebuilt pattern. It presents a Qt modal offering "Keep
existing" (trust, the default) and "Rebuild" (overwrite) and maps the user's
choice to the loader policy string. It lives in its own module so the seam stays
testable and ``app.py`` stays under the 500-line file cap.

Responsibilities:
    - ``build_key_mismatch_resolver``: build a zero-arg resolver that shows the
      modal and returns ``"trust"`` or ``"overwrite"``.

The resolver is built around an injectable ``ask`` callable (defaulting to a
``QMessageBox``-backed prompt) so tests can drive the trust/overwrite mapping
without opening a real dialog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.main_window import MainWindow

__all__ = [
    "DEFAULT_DIALOG_TITLE",
    "KEEP_EXISTING_LABEL",
    "REBUILD_LABEL",
    "build_key_mismatch_resolver",
]

# Button labels shown on the KEY-mismatch modal. "Keep existing" is the default.
KEEP_EXISTING_LABEL = "Keep existing"
REBUILD_LABEL = "Rebuild"
DEFAULT_DIALOG_TITLE = "KEY mismatch"

# The body text explaining the choice to the user.
_DIALOG_TEXT = (
    "The source KEY column does not match the rebuilt pattern.\n\n"
    "Choose 'Keep existing' to trust the source KEY values, or 'Rebuild' to "
    "overwrite them from their components."
)


def _qmessagebox_ask(window: MainWindow | None) -> bool:
    """Show the KEY-mismatch modal and return whether the user chose "Keep existing".

    Args:
        window: The parent window for the modal (may be ``None``).

    Returns:
        ``True`` when the user chose "Keep existing" (trust, the default),
        ``False`` when the user chose "Rebuild" (overwrite).

    Side effects:
        Shows a blocking modal the user must answer.
    """
    box = QMessageBox(window)
    box.setWindowTitle(DEFAULT_DIALOG_TITLE)
    box.setText(_DIALOG_TEXT)
    box.setIcon(QMessageBox.Icon.Question)
    # Add both choices; "Keep existing" is the accept role and the default so a
    # bare Enter/Escape resolves to trust (the safe, non-destructive option).
    keep_button = box.addButton(KEEP_EXISTING_LABEL, QMessageBox.ButtonRole.AcceptRole)
    box.addButton(REBUILD_LABEL, QMessageBox.ButtonRole.DestructiveRole)
    box.setDefaultButton(keep_button)
    box.exec()
    # Compare the clicked button against the retained "Keep existing" handle so
    # the mapping does not depend on standard-button identity.
    return box.clickedButton() is keep_button


def build_key_mismatch_resolver(
    window: MainWindow | None = None,
    *,
    ask: Callable[[MainWindow | None], bool] | None = None,
) -> Callable[[], str]:
    """Build the zero-arg KEY-mismatch resolver for the composition root (WS1a).

    The returned callable, when invoked by the pipeline service, shows the Qt
    modal (or the injected ``ask`` stand-in) and maps the user's choice to the
    loader policy: "Keep existing" -> ``"trust"`` and "Rebuild" ->
    ``"overwrite"``. "Keep existing" is the default selection (AC-2).

    Args:
        window: The parent window for the modal (may be ``None``).
        ask: Optional injectable prompt returning ``True`` for "Keep existing"
            and ``False`` for "Rebuild". Defaults to the ``QMessageBox``-backed
            prompt; tests inject a stand-in to assert the trust/overwrite mapping
            without opening a real dialog.

    Returns:
        A ``Callable[[], str]`` returning ``"trust"`` or ``"overwrite"``.
    """
    resolved_ask = ask if ask is not None else _qmessagebox_ask

    def _resolver() -> str:
        """Show the modal and map the choice to the loader policy."""
        # "Keep existing" (True) is trust; "Rebuild" (False) is overwrite.
        return "trust" if resolved_ask(window) else "overwrite"

    return _resolver
