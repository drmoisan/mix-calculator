"""Tests for the WS1a Qt KEY-mismatch resolver modal (issue #48).

Verifies that :func:`src.gui._key_mismatch_dialog.build_key_mismatch_resolver`
maps the dialog choice to the loader policy ("Keep existing" -> trust, the
default; "Rebuild" -> overwrite) without opening a real dialog, and that the
composition root injects the resolver into the production
:class:`PipelineService` (AC-2; reinforces AC-1/AC-3). Runs headless under
``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.gui import _key_mismatch_dialog
from src.gui._key_mismatch_dialog import build_key_mismatch_resolver
from src.gui.app import build_application
from src.gui.runners import SynchronousRunner

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot


class _FakeButton:
    """Stand-in for a QMessageBox button carrying its label.

    Attributes:
        label: The button text supplied to ``addButton``.
    """

    def __init__(self, label: str) -> None:
        """Initialize with the button label."""
        self.label = label


class _FakeMessageBox:
    """Recording QMessageBox stand-in that resolves to a chosen label.

    Purpose:
        Drive the QMessageBox-backed resolver without opening a real dialog. The
        box reports the button matching ``keep_label`` as clicked when
        ``return_keep`` is ``True``, else the other button.

    Attributes:
        return_keep: Whether the box should report "Keep existing" as clicked.
        keep_label: The label that maps to the trust policy.
    """

    return_keep = True
    keep_label = _key_mismatch_dialog.KEEP_EXISTING_LABEL

    class Icon:
        """Icon-enum stand-in exposing the ``Question`` member used by the dialog."""

        Question = object()

    class ButtonRole:
        """ButtonRole-enum stand-in exposing the roles used by the dialog."""

        AcceptRole = object()
        DestructiveRole = object()

    def __init__(self, _parent: object) -> None:
        """Initialize with no recorded buttons."""
        self._buttons: list[_FakeButton] = []
        self._default: _FakeButton | None = None

    def setWindowTitle(self, _title: str) -> None:
        """Accept the window title (no-op)."""

    def setText(self, _text: str) -> None:
        """Accept the body text (no-op)."""

    def setIcon(self, _icon: object) -> None:
        """Accept the icon (no-op)."""

    def addButton(self, label: str, _role: object) -> _FakeButton:
        """Record and return a fake button for the label."""
        button = _FakeButton(label)
        self._buttons.append(button)
        return button

    def setDefaultButton(self, button: _FakeButton) -> None:
        """Record the default button."""
        self._default = button

    def exec(self) -> None:
        """Simulate showing the modal (no-op)."""

    def clickedButton(self) -> _FakeButton | None:
        """Return the keep/rebuild button per ``return_keep``."""
        keep = next((b for b in self._buttons if b.label == self.keep_label), None)
        other = next((b for b in self._buttons if b.label != self.keep_label), None)
        return keep if type(self).return_keep else other


def test_resolver_maps_keep_existing_to_trust() -> None:
    """The 'Keep existing' choice maps to the trust policy (the default)."""
    # Arrange: an ask stand-in that returns True ("Keep existing").
    resolver = build_key_mismatch_resolver(ask=lambda _window: True)

    # Act / Assert
    assert resolver() == "trust"


def test_resolver_maps_rebuild_to_overwrite() -> None:
    """The 'Rebuild' choice maps to the overwrite policy."""
    # Arrange: an ask stand-in that returns False ("Rebuild").
    resolver = build_key_mismatch_resolver(ask=lambda _window: False)

    # Act / Assert
    assert resolver() == "overwrite"


def test_qmessagebox_resolver_default_maps_to_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The QMessageBox-backed resolver's default ('Keep existing') maps to trust.

    Patches ``QMessageBox`` at its import location so no real dialog opens; the
    fake reports the "Keep existing" button as clicked, modeling the default
    (Enter) resolution (AC-2).
    """
    # Arrange: the fake resolves to "Keep existing".
    _FakeMessageBox.return_keep = True
    monkeypatch.setattr(
        _key_mismatch_dialog, "QMessageBox", _FakeMessageBox, raising=True
    )
    resolver = build_key_mismatch_resolver(window=None)

    # Act / Assert
    assert resolver() == "trust"


def test_build_application_injects_resolver_forwarding_trust(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The composition root injects the modal resolver into the service (AC-2).

    Drives an AOP import through the production pipeline service (no injected
    service) with the modal forced to "Keep existing"; asserts the loader
    received the "trust" policy, proving the resolver reaches the loaders and no
    stdin is consulted.
    """
    # Arrange: force the modal to resolve to "Keep existing" and record the
    # policy the AOP loader receives.
    _FakeMessageBox.return_keep = True
    monkeypatch.setattr(
        _key_mismatch_dialog, "QMessageBox", _FakeMessageBox, raising=True
    )
    recorded: list[str] = []

    def _fake_load_aop(
        _path: str,
        *,
        sheet: str = "AOP1",
        key_mismatch: str = "prompt",
        **_kwargs: object,
    ) -> pd.DataFrame:
        recorded.append(key_mismatch)
        return pd.DataFrame({"KEY": ["k1"]})

    monkeypatch.setattr("src.load_aop.load_aop", _fake_load_aop)
    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    # Act: import AOP through the production service's injected resolver.
    wired.pipeline_service.import_aop("aop.xlsx", "AOP1")

    # Assert: the modal default ("Keep existing") forwarded "trust" to the loader.
    assert recorded == ["trust"]
