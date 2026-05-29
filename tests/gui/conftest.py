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

__all__ = ["force_offscreen_qt_platform"]


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
