"""Unit tests for the ``src.build_exe`` Nuitka build orchestration module.

These tests cover the argument parser, the path-anchor constant, the
deterministic Nuitka argv resolver, the subprocess seam, the dry-run path,
the clean path, and exit-code propagation. The real Nuitka binary is never
invoked: production code accepts ``run_nuitka`` / ``remove_tree`` seams that
tests substitute with recorders.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class _RunNuitkaRecorder:
    """Stub seam recording every ``run_nuitka`` invocation.

    Attributes:
        returncode: The integer return code returned by the stub's pretend
            completed process. Tests set this per scenario to verify that
            ``main`` propagates the seam's returncode.
        calls: A list of argv lists, one per invocation. Tests assert on
            the length (invocation count) and on argv content.
    """

    returncode: int = 0
    calls: list[list[str]] = field(default_factory=list[list[str]])

    def __call__(self, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        """Record the call and return a synthetic ``CompletedProcess``.

        Purpose:
            Mimic the ``subprocess.run`` contract just enough that the
            production ``main`` can read ``.returncode`` off the result.

        Args:
            argv: The argv list the production code would pass to Nuitka.

        Returns:
            A synthetic ``CompletedProcess`` with the configured
            ``returncode`` and empty ``stdout``/``stderr``.

        Side Effects:
            Appends a copy of ``argv`` (as a list) to ``self.calls``.
        """
        # Snapshot argv as a fresh list so callers cannot mutate it after.
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(args=list(argv), returncode=self.returncode)


@dataclass
class _RemoveTreeRecorder:
    """Stub seam recording every ``remove_tree`` invocation.

    Attributes:
        calls: A list of ``Path`` objects, one per invocation. Tests
            assert that the path the production code passes equals the
            expected ``REPO_ROOT / dist / nuitka`` location.
    """

    calls: list[pathlib.Path] = field(default_factory=list[pathlib.Path])

    def __call__(self, target: pathlib.Path) -> None:
        """Record the path the production code asked to remove.

        Args:
            target: The directory the production code intends to delete.

        Returns:
            ``None``.

        Side Effects:
            Appends ``target`` to ``self.calls``.
        """
        # Record the exact path so tests can assert equality with the expected target.
        self.calls.append(target)


@dataclass
class _OrderedCallLog:
    """Shared call-log for verifying ``--clean`` happens before ``run_nuitka``.

    Attributes:
        events: A list of marker strings (``"remove_tree"`` /
            ``"run_nuitka"``) in invocation order.
    """

    events: list[str] = field(default_factory=list[str])


def test_build_argument_parser_exposes_dry_run_and_clean_flags() -> None:
    """``--dry-run`` and ``--clean`` are exposed as bool flags defaulting to ``False``.

    Both flags are ``store_true`` with default ``False`` so a bare invocation parses
    cleanly and both can be enabled together on the command line.
    """
    from src.build_exe import build_argument_parser

    parser = build_argument_parser()
    # Defaults: both flags must be False when no args supplied.
    args_default = parser.parse_args([])
    assert args_default.dry_run is False
    assert args_default.clean is False

    # Both flags must flip to True when supplied on the command line.
    args_both = parser.parse_args(["--dry-run", "--clean"])
    assert args_both.dry_run is True
    assert args_both.clean is True


def test_repo_root_resolves_to_project_root() -> None:
    """``REPO_ROOT`` must anchor to the directory containing ``pyproject.toml``."""
    from src.build_exe import REPO_ROOT

    # The expected anchor: the parent of the src/ directory that contains build_exe.py.
    expected = pathlib.Path(__file__).resolve().parents[1]
    assert REPO_ROOT == expected
    # The anchor is verified by locating pyproject.toml at REPO_ROOT.
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_resolve_nuitka_command_contains_required_flags() -> None:
    """The resolved Nuitka argv contains every flag required by AC4.

    AC4 enumerates ``--standalone``, ``--enable-plugin=pyside6``, the two
    ``--include-package=`` inclusions, and an ``--output-dir=`` pointing at
    ``<REPO_ROOT>/dist/nuitka``. Order is not asserted here; ordering is
    pinned by the resolver implementation and covered by the trailing-arg
    test below.
    """
    from src.build_exe import REPO_ROOT, resolve_nuitka_command

    argv = resolve_nuitka_command()

    # The fixed flag tokens are compared as exact string equality. The
    # output-dir argument is compared after Path normalization so the
    # assertion is platform-independent on Windows path separators.
    assert "--standalone" in argv
    assert "--enable-plugin=pyside6" in argv
    assert "--include-package=pandas" in argv
    assert "--include-package=openpyxl" in argv
    expected_output_dir = f"--output-dir={REPO_ROOT / 'dist' / 'nuitka'}"
    assert expected_output_dir in argv


def test_resolve_nuitka_command_contains_icon_flags() -> None:
    """AC1: the resolved Nuitka argv contains the rename + icon flags in order.

    The three required flags are ``--output-filename=MixCalculator.exe``,
    ``--windows-icon-from-ico=<icon-abs-path>``, and
    ``--include-data-file=<icon-abs-path>=icon.ico``. Their values are
    string-compared against the ``REPO_ROOT``-anchored absolute paths so
    Windows separators line up with the production string formation.
    """
    from src.build_exe import REPO_ROOT, resolve_nuitka_command

    argv = resolve_nuitka_command()
    icon_path = REPO_ROOT / "packaging" / "velopack" / "icon.ico"

    expected_flags = [
        "--output-filename=MixCalculator.exe",
        f"--windows-icon-from-ico={icon_path}",
        f"--include-data-file={icon_path}=icon.ico",
    ]
    # Each required flag must appear in the argv. Ordered membership is
    # established by index comparison: the relative order matches the
    # contract documented in the resolver.
    indices: list[int] = []
    for flag in expected_flags:
        assert flag in argv, f"missing flag {flag!r} in argv {argv!r}"
        indices.append(argv.index(flag))
    # Strictly ascending indices verify the documented insertion order.
    assert indices == sorted(indices)


def test_resolve_nuitka_command_ends_with_app_entry() -> None:
    """The trailing positional must be the absolute path to ``src/gui/app.py``."""
    from src.build_exe import REPO_ROOT, resolve_nuitka_command

    argv = resolve_nuitka_command()
    # The final positional argument identifies the compile target for Nuitka.
    assert argv[-1] == str(REPO_ROOT / "src" / "gui" / "app.py")


def test_resolve_nuitka_command_starts_with_python_nuitka_invocation() -> None:
    """The argv must begin with ``[sys.executable, "-m", "nuitka"]``.

    This pins the invocation form to the current interpreter so the Nuitka
    binary used is the one installed in the active Poetry venv, never the
    ambient PATH.
    """
    from src.build_exe import resolve_nuitka_command

    argv = resolve_nuitka_command()
    # The three leading tokens are how the script delegates to Nuitka.
    assert argv[0] == sys.executable
    assert argv[1] == "-m"
    assert argv[2] == "nuitka"


def test_main_dry_run_prints_argv_and_does_not_invoke_seam(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` must print the resolved argv and skip the subprocess seam.

    AC3 requires that the dry-run path prints the fully-resolved Nuitka
    command and returns 0 without invoking Nuitka. The recorder seam
    verifies that no subprocess call is made.
    """
    from src.build_exe import main

    run_recorder = _RunNuitkaRecorder()
    # Inject the recorder so the test verifies the seam contract directly.
    rc = main(["--dry-run"], run_nuitka=run_recorder)

    captured = capsys.readouterr()
    # AC3: every required argv token appears in the printed line so a
    # human or CI consumer can copy-paste the command for inspection.
    assert "--standalone" in captured.out
    assert "--enable-plugin=pyside6" in captured.out
    assert "--include-package=pandas" in captured.out
    assert "--include-package=openpyxl" in captured.out
    assert "--output-dir=" in captured.out
    assert "app.py" in captured.out
    # AC1: the new rename + icon flags must also appear in the printed line so
    # an inspector sees the exe name and the icon-embed wiring at a glance.
    assert "--output-filename=MixCalculator.exe" in captured.out
    assert "--windows-icon-from-ico=" in captured.out
    assert "--include-data-file=" in captured.out
    # The seam must NOT fire on the dry-run path.
    assert len(run_recorder.calls) == 0
    assert rc == 0


