"""Unit tests for ``src.build_velopack`` (AC1, AC3-AC9). The real ``vpk``
binary is never invoked: production code accepts ``run_vpk`` and
``remove_tree`` seams that tests substitute with recorders."""

from __future__ import annotations

import pathlib
import subprocess
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class _RunVpkRecorder:
    """Stub seam recording every ``run_vpk`` invocation.

    Attributes:
        returncode: Returncode returned by the synthetic CompletedProcess.
        calls: Argv list per invocation; tests assert length and content.
    """

    returncode: int = 0
    calls: list[list[str]] = field(default_factory=list[list[str]])

    def __call__(self, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        """Record call and return a synthetic CompletedProcess."""
        # Snapshot argv as a fresh list so callers cannot mutate it after.
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(args=list(argv), returncode=self.returncode)


@dataclass
class _RemoveTreeRecorder:
    """Stub seam recording every ``remove_tree`` invocation."""

    calls: list[pathlib.Path] = field(default_factory=list[pathlib.Path])

    def __call__(self, target: pathlib.Path) -> None:
        """Record the removal target path."""
        self.calls.append(target)


@dataclass
class _OrderedCallLog:
    """Shared call-log verifying invocation ordering across seams."""

    events: list[str] = field(default_factory=list[str])


# ---------------------------------------------------------------------------
# Phase 1: argparse contract, REPO_ROOT, version resolution, pack argv
# ---------------------------------------------------------------------------


def test_build_argument_parser_exposes_required_flags() -> None:
    """AC1: --dry-run / --clean / --upload bool; --version and --release-dir value."""
    from src.build_velopack import build_argument_parser

    parser = build_argument_parser()
    # Defaults: every bool flag is False; value flags are None.
    args_default = parser.parse_args([])
    assert args_default.dry_run is False
    assert args_default.clean is False
    assert args_default.upload is False
    assert args_default.version is None
    assert args_default.release_dir is None

    # All flags flip / accept values when supplied.
    args_all = parser.parse_args(
        ["--dry-run", "--clean", "--upload", "--version", "1.2.3", "--release-dir", "x"]
    )
    assert args_all.dry_run is True
    assert args_all.clean is True
    assert args_all.upload is True
    assert args_all.version == "1.2.3"
    assert args_all.release_dir == "x"


def test_repo_root_resolves_to_project_root() -> None:
    """REPO_ROOT must anchor to the directory containing pyproject.toml."""
    from src.build_velopack import REPO_ROOT

    expected = pathlib.Path(__file__).resolve().parents[1]
    assert REPO_ROOT == expected
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_validate_semver2_accepts_canonical_versions() -> None:
    """AC9: canonical SemVer2 inputs (base, pre-release, metadata) must not raise."""
    from src.build_velopack import validate_semver2

    validate_semver2("0.1.0")
    validate_semver2("1.2.3-rc.1")
    validate_semver2("1.0.0+build.23")
    validate_semver2("1.0.0-build.23+metadata")


@pytest.mark.parametrize(
    "bad",
    [
        "1.0.0.0",  # Four-part — explicit Velopack rejection (research Q6).
        "1.0",  # Two-part.
        "v1.0.0",  # Leading 'v' tag prefix is not a version.
        "",  # Empty.
        "abc",  # Non-numeric.
    ],
)
def test_validate_semver2_rejects_invalid_versions(bad: str) -> None:
    """AC9: every non-SemVer2 input raises ValueError."""
    from src.build_velopack import validate_semver2

    with pytest.raises(ValueError):
        validate_semver2(bad)


def test_resolve_version_defaults_to_pyproject(tmp_path: pathlib.Path) -> None:
    """When override is None the function returns tool.poetry.version."""
    from src.build_velopack import resolve_version

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "test"\nversion = "9.8.7"\n', encoding="utf-8"
    )
    assert resolve_version(pyproject, None) == "9.8.7"


def test_resolve_version_honors_override(tmp_path: pathlib.Path) -> None:
    """AC9: a valid override replaces the pyproject value."""
    from src.build_velopack import resolve_version

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "test"\nversion = "9.8.7"\n', encoding="utf-8"
    )
    assert resolve_version(pyproject, "0.2.0-rc.1") == "0.2.0-rc.1"


def test_resolve_version_rejects_invalid_override(tmp_path: pathlib.Path) -> None:
    """AC9: a malformed override (including four-part) raises ValueError."""
    from src.build_velopack import resolve_version

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "test"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    with pytest.raises(ValueError):
        resolve_version(pyproject, "1.0.0.0")


