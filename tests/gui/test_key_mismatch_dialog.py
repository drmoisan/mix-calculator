"""Tests for the example-aware Qt KEY-mismatch resolver modal (issue #52).

Verifies that :func:`src.gui._key_mismatch_dialog.build_key_mismatch_resolver`
renders the 2-3 ``(source KEY, computed KEY)`` example pairs in the dialog body
(AC-2), maps the dialog choice to the loader policy ("Keep existing" -> trust,
the default; "Rebuild" -> overwrite) (AC-4) without opening a real dialog, and
that the composition root injects the example-aware resolver into the production
:class:`PipelineService` as the loaders' divergence-only resolver callable (AC-5;
reinforces AC-1/AC-3). Runs headless under ``QT_QPA_PLATFORM=offscreen`` from
:mod:`tests.gui.conftest`.
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

# Representative diverging example pairs used across the rendering/mapping tests.
_EXAMPLES: list[tuple[str, str]] = [
    ("LEGACY_A", "CustA5GS"),
    ("LEGACY_B", "CustB7GS"),
]


class _FakeButton:
    """Stand-in for a QMessageBox button carrying its label.

    Attributes:
        label: The button text supplied to ``addButton``.
    """

    def __init__(self, label: str) -> None:
        """Initialize with the button label."""
        self.label = label


class _FakeMessageBox:
    """Recording QMessageBox stand-in that captures the body text and resolves.

    Purpose:
        Drive the QMessageBox-backed resolver without opening a real dialog. The
        box records the body text passed to ``setText`` so tests can assert the
        rendered example pairs, and reports the button matching ``keep_label`` as
        clicked when ``return_keep`` is ``True``, else the other button.

    Attributes:
        return_keep: Whether the box should report "Keep existing" as clicked.
        keep_label: The label that maps to the trust policy.
        last_text: The most recent body text passed to ``setText`` (class-level
            so the test can read it after the resolver runs).
    """

    return_keep = True
    keep_label = _key_mismatch_dialog.KEEP_EXISTING_LABEL
    last_text = ""

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

    def setText(self, text: str) -> None:
        """Record the body text so tests can assert the rendered examples."""
        type(self).last_text = text

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

    def default_button_label(self) -> str | None:
        """Return the label of the recorded default button (test accessor)."""
        return self._default.label if self._default is not None else None

    def exec(self) -> None:
        """Simulate showing the modal (no-op)."""

    def clickedButton(self) -> _FakeButton | None:
        """Return the keep/rebuild button per ``return_keep``."""
        keep = next((b for b in self._buttons if b.label == self.keep_label), None)
        other = next((b for b in self._buttons if b.label != self.keep_label), None)
        return keep if type(self).return_keep else other


def test_resolver_maps_keep_existing_to_trust() -> None:
    """The 'Keep existing' choice maps to the trust policy (the default)."""
    # Arrange: an example-aware ask stand-in that returns True ("Keep existing").
    resolver = build_key_mismatch_resolver(ask=lambda _window, _examples: True)

    # Act / Assert
    assert resolver(_EXAMPLES) == "trust"


def test_resolver_maps_rebuild_to_overwrite() -> None:
    """The 'Rebuild' choice maps to the overwrite policy."""
    # Arrange: an example-aware ask stand-in that returns False ("Rebuild").
    resolver = build_key_mismatch_resolver(ask=lambda _window, _examples: False)

    # Act / Assert
    assert resolver(_EXAMPLES) == "overwrite"


def test_resolver_forwards_examples_to_ask() -> None:
    """The resolver forwards the example pairs to the injected ask seam (AC-2)."""
    # Arrange: an ask stand-in that records the examples it receives.
    received: list[list[tuple[str, str]]] = []

    def _ask(_window: object, examples: list[tuple[str, str]]) -> bool:
        received.append(examples)
        return True

    resolver = build_key_mismatch_resolver(ask=_ask)

    # Act
    resolver(_EXAMPLES)

    # Assert: the exact example pairs reached the dialog seam.
    assert received == [_EXAMPLES]


def test_qmessagebox_renders_example_pairs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The QMessageBox body renders each (source, computed) example pair (AC-2).

    Patches ``QMessageBox`` at its import location so no real dialog opens; the
    fake records the body text passed to ``setText`` so the test asserts each
    pair appears.
    """
    # Arrange: the fake resolves to "Keep existing" and records the body text.
    _FakeMessageBox.return_keep = True
    _FakeMessageBox.last_text = ""
    monkeypatch.setattr(
        _key_mismatch_dialog, "QMessageBox", _FakeMessageBox, raising=True
    )
    resolver = build_key_mismatch_resolver(window=None)

    # Act
    resolver(_EXAMPLES)

    # Assert: each example pair is rendered in the dialog body.
    body = _FakeMessageBox.last_text
    for existing, rebuilt in _EXAMPLES:
        assert existing in body
        assert rebuilt in body


