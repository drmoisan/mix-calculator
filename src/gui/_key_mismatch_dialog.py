"""Qt KEY-mismatch resolver modal for the GUI import path (issue #52).

This module provides the composition-root resolver that the
:class:`~src.gui.pipeline_service.PipelineService` invokes when a source ``KEY``
column diverges from the rebuilt pattern. It presents a Qt modal that explains
the divergence, lists two to three concrete ``(source KEY, computed KEY)`` example
pairs, and offers "Keep existing" (trust, the default) and "Rebuild" (overwrite),
mapping the user's choice to the loader policy string. It lives in its own module
so the seam stays testable and ``app.py`` stays under the 500-line file cap.

Responsibilities:
    - ``build_key_mismatch_resolver``: build an example-aware resolver that
      dispatches the modal on the GUI thread via :class:`KeyMismatchBridge` and
      returns ``"trust"`` or ``"overwrite"``.

The resolver is built around an injectable example-aware ``ask`` callable
(defaulting to a ``QMessageBox``-backed prompt) so tests can drive the
trust/overwrite mapping and assert the rendered examples without opening a real
dialog, and around a cross-thread bridge so the modal always renders on the GUI
thread even when the import runs on a worker thread (issue #52, AC-1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

from src.gui._key_mismatch_bridge import KeyMismatchBridge

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

# The body text explaining the choice to the user. The concrete example pairs are
# appended below this explanation at render time.
_DIALOG_TEXT = (
    "The source KEY column does not match the rebuilt pattern.\n\n"
    "Choose 'Keep existing' to trust the source KEY values, or 'Rebuild' to "
    "overwrite them from their components."
)


def _format_examples(examples: list[tuple[str, str]]) -> str:
    """Render the divergence example pairs as dialog body text (issue #52, AC-2).

    Args:
        examples: Up to three ``(source KEY, computed KEY)`` pairs to show.

    Returns:
        A newline-joined block listing each pair as
        ``"source KEY -> computed KEY"``, prefixed by a short header, or the empty
        string when no examples were supplied (so the dialog body is unchanged).
    """
    # No examples: return an empty block so the body text is the explanation only.
    if not examples:
        return ""

    # Build one line per example pair so the user can compare the source value
    # against the computed value for each diverging row.
    lines = [f"{existing} -> {rebuilt}" for existing, rebuilt in examples]
    return "\n\nExamples (source KEY -> computed KEY):\n" + "\n".join(lines)


def _qmessagebox_ask(
    window: MainWindow | None, examples: list[tuple[str, str]]
) -> bool:
    """Show the KEY-mismatch modal and return whether the user chose "Keep existing".

    Args:
        window: The parent window for the modal (may be ``None``).
        examples: Up to three ``(source KEY, computed KEY)`` example pairs shown
            below the explanation so the user can diagnose the divergence.

    Returns:
        ``True`` when the user chose "Keep existing" (trust, the default),
        ``False`` when the user chose "Rebuild" (overwrite).

    Side effects:
        Shows a blocking modal the user must answer.
    """
    box = QMessageBox(window)
    box.setWindowTitle(DEFAULT_DIALOG_TITLE)
    # Render the explanation plus the concrete example pairs so the dialog carries
    # per-row evidence of the divergence (AC-2).
    box.setText(_DIALOG_TEXT + _format_examples(examples))
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
    ask: Callable[[MainWindow | None, list[tuple[str, str]]], bool] | None = None,
) -> Callable[[list[tuple[str, str]]], str]:
    """Build the example-aware KEY-mismatch resolver for the composition root.

    The returned callable, when invoked by the pipeline service with the
    divergence example pairs, dispatches the Qt modal (or the injected ``ask``
    stand-in) onto the GUI thread via a :class:`KeyMismatchBridge` and maps the
    user's choice to the loader policy: "Keep existing" -> ``"trust"`` and
    "Rebuild" -> ``"overwrite"``. "Keep existing" is the default selection
    (AC-4). The bridge guarantees the modal renders on the GUI thread even when
    the import runs on a worker thread, so no cross-thread Qt construction occurs
    (issue #52, AC-1).

    Args:
        window: The parent window for the modal (may be ``None``). It is captured
            by the bridge on the GUI thread so the marshaled modal has a
            GUI-thread parent.
        ask: Optional injectable example-aware prompt returning ``True`` for
            "Keep existing" and ``False`` for "Rebuild". Defaults to the
            ``QMessageBox``-backed prompt; tests inject a stand-in to assert the
            rendered examples and the trust/overwrite mapping without opening a
            real dialog.

    Returns:
        A ``Callable[[list[tuple[str, str]]], str]`` returning ``"trust"`` or
        ``"overwrite"`` for the supplied example pairs.

    Side effects:
        Constructs a :class:`KeyMismatchBridge` on the calling (GUI) thread bound
        to ``ask`` and ``window``; the bridge is held by the returned closure.
    """
    resolved_ask = ask if ask is not None else _qmessagebox_ask
    # Construct the bridge on the GUI thread so its thread affinity (and the
    # same-thread guard / queued cross-thread dispatch) is established here at the
    # composition root, not lazily on a worker thread.
    bridge = KeyMismatchBridge(resolved_ask, window)

    def _resolver(examples: list[tuple[str, str]]) -> str:
        """Dispatch the modal via the bridge and map the choice to the policy."""
        # "Keep existing" (True) is trust; "Rebuild" (False) is overwrite. The
        # bridge renders the modal on the GUI thread regardless of the caller's
        # thread, so this is safe to call from an import worker.
        return "trust" if bridge.resolve(examples) else "overwrite"

    return _resolver