def test_main_clean_removes_existing_dist_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,  # type: ignore[unused-ignore]
) -> None:
    """``--clean`` triggers the ``remove_tree`` seam iff the directory exists.

    Sub-case 1: when the synthetic ``dist/nuitka`` directory exists, the
    seam fires exactly once with the expected path.
    Sub-case 2: when the directory does not exist, the seam is never
    invoked.

    The test does NOT create real temp files for production behavior.
    Instead it monkeypatches the production ``Path.is_dir`` lookup so the
    "exists" branch is exercised without touching the filesystem.
    """
    import src.build_exe as build_exe_module
    from src.build_exe import REPO_ROOT, main

    expected_target = REPO_ROOT / "dist" / "nuitka"

    # Sub-case 1: directory exists -> seam fires exactly once with the
    # expected path. Force the production is_dir() guard to True via a
    # patched callable so no real directory is created.
    run_recorder = _RunNuitkaRecorder()
    remove_recorder = _RemoveTreeRecorder()
    monkeypatch.setattr(
        build_exe_module,
        "_dist_nuitka_exists",
        lambda: True,
    )
    rc = main(
        ["--clean", "--dry-run"],
        run_nuitka=run_recorder,
        remove_tree=remove_recorder,
    )
    assert rc == 0
    assert len(remove_recorder.calls) == 1
    assert remove_recorder.calls[0] == expected_target

    # Sub-case 2: directory does not exist -> seam must NOT fire.
    remove_recorder_missing = _RemoveTreeRecorder()
    monkeypatch.setattr(
        build_exe_module,
        "_dist_nuitka_exists",
        lambda: False,
    )
    rc_missing = main(
        ["--clean", "--dry-run"],
        run_nuitka=run_recorder,
        remove_tree=remove_recorder_missing,
    )
    assert rc_missing == 0
    assert len(remove_recorder_missing.calls) == 0


