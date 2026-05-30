"""Compile ``mix-pipeline-gui`` into a standalone Windows ``.exe`` using Nuitka.

Purpose:
    Provide a reproducible, flag-stable invocation of Nuitka so end-user
    distribution of the GUI does not drift across developers or CI runs.
    The script does NOT compile the CLI entry points (``normalize-le``,
    ``load-aop``); only ``src/gui/app.py`` is compiled.

Responsibilities:
    * Build the deterministic Nuitka argv list (``resolve_nuitka_command``).
    * Parse ``--dry-run`` / ``--clean`` flags (``build_argument_parser``).
    * Orchestrate the optional ``dist/nuitka`` cleanup, the dry-run preview,
      and the actual Nuitka invocation via an injected subprocess seam.

Usage:
    Invoked via the Poetry entry point ``build-exe`` (declared in
    ``pyproject.toml``). The seams ``run_nuitka`` and ``remove_tree`` allow
    tests to substitute recorders so the real Nuitka binary is never
    invoked from unit tests.

Side Effects:
    On the non-dry path, ``main`` invokes the Nuitka subprocess (a multi-
    minute C compile via MSVC) and writes the standalone build into
    ``dist/nuitka/`` at the repository root. On ``--clean`` the existing
    ``dist/nuitka/`` directory is removed before building.
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

# The repository root, anchored deterministically off this module's location
# so the resolver never depends on the current working directory. The
# ``parents[1]`` index reflects the ``src/build_exe.py`` layout: parents[0]
# is ``src/``, parents[1] is the repo root containing ``pyproject.toml``.
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

# Name of the compiled Windows executable Nuitka emits. The constant is
# referenced by ``src.build_velopack.resolve_pack_command`` so the Velopack
# ``--mainExe`` value stays in sync with the Nuitka ``--output-filename``.
EXE_NAME: Final[str] = "MixCalculator.exe"


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser exposing ``--dry-run`` and ``--clean``.

    Purpose:
        Return an ``argparse.ArgumentParser`` whose only two flags are
        ``--dry-run`` (print the resolved argv and exit 0 without running
        Nuitka) and ``--clean`` (delete the existing ``dist/nuitka`` tree
        before building). Both default to ``False``.

    Returns:
        A configured ``argparse.ArgumentParser`` ready for ``parse_args``.

    Side Effects:
        ``None``.
    """
    parser = argparse.ArgumentParser(
        prog="build-exe",
        description=(
            "Compile the mix-pipeline-gui PySide6 application into a "
            "standalone Windows .exe using Nuitka."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the resolved Nuitka command and exit without invoking Nuitka.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Remove the existing dist/nuitka tree before building.",
    )
    return parser


def resolve_nuitka_command() -> list[str]:
    """Return the deterministic Nuitka argv used to compile the GUI.

    Purpose:
        Centralize the Nuitka flag set so the invocation cannot drift across
        developers or CI runs. The argv binds Nuitka to the current Python
        interpreter, enables the PySide6 plug-in, explicitly includes the
        pandas and openpyxl packages (rather than relying on module-graph
        auto-detection), pins the output tree to ``<REPO_ROOT>/dist/nuitka``,
        sets the output executable name to :data:`EXE_NAME`
        (``MixCalculator.exe``), embeds the Windows ICO into the executable
        via ``--windows-icon-from-ico``, bundles the same ICO into the
        standalone tree root via
        ``--include-data-file=<icon-abs-path>=icon.ico`` so the running GUI
        can resolve it at runtime, and points Nuitka at ``src/gui/app.py``
        as the compile entry point.

    Returns:
        The fully-resolved argv as a list of strings, in the exact order
        Nuitka receives them. The first three elements are always
        ``[sys.executable, "-m", "nuitka"]`` so the resolver delegates to
        the Nuitka installed in the active interpreter rather than the
        ambient PATH.

    Side Effects:
        ``None``.
    """
    # The argv order is part of the function's contract. The leading
    # python+m+nuitka triple delegates to the active interpreter; the
    # flags follow in the order documented in the issue acceptance
    # criteria; the trailing positional names the compile target. The
    # icon path is absolute (anchored off REPO_ROOT) so Nuitka receives
    # an unambiguous filesystem location regardless of the working dir.
    icon_path = REPO_ROOT / "packaging" / "velopack" / "icon.ico"
    return [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--enable-plugin=pyside6",
        "--include-package=pandas",
        "--include-package=openpyxl",
        f"--output-dir={REPO_ROOT / 'dist' / 'nuitka'}",
        f"--output-filename={EXE_NAME}",
        f"--windows-icon-from-ico={icon_path}",
        # ``--include-data-file=<src>=<dst>`` semantics: ``<dst>`` is a
        # path RELATIVE to the standalone tree root. ``icon.ico`` places
        # the ICO alongside the compiled executable so the helper
        # ``src.gui._icon.resolve_icon_path`` finds it at runtime via
        # ``Path(sys.executable).parent / "icon.ico"``.
        f"--include-data-file={icon_path}=icon.ico",
        str(REPO_ROOT / "src" / "gui" / "app.py"),
    ]


def _dist_nuitka_exists() -> bool:
    """Return whether the ``dist/nuitka`` output tree currently exists.

    Purpose:
        Indirection seam so unit tests can force the "exists" / "missing"
        branches of the ``--clean`` path without creating real directories
        on disk. Production callers receive the real ``Path.is_dir`` result.

    Returns:
        ``True`` if ``REPO_ROOT/dist/nuitka`` is an existing directory,
        ``False`` otherwise.

    Side Effects:
        ``None``.
    """
    return (REPO_ROOT / "dist" / "nuitka").is_dir()


def main(
    argv: Sequence[str] | None = None,
    *,
    run_nuitka: (
        Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None
    ) = None,
    remove_tree: Callable[[Path], None] | None = None,
) -> int:
    """Entry point for the ``build-exe`` Poetry script.

    Purpose:
        Orchestrate the optional cleanup of ``dist/nuitka``, the dry-run
        preview of the Nuitka argv, and the actual Nuitka invocation. The
        function delegates the subprocess and rmtree calls to injected
        seams so unit tests can substitute recorders.

    Args:
        argv: Optional argv to parse. When ``None``, ``argparse`` reads
            ``sys.argv[1:]`` as usual.
        run_nuitka: Optional callable used to invoke Nuitka. Defaults to
            ``subprocess.run`` (resolved at call time so tests can patch
            ``src.build_exe.subprocess.run``). Must accept the argv list
            and return an object with a ``returncode`` attribute.
        remove_tree: Optional callable used to delete the existing
            ``dist/nuitka`` tree on ``--clean``. Defaults to
            ``shutil.rmtree`` (resolved at call time so tests can patch
            ``src.build_exe.shutil.rmtree``).

    Returns:
        ``0`` on the dry-run path. Otherwise the Nuitka subprocess's
        ``returncode`` propagates unchanged so callers (Poetry, CI) see
        the same exit code Nuitka produced.

    Side Effects:
        On ``--clean``, deletes ``REPO_ROOT/dist/nuitka`` when it exists.
        On the non-dry path, invokes Nuitka via the injected (or default)
        subprocess seam.
    """
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    # The clean branch fires before any other work so a stale or partial
    # tree cannot be fed to the compile step. The is_dir guard makes the
    # branch a no-op when nothing needs to be removed.
    if args.clean and _dist_nuitka_exists():
        remover = remove_tree if remove_tree is not None else shutil.rmtree
        remover(REPO_ROOT / "dist" / "nuitka")

    argv_list = resolve_nuitka_command()

    # The dry-run branch is the AC3 preview: emit a copy-pasteable line
    # via shlex.join and exit 0 without invoking Nuitka.
    if args.dry_run:
        print(shlex.join(argv_list))
        return 0

    # Default seam: subprocess.run propagates Nuitka's returncode (AC6).
    runner = run_nuitka if run_nuitka is not None else subprocess.run
    completed = runner(
        argv_list
    )  # noqa: S603 - static analysis can't verify runtime validation
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
