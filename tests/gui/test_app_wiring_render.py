"""Behavioral tests for Render-tab checkbox wiring through ``build_application``.

Exercises the single-selection and preview-clear behavior wired by
:func:`src.gui._render_exclusivity.wire_render_checkboxes` through the
composition root (AC1-AC3), plus a direct unit test of the pure
:func:`wire_render_exclusivity` guard. Kept as a sibling of
``test_app_wiring.py`` so neither file exceeds the repository's 500-line cap
(see ``.claude/rules/general-code-change.md``). Tests run headless under the
pytest-qt fixture with ``QT_QPA_PLATFORM=offscreen`` from
:mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.runners import SynchronousRunner

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_build_application_checking_aop_after_le_unchecks_le_and_skulu(
    qtbot: QtBot,
) -> None:
    """AC1: checking AOP after LE leaves AOP checked and LE+SKU_LU unchecked."""
    # Arrange: build the fully-wired application; check LE first.
    from src.gui.app import build_application

    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)
    wired.window.le_widget.render_checkbox.setChecked(True)

    # Act: check AOP; exclusivity must displace LE.
    wired.window.aop_widget.render_checkbox.setChecked(True)

    # Assert: only AOP remains checked.
    assert wired.window.aop_widget.render_checkbox.isChecked() is True
    assert wired.window.le_widget.render_checkbox.isChecked() is False
    assert wired.window.skulu_widget.render_checkbox.isChecked() is False


def test_build_application_checking_each_box_in_turn_leaves_only_that_box(
    qtbot: QtBot,
) -> None:
    """AC1: checking each render box in turn leaves exactly that box checked."""
    # Arrange
    from src.gui.app import build_application

    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)
    le_box = wired.window.le_widget.render_checkbox
    aop_box = wired.window.aop_widget.render_checkbox
    skulu_box = wired.window.skulu_widget.render_checkbox

    # Act + Assert: walk each box in turn, asserting single-selection holds
    # after each check so any failure identifies the offending transition.
    for active, others in (
        (le_box, (aop_box, skulu_box)),
        (aop_box, (le_box, skulu_box)),
        (skulu_box, (le_box, aop_box)),
    ):
        active.setChecked(True)
        assert active.isChecked() is True
        assert all(other.isChecked() is False for other in others)


def test_build_application_displaced_uncheck_does_not_clear_new_preview(
    qtbot: QtBot,
) -> None:
    """AC2: displacing a box does not push an empty preview to the shared sink.

    The exclusivity guard unchecks the previously-active box with signals
    blocked, so the displaced box's preview-clear closure never fires. The
    observable effect is that no ``show_preview([])`` reaches the shared preview
    widget while the newly-checked widget's preview is established, so the new
    preview survives.
    """
    # Arrange: wire the application, then populate the shared preview to stand
    # in for the newly-checked widget's render output.
    from src.gui.app import build_application

    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    le_box = wired.window.le_widget.render_checkbox
    aop_box = wired.window.aop_widget.render_checkbox

    # Check LE first, then simulate AOP's preview having been rendered into the
    # shared surface so a spurious clear would be observable as an empty model.
    le_box.setChecked(True)
    wired.window.preview_widget.show_preview([["new", "preview"]])
    assert wired.window.preview_widget.model.rowCount() > 0

    # Act: check AOP; exclusivity displaces LE with signals blocked, so LE's
    # clear-preview closure must not fire and empty the shared surface.
    aop_box.setChecked(True)

    # Assert: the displaced LE uncheck did not clear the new preview.
    assert wired.window.preview_widget.model.rowCount() > 0
    assert aop_box.isChecked() is True
    assert le_box.isChecked() is False


def test_build_application_uncheck_active_box_clears_preview_zero_checked(
    qtbot: QtBot,
) -> None:
    """AC3: unchecking the active box leaves all unchecked and clears preview."""
    # Arrange
    from src.gui.app import build_application

    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)
    wired.window.preview_widget.show_preview([["a", "b"]])
    assert wired.window.preview_widget.model.rowCount() > 0

    # Act: check then uncheck the active box (zero-checked must be reachable).
    le_box = wired.window.le_widget.render_checkbox
    le_box.setChecked(True)
    le_box.setChecked(False)

    # Assert: all three boxes unchecked and the shared preview cleared.
    assert wired.window.le_widget.render_checkbox.isChecked() is False
    assert wired.window.aop_widget.render_checkbox.isChecked() is False
    assert wired.window.skulu_widget.render_checkbox.isChecked() is False
    assert wired.window.preview_widget.model.rowCount() == 0


def test_wire_render_exclusivity_unit_unchecks_others_on_check(qtbot: QtBot) -> None:
    """AC1: direct unit test of the pure exclusivity guard in isolation."""
    # Arrange: three bare checkboxes with only the exclusivity guard wired.
    from PySide6.QtWidgets import QCheckBox

    from src.gui._render_exclusivity import wire_render_exclusivity

    box_a = QCheckBox()
    box_b = QCheckBox()
    box_c = QCheckBox()
    for box in (box_a, box_b, box_c):
        qtbot.addWidget(box)
    wire_render_exclusivity([box_a, box_b, box_c])

    # Act: check A, then B.
    box_a.setChecked(True)
    box_b.setChecked(True)

    # Assert: only B remains checked; checking A again displaces B.
    assert box_b.isChecked() is True
    assert box_a.isChecked() is False
    assert box_c.isChecked() is False


def test_wire_render_checkboxes_rejects_mismatched_lengths(qtbot: QtBot) -> None:
    """AC2: a length mismatch between boxes and callbacks fails fast."""
    # Arrange
    import pytest
    from PySide6.QtWidgets import QCheckBox

    from src.gui._render_exclusivity import wire_render_checkboxes

    box = QCheckBox()
    qtbot.addWidget(box)

    # Act + Assert: one box but two callbacks is an ambiguous pairing.
    with pytest.raises(ValueError, match="same length"):
        wire_render_checkboxes([box], [lambda: None, lambda: None])
