"""Pytest configuration for the GUI test suite (headless Qt harness).

This conftest forces the Qt platform to ``offscreen`` before any Qt import so
the widget and worker tests run headless in CI (no display server). The
repository unit-test policy requires deterministic, environment-independent
tests; pinning the platform to ``offscreen`` removes the dependency on a real
windowing system and keeps widget construction reproducible across machines.

The environment variable is set at module import time (when pytest first
imports this conftest, before it collects any test module that imports
``PySide6``), so the platform plugin is selected before ``QApplication`` is ever
constructed. A session-scoped autouse fixture additionally asserts the variable
is in place for every test, documenting the invariant and failing loudly if a
later import path ever clears it.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

# Pin the Qt platform to offscreen at import time, before any test module
# imports PySide6. Setting it here (rather than only in a fixture) guarantees
# the plugin is chosen before the first QApplication is constructed during
# collection of the Qt test modules.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

__all__ = ["force_offscreen_qt_platform", "suppress_blocking_error_modals"]


@pytest.fixture(scope="session", autouse=True)
def force_offscreen_qt_platform() -> Iterator[None]:
    """Ensure the Qt platform stays ``offscreen`` for the whole test session.

    The variable is already set at module import; this fixture re-asserts it for
    every session so the headless invariant is explicit and any accidental clear
    by another import path fails fast with a clear message.

    Yields:
        ``None``. The fixture only enforces the environment invariant.
    """
    # Re-assert the headless platform; setdefault at import time should already
    # have placed it, but enforce it here so the invariant is verifiable.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
    yield


@pytest.fixture(autouse=True)
def suppress_blocking_error_modals(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    """Replace the WS4 error modal with a no-op so tests never block (issue #48).

    The WS4 error surface (:meth:`MainWindowPipelineView.show_error` /
    :meth:`show_dialog_error`) calls ``QMessageBox.critical``, which is a
    blocking modal. Under the offscreen platform an unacknowledged modal would
    hang the suite. This autouse fixture patches ``QMessageBox.critical`` at its
    import location in ``_main_window_view`` to a no-op for every GUI test so the
    error path runs without blocking. Tests that need to assert the modal (for
    example ``test_main_window_view``) re-patch it in their own body; that patch
    runs after this fixture and therefore takes precedence.

    Yields:
        ``None``. The fixture only installs the non-blocking modal stub.
    """

    def _noop_critical(*_args: object, **_kwargs: object) -> None:
        """Swallow a critical-modal invocation without opening a dialog."""

    # Patch at the import location used by the unit under test (the view module),
    # per the repository's patch-where-used rule.
    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical",
        _noop_critical,
        raising=True,
    )
    yield