def test_qmessagebox_body_omits_examples_block_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no example pairs the dialog body is the explanation only (no block).

    Covers the empty-examples branch: the body must not contain the
    "Examples" header when no diverging pairs are supplied.
    """
    # Arrange: the fake resolves to "Keep existing" and records the body text.
    _FakeMessageBox.return_keep = True
    _FakeMessageBox.last_text = ""
    monkeypatch.setattr(
        _key_mismatch_dialog, "QMessageBox", _FakeMessageBox, raising=True
    )
    resolver = build_key_mismatch_resolver(window=None)

    # Act: resolve with no example pairs.
    resolver([])

    # Assert: the explanation is present but the examples block is omitted.
    body = _FakeMessageBox.last_text
    assert "does not match the rebuilt pattern" in body
    assert "Examples" not in body


def test_qmessagebox_default_button_is_keep_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ "Keep existing" is set as the dialog's default button (AC-4)."""
    # Arrange: capture the constructed fake box so its default can be asserted.
    boxes: list[_FakeMessageBox] = []
    original_init = _FakeMessageBox.__init__

    def _record_init(self: _FakeMessageBox, parent: object) -> None:
        original_init(self, parent)
        boxes.append(self)

    _FakeMessageBox.return_keep = True
    monkeypatch.setattr(
        _key_mismatch_dialog, "QMessageBox", _FakeMessageBox, raising=True
    )
    monkeypatch.setattr(_FakeMessageBox, "__init__", _record_init, raising=True)
    resolver = build_key_mismatch_resolver(window=None)

    # Act
    resolver(_EXAMPLES)

    # Assert: the default button is "Keep existing".
    assert len(boxes) == 1
    assert boxes[0].default_button_label() == _key_mismatch_dialog.KEEP_EXISTING_LABEL


def test_qmessagebox_resolver_default_maps_to_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The QMessageBox-backed resolver's default ('Keep existing') maps to trust.

    Patches ``QMessageBox`` at its import location so no real dialog opens; the
    fake reports the "Keep existing" button as clicked, modeling the default
    (Enter) resolution (AC-4).
    """
    # Arrange: the fake resolves to "Keep existing".
    _FakeMessageBox.return_keep = True
    monkeypatch.setattr(
        _key_mismatch_dialog, "QMessageBox", _FakeMessageBox, raising=True
    )
    resolver = build_key_mismatch_resolver(window=None)

    # Act / Assert
    assert resolver(_EXAMPLES) == "trust"


def test_build_application_injects_resolver_callable(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The composition root injects the resolver callable into the service (AC-5).

    Drives an AOP import through the production pipeline service (no injected
    service); asserts the AOP loader received the example-aware resolver as its
    ``resolver`` argument (a callable), proving the resolver reaches the loaders
    as the divergence-only seam and that no eager invocation or stdin occurs.
    """
    # Arrange: record the resolver the AOP loader receives.
    recorded: list[object] = []

    def _fake_load_aop(
        _path: str,
        *,
        sheet: str = "AOP1",
        resolver: object = None,
        **_kwargs: object,
    ) -> pd.DataFrame:
        recorded.append(resolver)
        return pd.DataFrame({"KEY": ["k1"]})

    monkeypatch.setattr("src.load_aop.load_aop", _fake_load_aop)
    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    # Act: import AOP through the production service's injected resolver.
    wired.pipeline_service.import_aop("aop.xlsx", "AOP1")

    # Assert: the loader received a callable resolver (the divergence-only seam),
    # not an eagerly computed policy string.
    assert len(recorded) == 1
    assert callable(recorded[0])