@pytest.mark.parametrize("code", [0, 1, 2, 137])
def test_main_invokes_seam_and_propagates_returncode(code: int) -> None:
    """AC6: the seam's returncode is propagated unchanged through ``main``.

    The parametrization covers success, generic failure, a distinct error
    code, and a POSIX-style termination signal exit code so propagation is
    verified across the full integer range Nuitka could return.
    """
    from src.build_exe import main, resolve_nuitka_command

    run_recorder = _RunNuitkaRecorder(returncode=code)
    rc = main([], run_nuitka=run_recorder)

    expected_argv = resolve_nuitka_command()
    assert rc == code
    assert len(run_recorder.calls) == 1
    assert run_recorder.calls[0] == expected_argv


def test_main_clean_flag_then_invokes_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--clean`` (without ``--dry-run``) removes the tree, then invokes the seam.

    A shared call-log records the order; the ``remove_tree`` event must
    precede the ``run_nuitka`` event so a half-cleaned tree can never be
    fed to the compile step.
    """
    import src.build_exe as build_exe_module
    from src.build_exe import main

    monkeypatch.setattr(build_exe_module, "_dist_nuitka_exists", lambda: True)

    call_log = _OrderedCallLog()

    def fake_run(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        """Record the ordered ``run_nuitka`` event and return a 0 exit."""
        call_log.events.append("run_nuitka")
        return subprocess.CompletedProcess(args=list(argv), returncode=0)

    def fake_remove(target: pathlib.Path) -> None:
        """Record the ordered ``remove_tree`` event."""
        # The argument is unused by the ordering assertion; suppress
        # the unused-argument lint by referencing it explicitly.
        del target
        call_log.events.append("remove_tree")

    rc = main(["--clean"], run_nuitka=fake_run, remove_tree=fake_remove)

    assert rc == 0
    assert call_log.events == ["remove_tree", "run_nuitka"]


def test_main_uses_default_seams_when_unspecified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The defaults bind to ``subprocess.run`` and ``shutil.rmtree``.

    The first assertion confirms that ``main(["--dry-run"])`` does not
    fall through to ``subprocess.run`` (verified by patching the
    module-level ``subprocess.run`` with a recorder that should not fire).
    The second assertion confirms that with ``--clean --dry-run`` and a
    forced "exists" branch, ``shutil.rmtree`` IS invoked exactly once.
    """
    import src.build_exe as build_exe_module
    from src.build_exe import REPO_ROOT, main

    expected_target = REPO_ROOT / "dist" / "nuitka"

    # First assertion: --dry-run alone must not reach subprocess.run.
    subprocess_calls: list[Sequence[str]] = []

    def recording_run(
        argv: Sequence[str], *_: object, **__: object
    ) -> subprocess.CompletedProcess[str]:
        """Record subprocess.run invocations and return a synthetic result."""
        subprocess_calls.append(list(argv))
        return subprocess.CompletedProcess[str](args=list(argv), returncode=0)

    monkeypatch.setattr(build_exe_module.subprocess, "run", recording_run)
    rc_dry = main(["--dry-run"])
    assert rc_dry == 0
    assert subprocess_calls == []

    # Second assertion: --clean --dry-run with forced "exists" must call
    # shutil.rmtree exactly once with the expected target path.
    rmtree_calls: list[pathlib.Path] = []

    def recording_rmtree(target: pathlib.Path, *_: object, **__: object) -> None:
        """Record shutil.rmtree invocations for verification."""
        rmtree_calls.append(pathlib.Path(target))

    monkeypatch.setattr(build_exe_module.shutil, "rmtree", recording_rmtree)
    monkeypatch.setattr(build_exe_module, "_dist_nuitka_exists", lambda: True)
    rc_clean = main(["--clean", "--dry-run"])
    assert rc_clean == 0
    assert rmtree_calls == [expected_target]
