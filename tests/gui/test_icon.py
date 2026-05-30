"""Unit tests for :mod:`src.gui._icon` icon-path resolution helper.

The helper resolves the application icon path independently of any Qt
runtime, so the tests inject a ``path_exists`` callable to drive every
probe branch deterministically. No real filesystem is touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def test_resolve_icon_path_prefers_compiled_mode() -> None:
    """Compiled-mode probe wins when its sibling icon.ico is reported existing.

    The helper probes the compiled-mode location first (next to the running
    executable). When that path's existence callable reports True, the
    helper must return that path without checking the dev-mode fallback.
    """
    # Arrange: import the unit under test and compute the expected probe.
    from src.gui._icon import resolve_icon_path

    expected = Path(sys.executable).parent / "icon.ico"

    # Inject a callable that reports True only for the compiled-mode probe.
    def fake_exists(path: Path) -> bool:
        return path == expected

    # Act
    resolved = resolve_icon_path(path_exists=fake_exists)

    # Assert: the helper returned the compiled-mode path.
    assert resolved == expected


def test_resolve_icon_path_falls_back_to_dev_mode() -> None:
    """Dev-mode probe wins when the compiled-mode probe does not resolve.

    Simulates running from a developer checkout: the compiled-mode
    sibling does not exist, but the dev-mode location (relative to the
    helper module's own location) does. The helper must fall through to
    the dev-mode probe.
    """
    # Arrange: anchor off the helper module to compute the dev-mode probe.
    from src.gui import _icon as icon_module
    from src.gui._icon import resolve_icon_path

    helper_path = Path(icon_module.__file__).resolve()
    expected_dev = helper_path.parents[2] / "packaging" / "velopack" / "icon.ico"
    compiled_probe = Path(sys.executable).parent / "icon.ico"

    # Reports False for the compiled-mode probe, True for the dev-mode probe.
    def fake_exists(path: Path) -> bool:
        if path == compiled_probe:
            return False
        return path == expected_dev

    # Act
    resolved = resolve_icon_path(path_exists=fake_exists)

    # Assert
    assert resolved == expected_dev


def test_resolve_icon_path_raises_when_no_probe_resolves() -> None:
    """When neither probe exists the helper raises FileNotFoundError.

    A missing icon in both probe locations is a contract violation: the
    helper must fail loudly so callers cannot silently swallow it.
    """
    # Arrange
    from src.gui._icon import resolve_icon_path

    def fake_exists(path: Path) -> bool:
        # The argument is intentionally unused; both probes report missing.
        del path
        return False

    # Act / Assert
    with pytest.raises(FileNotFoundError):
        resolve_icon_path(path_exists=fake_exists)
