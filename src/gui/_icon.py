"""Application-icon path resolution helper.

Purpose:
    Resolve the absolute filesystem path of the application icon
    (``icon.ico``) used by ``QApplication.setWindowIcon`` for the title
    bar, taskbar, and Alt-Tab preview, independently of any Qt runtime
    state. The helper is constructor-free, depends only on the standard
    library, and accepts a ``path_exists`` callable so unit tests can
    drive every probe branch deterministically.

Responsibilities:
    * Probe the compiled-mode location first
      (``Path(sys.executable).parent / "icon.ico"``), which matches the
      Nuitka ``--include-data-file=...icon.ico=icon.ico`` destination at
      the standalone tree root.
    * Fall back to the dev-mode location
      (``Path(__file__).resolve().parents[2] / "packaging" / "velopack"
      / "icon.ico"``) so the running GUI finds the committed icon when
      developers launch ``poetry run mix-pipeline-gui`` without a
      Nuitka-compiled exe.
    * Raise :class:`FileNotFoundError` naming both probed locations when
      neither resolves so callers cannot silently swallow a missing
      asset.

Usage:
    ``icon_path = resolve_icon_path()`` returns a :class:`pathlib.Path`.
    Tests pass ``path_exists=fake_exists`` to drive each probe branch.

Side Effects:
    None. The helper reads only ``sys.executable`` and the
    ``path_exists`` callable; it does not touch the filesystem unless
    the default callable (``Path.is_file``) is in use.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def _default_path_exists(path: Path) -> bool:
    """Return whether ``path`` is an existing regular file.

    Purpose:
        Provide the production default for the ``path_exists`` seam so
        the helper has no required arguments outside of tests.

    Args:
        path: The candidate filesystem path.

    Returns:
        ``True`` when ``path`` is an existing regular file, ``False``
        otherwise.

    Side Effects:
        Performs a single ``stat`` call against the underlying filesystem.
    """
    return path.is_file()


def resolve_icon_path(
    *,
    path_exists: Callable[[Path], bool] | None = None,
) -> Path:
    """Resolve the application icon path for runtime use.

    Purpose:
        Return the absolute path of the application icon by probing the
        compiled-mode location first and the dev-mode location as a
        fallback. The first probe whose ``path_exists`` callable reports
        ``True`` is returned.

    Args:
        path_exists: Optional callable used to test each candidate path.
            Defaults to :func:`_default_path_exists` (a thin wrapper
            around :meth:`pathlib.Path.is_file`). Unit tests inject a
            recorder so each branch is exercised deterministically
            without filesystem dependencies.

    Returns:
        A :class:`pathlib.Path` pointing to the icon file. The path is
        either the compiled-mode probe
        (``Path(sys.executable).parent / "icon.ico"``) or the dev-mode
        probe (``<repo>/packaging/velopack/icon.ico``).

    Raises:
        FileNotFoundError: When neither probe resolves. The exception
            message names both probed paths so the caller can diagnose
            the missing asset.

    Side Effects:
        None beyond the optional filesystem ``stat`` call inside the
        default ``path_exists`` callable.
    """
    exists = path_exists if path_exists is not None else _default_path_exists

    # The compiled-mode probe targets the Nuitka standalone tree root
    # where ``--include-data-file=...icon.ico=icon.ico`` lands the icon
    # alongside the compiled executable.
    compiled_probe = Path(sys.executable).parent / "icon.ico"

    # The dev-mode probe targets the icon committed under
    # ``packaging/velopack/`` relative to this helper module so
    # ``poetry run mix-pipeline-gui`` finds the icon without requiring a
    # Nuitka build.
    dev_probe = (
        Path(__file__).resolve().parents[2] / "packaging" / "velopack" / "icon.ico"
    )

    # Decision-logic: probe compiled-mode first because in a deployed
    # build the dev-mode path does not exist; the dev-mode probe is the
    # fallback for developer launches.
    for candidate in (compiled_probe, dev_probe):
        if exists(candidate):
            return candidate

    raise FileNotFoundError(
        f"Application icon not found. Probed compiled-mode path "
        f"{compiled_probe!s} and dev-mode path {dev_probe!s}."
    )