def test_resolve_pack_command_contains_required_argv() -> None:
    """AC4: the resolved vpk pack argv contains every documented flag/value pair."""
    from src.build_velopack import REPO_ROOT, resolve_pack_command

    release_dir = REPO_ROOT / "dist" / "velopack"
    argv = resolve_pack_command("0.1.0", release_dir)

    assert argv[0] == "vpk"
    assert argv[1] == "pack"

    # Each documented flag must appear once, immediately followed by its value.
    expected_pairs = [
        ("--packId", "mix-calculator"),
        ("--packVersion", "0.1.0"),
        ("--packDir", str(REPO_ROOT / "dist" / "nuitka" / "app.dist")),
        ("--mainExe", "app.exe"),
        ("--packTitle", "Mix Calculator"),
        ("--packAuthors", "Dan Moisan"),
        ("--outputDir", str(release_dir)),
        ("--icon", str(REPO_ROOT / "packaging" / "velopack" / "icon.ico")),
        ("--channel", "win"),
    ]
    for flag, value in expected_pairs:
        assert flag in argv, f"missing flag {flag!r} in argv {argv!r}"
        idx = argv.index(flag)
        assert (
            argv[idx + 1] == value
        ), f"flag {flag!r} not followed by {value!r}; got {argv[idx + 1]!r}"


# ---------------------------------------------------------------------------
# Phase 2: dry-run, clean, pre-flight, seam orchestration
# ---------------------------------------------------------------------------


