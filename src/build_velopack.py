"""Pack the Nuitka standalone build into a Velopack Windows installer.

Provides a reproducible, flag-stable invocation of the Velopack CLI
(``vpk``) wrapping ``dist/nuitka/app.dist/`` into the Velopack artifacts
(``mix-calculator-Setup.exe``, ``mix-calculator-<version>-full.nupkg``,
``releases.win.json``), and optionally publishing the bundle to GitHub
Releases.

Surface:
    * ``build_argument_parser`` returns the AC1 argparse parser.
    * ``validate_semver2`` raises ``ValueError`` on non-SemVer2 inputs
      including four-part versions (per Velopack constraint, AC9).
    * ``resolve_version`` reads ``tool.poetry.version`` from
      ``pyproject.toml`` or honors the ``--version`` override.
    * ``resolve_pack_command`` returns the deterministic ``vpk pack``
      argv (AC4).
    * ``resolve_upload_command`` returns the ``vpk upload github`` argv
      (AC7).
    * ``redact_token`` returns a copy of an argv with the GitHub token
      replaced by ``"<REDACTED>"`` for safe logging.
    * ``main`` is the Poetry script entry point. Subprocess and rmtree
      calls flow through injected seams (``run_vpk``, ``remove_tree``).

Tier: T4-Scaffolding. The real ``vpk`` binary is never invoked from
unit tests because production code accepts seams.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

# REPO_ROOT is anchored off this module's location so the resolver never
# depends on the current working directory. ``parents[1]`` reflects the
# ``src/build_velopack.py`` layout: parents[1] is the repo root.
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

# Hardcoded because the script is repo-specific; matches the verified
# remote URL recorded in the research artifact (Q3).
_REPO_URL: Final[str] = "https://github.com/drmoisan/mix-calculator"

# SemVer2 spec (https://semver.org/), restricted to three numeric
# components plus optional pre-release and build-metadata. The anchored
# ^...$ form rejects Velopack-forbidden four-part versions (research Q6).
_SEMVER2_RE: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


def build_argument_parser() -> argparse.ArgumentParser:
    """Return the AC1 argparse parser.

    The parser exposes ``--dry-run`` / ``--clean`` / ``--upload`` as
    boolean switches (default ``False``), ``--version`` as a SemVer2
    override (default ``None``, falls back to the pyproject value), and
    ``--release-dir`` as an output-directory override (default ``None``,
    falls back to ``REPO_ROOT/dist/velopack``).

    Returns:
        A configured ``argparse.ArgumentParser`` ready for ``parse_args``.
    """
    parser = argparse.ArgumentParser(
        prog="build-velopack",
        description=(
            "Pack the Nuitka standalone build into a Velopack Windows "
            "installer, and optionally upload the release to GitHub."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the resolved vpk command and exit without invoking vpk.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Remove the existing dist/velopack tree before packing.",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        default=False,
        help=(
            "After a successful pack, publish the artifacts to GitHub "
            "Releases. Requires the GITHUB_TOKEN environment variable."
        ),
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help=(
            "Override the SemVer2 version string. Defaults to "
            "tool.poetry.version in pyproject.toml."
        ),
    )
    parser.add_argument(
        "--release-dir",
        dest="release_dir",
        type=str,
        default=None,
        help=(
            "Override the output directory for Velopack artifacts. "
            "Defaults to <REPO_ROOT>/dist/velopack."
        ),
    )
    return parser


def validate_semver2(version: str) -> None:
    """Raise ``ValueError`` when ``version`` is not Velopack-acceptable SemVer2.

    Args:
        version: Candidate version string; no whitespace, no ``v`` prefix.

    Raises:
        ValueError: Includes the offending input. Four-part versions
            (e.g., ``1.0.0.0``) are explicitly rejected per Velopack.
    """
    if not _SEMVER2_RE.match(version):
        raise ValueError(
            f"Invalid SemVer2 version: {version!r}. Velopack requires "
            f"MAJOR.MINOR.PATCH[-prerelease][+buildmeta]; four-part "
            f"versions (e.g., 1.0.0.0) are rejected."
        )


def resolve_version(pyproject_path: Path, override: str | None) -> str:
    """Resolve the build version from ``pyproject.toml`` or an override.

    The override path skips the pyproject read entirely; the validator
    gates both paths so a malformed value cannot reach the seam.

    Args:
        pyproject_path: Path to ``pyproject.toml`` (read via ``tomllib``).
        override: Optional override; when non-``None`` replaces pyproject.

    Returns:
        The resolved SemVer2 version string.

    Raises:
        ValueError: When the resolved version is not valid SemVer2 or
            when ``tool.poetry.version`` is not a string.
        KeyError: When ``tool.poetry.version`` is absent.
    """
    if override is not None:
        validate_semver2(override)
        return override

    # tomllib requires a binary stream.
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    version_value = data["tool"]["poetry"]["version"]
    if not isinstance(version_value, str):
        raise ValueError(
            f"tool.poetry.version in {pyproject_path} is not a string: "
            f"{version_value!r}"
        )
    validate_semver2(version_value)
    return version_value


def resolve_pack_command(version: str, release_dir: Path) -> list[str]:
    """Return the deterministic AC4 ``vpk pack`` argv.

    The argv encodes the documented packId / packTitle / packAuthors /
    channel and anchors path arguments off ``REPO_ROOT``. The caller is
    responsible for SemVer2 validation; this function does not re-validate.

    Args:
        version: A pre-validated SemVer2 version string.
        release_dir: The destination directory for Velopack artifacts.

    Returns:
        The fully-resolved argv as a list of strings.
    """
    # The argv order is part of the contract: tool, command, then the AC4
    # flag/value pairs. Path values are stringified Path objects so the
    # assertion side compares against platform-correct separators on Windows.
    return [
        "vpk",
        "pack",
        "--packId",
        "mix-calculator",
        "--packVersion",
        version,
        "--packDir",
        str(REPO_ROOT / "dist" / "nuitka" / "app.dist"),
        "--mainExe",
        "app.exe",
        "--packTitle",
        "Mix Calculator",
        "--packAuthors",
        "Dan Moisan",
        "--outputDir",
        str(release_dir),
        "--icon",
        str(REPO_ROOT / "packaging" / "velopack" / "icon.ico"),
        "--channel",
        "win",
    ]


def resolve_upload_command(version: str, repo_url: str, token: str) -> list[str]:
    """Return the deterministic AC7 ``vpk upload github`` argv.

    Args:
        version: Pre-validated SemVer2 version string.
        repo_url: HTTPS URL of the target repository.
        token: GitHub auth token (caller reads from ``GITHUB_TOKEN``).

    Returns:
        The fully-resolved upload argv as a list of strings.
    """
    # ``--publish`` is a bare switch; the tag is the v-prefixed version per
    # the GitHub Releases convention.
    return [
        "vpk",
        "upload",
        "github",
        "--repoUrl",
        repo_url,
        "--publish",
        "--tag",
        f"v{version}",
        "--releaseName",
        f"mix-calculator {version}",
        "--token",
        token,
    ]


def redact_token(argv: list[str], token: str) -> list[str]:
    """Return a copy of ``argv`` with every ``token`` occurrence redacted.

    Defensive deep-copy redactor so the script can log the upload command
    without leaking the token. The input argv is never mutated. An empty
    ``token`` is passed through unchanged (the loop would otherwise match
    every empty-string element).

    Args:
        argv: The argv list as built by ``resolve_upload_command``.
        token: The exact token string to redact.

    Returns:
        A new list with every element equal to ``token`` replaced by
        ``"<REDACTED>"``.
    """
    if not token:
        return list(argv)
    return ["<REDACTED>" if element == token else element for element in argv]


def _dist_velopack_exists() -> bool:
    """Predicate seam: return whether ``REPO_ROOT/dist/velopack`` exists.

    Tests substitute this seam to exercise both branches of ``--clean``
    without creating real directories.
    """
    return (REPO_ROOT / "dist" / "velopack").is_dir()


def _app_exe_exists() -> bool:
    """Predicate seam: return whether the Nuitka standalone exe exists."""
    return (REPO_ROOT / "dist" / "nuitka" / "app.dist" / "app.exe").is_file()


def _icon_exists() -> bool:
    """Predicate seam: return whether the installer icon exists."""
    return (REPO_ROOT / "packaging" / "velopack" / "icon.ico").is_file()


def main(
    argv: Sequence[str] | None = None,
    *,
    run_vpk: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
    remove_tree: Callable[[Path], None] | None = None,
) -> int:
    """Entry point for the ``build-velopack`` Poetry script.

    Orchestrates: version resolution -> dist cleanup -> dry-run preview ->
    pre-flight checks (``app.exe`` and ``icon.ico``) -> GITHUB_TOKEN
    validation when ``--upload`` -> ``vpk pack`` -> ``vpk upload github``.
    Subprocess and rmtree calls flow through injected seams.

    Args:
        argv: Optional argv to parse. When ``None``, uses ``sys.argv[1:]``.
        run_vpk: Optional seam. Default resolves to ``subprocess.run``
            at call time so tests can patch ``subprocess.run`` directly.
        remove_tree: Optional seam. Default resolves to ``shutil.rmtree``.

    Returns:
        ``0`` on dry-run success; ``2`` for invalid version, missing
        pre-flight input, or missing ``GITHUB_TOKEN`` when ``--upload``.
        Otherwise the ``vpk pack`` returncode (default path) or, when
        ``--upload`` and pack succeeds, the ``vpk upload github``
        returncode. A non-zero pack returncode suppresses upload.
    """
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    # Validate the version up-front so a malformed input fails fast (AC9).
    try:
        version = resolve_version(REPO_ROOT / "pyproject.toml", args.version)
    except ValueError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    # Resolve the release directory: explicit --release-dir overrides the
    # default ``REPO_ROOT/dist/velopack``.
    release_dir = (
        Path(args.release_dir) if args.release_dir else REPO_ROOT / "dist" / "velopack"
    )

    pack_argv = resolve_pack_command(version, release_dir)

    # The clean branch fires before the pack and before the dry-run early-
    # return so a stale tree cannot be fed to the pack step. The is_dir
    # guard makes the branch a no-op when nothing needs to be removed.
    if args.clean and _dist_velopack_exists():
        remover = remove_tree if remove_tree is not None else shutil.rmtree
        remover(REPO_ROOT / "dist" / "velopack")

    # Dry-run branch (AC3): print the resolved argv and exit 0 without
    # invoking the seam or running pre-flight checks.
    if args.dry_run:
        print(shlex.join(pack_argv))
        return 0

    # Pre-flight checks: both ``app.exe`` and ``icon.ico`` must exist on
    # non-dry runs so the seam never receives an invalid input.
    if not _app_exe_exists():
        print(
            "Error: dist/nuitka/app.dist/app.exe is missing. Run "
            "`poetry run build-exe` first to produce the Nuitka "
            "standalone build.",
            file=sys.stderr,
        )
        return 2
    if not _icon_exists():
        print(
            "Error: packaging/velopack/icon.ico is missing. See "
            "packaging/velopack/README.md for the icon contract.",
            file=sys.stderr,
        )
        return 2

    # Upload pre-flight: validate GITHUB_TOKEN BEFORE any seam call so a
    # missing token cannot waste a multi-minute pack invocation (AC8).
    github_token: str | None = None
    if args.upload:
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            print(
                "Error: --upload requires the GITHUB_TOKEN environment "
                "variable to be set (contents: write scope).",
                file=sys.stderr,
            )
            return 2

    # Default pack invocation. Seam default resolves to subprocess.run at
    # call time so tests can patch src.build_velopack.subprocess.run.
    runner = run_vpk if run_vpk is not None else subprocess.run
    _LOG.info("Running vpk pack: %s", shlex.join(pack_argv))
    pack_completed = runner(
        pack_argv
    )  # noqa: S603 - static analysis can't verify runtime validation
    if pack_completed.returncode != 0 or not args.upload:
        # Propagate pack returncode unchanged (AC5). On the upload path,
        # a non-zero pack suppresses the upload step (AC7).
        return pack_completed.returncode

    # Upload branch. The github_token-None guard below is a static-checker
    # narrowing; the args.upload branch always populates the token or
    # returns 2, so reaching that branch is a programmer error.
    if github_token is None:
        raise RuntimeError(
            "Internal error: GITHUB_TOKEN unexpectedly None on upload path."
        )
    upload_argv = resolve_upload_command(version, _REPO_URL, github_token)
    _LOG.info(
        "Running vpk upload github: %s",
        shlex.join(redact_token(upload_argv, github_token)),
    )
    upload_completed = runner(
        upload_argv
    )  # noqa: S603 - static analysis can't verify runtime validation
    return upload_completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