def test_main_dry_run_prints_argv_and_does_not_invoke_seam(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC3: dry-run prints resolved vpk pack argv and skips the seam."""
    from src.build_velopack import main

    run_recorder = _RunVpkRecorder()
    rc = main(["--dry-run"], run_vpk=run_recorder)

    captured = capsys.readouterr()
    # Every required argv token appears in the printed line.
    for token in ("vpk", "pack", "--packId", "mix-calculator", "--channel", "win"):
        assert token in captured.out
    assert len(run_recorder.calls) == 0
    assert rc == 0


def test_main_clean_removes_dist_velopack(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC6: --clean triggers remove_tree iff dist/velopack exists."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import REPO_ROOT, main

    expected_target = REPO_ROOT / "dist" / "velopack"

    # Sub-case 1: directory exists -> seam fires exactly once.
    run_recorder = _RunVpkRecorder()
    remove_recorder = _RemoveTreeRecorder()
    monkeypatch.setattr(build_velopack_module, "_dist_velopack_exists", lambda: True)
    rc = main(
        ["--clean", "--dry-run"], run_vpk=run_recorder, remove_tree=remove_recorder
    )
    assert rc == 0
    assert len(remove_recorder.calls) == 1
    assert remove_recorder.calls[0] == expected_target

    # Sub-case 2: directory does not exist -> seam must NOT fire.
    remove_recorder_missing = _RemoveTreeRecorder()
    monkeypatch.setattr(build_velopack_module, "_dist_velopack_exists", lambda: False)
    rc_missing = main(
        ["--clean", "--dry-run"],
        run_vpk=run_recorder,
        remove_tree=remove_recorder_missing,
    )
    assert rc_missing == 0
    assert len(remove_recorder_missing.calls) == 0


@pytest.mark.parametrize("code", [0, 1, 2, 137])
def test_main_propagates_seam_returncode(
    code: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC5: the vpk seam's returncode propagates unchanged through main."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)

    run_recorder = _RunVpkRecorder(returncode=code)
    rc = main([], run_vpk=run_recorder)

    assert rc == code
    assert len(run_recorder.calls) == 1
    assert run_recorder.calls[0][0] == "vpk"


def test_main_clean_then_invokes_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    """--clean (without --dry-run) removes the tree, then invokes the seam."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_dist_velopack_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)

    call_log = _OrderedCallLog()

    def fake_run(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        """Record the ordered run_vpk event and return 0 exit."""
        call_log.events.append("run_vpk")
        return subprocess.CompletedProcess(args=list(argv), returncode=0)

    def fake_remove(target: pathlib.Path) -> None:
        """Record the ordered remove_tree event."""
        del target  # Argument unused by the ordering assertion.
        call_log.events.append("remove_tree")

    rc = main(["--clean"], run_vpk=fake_run, remove_tree=fake_remove)

    assert rc == 0
    assert call_log.events == ["remove_tree", "run_vpk"]


def test_main_exits_two_when_app_exe_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """When dist/nuitka/app.dist/app.exe is absent, main exits 2."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: False)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)

    run_recorder = _RunVpkRecorder()
    rc = main([], run_vpk=run_recorder)
    captured = capsys.readouterr()

    assert rc == 2
    assert "build-exe" in captured.err
    assert len(run_recorder.calls) == 0


def test_main_exits_two_when_icon_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """When packaging/velopack/icon.ico is absent, main exits 2."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: False)

    run_recorder = _RunVpkRecorder()
    rc = main([], run_vpk=run_recorder)
    captured = capsys.readouterr()

    assert rc == 2
    assert "icon" in captured.err.lower()
    assert len(run_recorder.calls) == 0


# ---------------------------------------------------------------------------
# Phase 3: upload command, token redaction, GITHUB_TOKEN validation
# ---------------------------------------------------------------------------


def test_resolve_upload_command_argv_shape() -> None:
    """AC7: vpk upload github argv contains the documented flag/value pairs."""
    from src.build_velopack import resolve_upload_command

    argv = resolve_upload_command(
        "0.1.0",
        "https://github.com/drmoisan/mix-calculator",
        "ghp_test_TOKEN_VALUE_DO_NOT_USE",  # noqa: S106 - test fixture data
    )
    assert argv[:3] == ["vpk", "upload", "github"]

    expected_pairs = [
        ("--repoUrl", "https://github.com/drmoisan/mix-calculator"),
        ("--tag", "v0.1.0"),
        ("--releaseName", "mix-calculator 0.1.0"),
        ("--token", "ghp_test_TOKEN_VALUE_DO_NOT_USE"),
    ]
    for flag, value in expected_pairs:
        assert flag in argv
        idx = argv.index(flag)
        assert argv[idx + 1] == value
    assert "--publish" in argv


def test_redact_token_replaces_token_in_argv() -> None:
    """redact_token replaces every token occurrence with <REDACTED>."""
    from src.build_velopack import redact_token

    token = "ghp_test_TOKEN_VALUE_DO_NOT_USE"  # noqa: S105 - test fixture data
    argv = ["vpk", "upload", "github", "--token", token, "--other", token]
    redacted = redact_token(argv, token)

    # Original argv is unchanged (defensive deep copy).
    assert token in argv
    assert redacted == [
        "vpk",
        "upload",
        "github",
        "--token",
        "<REDACTED>",
        "--other",
        "<REDACTED>",
    ]


def test_upload_without_github_token_exits_two(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC8: --upload with no GITHUB_TOKEN exits 2 before any seam call."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    run_recorder = _RunVpkRecorder()
    rc = main(["--upload"], run_vpk=run_recorder)
    captured = capsys.readouterr()

    assert rc == 2
    assert "GITHUB_TOKEN" in captured.err
    assert len(run_recorder.calls) == 0


def test_upload_with_token_runs_pack_then_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC7: --upload with token invokes the seam twice: pack then upload."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)
    monkeypatch.setenv(
        "GITHUB_TOKEN",
        "ghp_test_TOKEN_VALUE_DO_NOT_USE",  # noqa: S105 - test fixture data
    )

    run_recorder = _RunVpkRecorder(returncode=0)
    rc = main(["--upload"], run_vpk=run_recorder)

    assert rc == 0
    assert len(run_recorder.calls) == 2
    pack_argv, upload_argv = run_recorder.calls
    assert pack_argv[:2] == ["vpk", "pack"]
    assert upload_argv[:3] == ["vpk", "upload", "github"]


def test_upload_skipped_when_pack_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-zero pack returncode suppresses the upload step (AC7 / AC5)."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)
    monkeypatch.setenv(
        "GITHUB_TOKEN",
        "ghp_test_TOKEN_VALUE_DO_NOT_USE",  # noqa: S105 - test fixture data
    )

    run_recorder = _RunVpkRecorder(returncode=1)
    rc = main(["--upload"], run_vpk=run_recorder)

    assert rc == 1
    assert len(run_recorder.calls) == 1
    assert run_recorder.calls[0][:2] == ["vpk", "pack"]


def test_main_rejects_invalid_version_before_any_seam_call(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC9: a four-part --version exits 2 before any seam call."""
    import src.build_velopack as build_velopack_module
    from src.build_velopack import main

    monkeypatch.setattr(build_velopack_module, "_app_exe_exists", lambda: True)
    monkeypatch.setattr(build_velopack_module, "_icon_exists", lambda: True)

    run_recorder = _RunVpkRecorder()
    rc = main(["--version", "1.0.0.0"], run_vpk=run_recorder)
    captured = capsys.readouterr()

    assert rc == 2
    assert len(run_recorder.calls) == 0
    assert "1.0.0.0" in captured.err or "version" in captured.err.lower()


# ---------------------------------------------------------------------------
# Coverage: defensive guards and real predicate seams
# ---------------------------------------------------------------------------


def test_redact_token_passes_through_when_token_empty() -> None:
    """redact_token with empty token returns a copy unchanged."""
    from src.build_velopack import redact_token

    argv = ["vpk", "upload", "github", "--token", ""]
    result = redact_token(argv, "")
    assert result == argv
    assert result is not argv


def test_resolve_version_rejects_non_string_pyproject_value(
    tmp_path: pathlib.Path,
) -> None:
    """A non-string tool.poetry.version raises ValueError."""
    from src.build_velopack import resolve_version

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "test"\nversion = 123\n', encoding="utf-8"
    )
    with pytest.raises(ValueError):
        resolve_version(pyproject, None)


def test_real_predicate_seams_return_bool() -> None:
    """The real predicate seams return bool from Path.is_dir / Path.is_file.

    Uses getattr so Pyright's private-symbol-access check is satisfied.
    """
    import src.build_velopack as build_velopack_module

    for predicate_name in (
        "_dist_velopack_exists",
        "_app_exe_exists",
        "_icon_exists",
    ):
        predicate = getattr(build_velopack_module, predicate_name)
        assert isinstance(predicate(), bool)
