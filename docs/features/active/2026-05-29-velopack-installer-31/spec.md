# velopack-installer — Spec

- **Issue:** #31
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-29
- **Status:** Draft
- **Version:** 1.0

## Overview

Issue #29 added `build-exe` which compiles the PySide6 GUI to a 285 MB
standalone folder (`dist/nuitka/app.dist/`). End-user distribution from
that folder is awkward: no installer UX, no Start Menu entry, no clean
uninstall, no auto-update path. The user requirement is to install to a
per-user folder (`%LocalAppData%\<AppName>\`) without admin privileges.

Sideloaded MSIX is unsuitable because the signing certificate must be
trusted in `LocalMachine\TrustedPeople`, which requires admin on each
target machine. Velopack (the maintained successor to Squirrel.Windows;
used by Slack, Discord, GitHub Desktop, and VS Code's User Installer)
installs to `%LocalAppData%\<AppId>\` with no UAC and no admin, and
ships built-in delta auto-update from a remote channel (GitHub Releases
supported natively).

All facts in this spec are sourced from the research artifact at
[artifacts/research/2026-05-29-velopack-installer-landscape.md](../../../../artifacts/research/2026-05-29-velopack-installer-landscape.md).

## Behavior

### Build path

1. Add a new Python module `src/build_velopack.py` exposing
   `main(argv: Sequence[str] | None = None) -> int` and registered as
   the Poetry script `build-velopack = "src.build_velopack:main"`.
2. The script reads the package version from `pyproject.toml`
   (`tool.poetry.version`) or accepts `--version <semver>` to override.
   Versions are validated against SemVer2; four-part versions
   (`1.0.0.0`) are rejected per Velopack's documented constraint.
3. The script resolves the `vpk pack` argv deterministically from a
   `REPO_ROOT` anchor (`Path(__file__).resolve().parents[1]`). The argv
   includes:
   - `--packId mix-calculator`
   - `--packVersion <resolved-version>`
   - `--packDir <REPO_ROOT>/dist/nuitka/app.dist`
   - `--mainExe app.exe`
   - `--packTitle "Mix Calculator"`
   - `--packAuthors "Dan Moisan"`
   - `--outputDir <REPO_ROOT>/dist/velopack`
   - `--icon <REPO_ROOT>/packaging/velopack/icon.ico`
   - `--channel win`
4. The script invokes `vpk` via an injected subprocess seam (default
   bound to `subprocess.run`). The seam accepts the argv and returns an
   object with `.returncode`. Tests substitute a recorder.
5. The script's primary modes (selected by flag):
   - `--dry-run`: print the resolved `vpk` argv (via `shlex.join`) and
     exit 0. No subprocess call.
   - `--clean`: recursively delete `dist/velopack/` if it exists, then
     proceed with the pack step. Guarded by an `is_dir` check.
   - default: invoke the seam with the resolved argv. Propagate the
     returncode unchanged.
   - `--upload`: after a successful pack, invoke
     `vpk upload github --repoUrl <derived> --publish --tag v<version> --releaseName "mix-calculator <version>" --token $GITHUB_TOKEN`.
     The token is read from the `GITHUB_TOKEN` environment variable;
     the script logs the command with the token redacted (replaced by
     `<REDACTED>`). The release is published immediately (per
     `--publish`); a draft mode is not exposed in this iteration.
6. The script does NOT build the Nuitka standalone itself. The user
   must run `poetry run build-exe` first. The script verifies
   `dist/nuitka/app.dist/app.exe` exists before invoking `vpk pack`;
   if absent the script exits 2 with a clear message pointing to
   `build-exe`.

### Runtime integration

Velopack requires `velopack.App().run()` as the first call in the
application's entry point. Without it, first-install hooks (Start Menu
shortcut creation, uninstall cleanup) fail. This is a hard runtime
requirement, not an optional optimization.

7. Add `velopack` to the runtime dependencies in `pyproject.toml`
   (`velopack = ">=1.0.1,<2.0"` per PyPI as of 2026-05-29).
8. Modify `src/gui/app.py:main()` to call `velopack.App().run()` as
   the first statement (before logging configuration and Qt
   construction). Tests under `tests/gui/test_app_composition.py`
   that exercise `main` are updated to patch the Velopack bootstrap so
   the call is observable but inert.

In-app update-check UI (the `UpdateManager.check_for_updates` /
`download_updates` / `apply_updates_and_restart` flow) is OUT OF
SCOPE for this PR and is tracked as a follow-up.

### Dev environment bootstrap

9. Extend `scripts/dev-tools/Initialize-DevEnvironment.ps1` and its
   sibling module `scripts/dev-tools/DevEnvironment.psm1` to recognize
   `vpk` as the fifth dev-environment requirement. Detection is
   command-availability via `Test-CommandAvailable -Name 'vpk'`.
   Installation is `dotnet tool install -g vpk`. The PowerShell change
   set follows the existing wrapper-seam pattern
   (`Invoke-DotnetExe -DotnetArgs <string[]>`).
10. Update the corresponding Pester tests under
    `tests/scripts/dev-tools/` to cover the new requirement's
    detection, install, and idempotence paths.

### Distribution artifacts

11. Commit `packaging/velopack/icon.ico` — a placeholder 256x256 ICO
    with a simple "MC" mark on a flat background. The script passes
    this file to `vpk pack --icon`. Multi-size ICO (16, 32, 48, 256 px)
    is recommended; the placeholder may ship single-size and be
    replaced in a follow-up.
12. Commit `packaging/velopack/README.md` describing the `--packId`,
    `--packTitle`, `--packAuthors`, channel name, icon location, and
    how to replace the icon. Includes the GitHub Releases token
    permission requirement (`contents: write`).
13. The script writes its output to `dist/velopack/`. `.gitignore`
    already covers `dist/`; no `.gitignore` edit is needed.

## Inputs / Outputs

**Inputs**

- CLI flags on `build-velopack`: `--dry-run`, `--clean`,
  `--version <semver>`, `--upload`, `--release-dir <path>` (default
  `dist/velopack`).
- Environment variables: `GITHUB_TOKEN` (required when `--upload` is
  set; otherwise ignored).
- Files: `pyproject.toml` (for version resolution),
  `dist/nuitka/app.dist/app.exe` (must exist for non-dry runs),
  `packaging/velopack/icon.ico` (must exist for non-dry runs).

**Outputs (on a successful non-dry, non-upload run)**

- `dist/velopack/mix-calculator-Setup.exe` — the bootstrap installer
  for end users.
- `dist/velopack/mix-calculator-<version>-full.nupkg` — the full
  update package.
- `dist/velopack/mix-calculator-<version>-delta.nupkg` — the delta
  package against the prior release (omitted on the first release).
- `dist/velopack/mix-calculator-Portable.zip` — portable archive for
  users who do not want the installer.
- `dist/velopack/releases.win.json` — channel manifest read by
  `UpdateManager` at runtime.
- `dist/velopack/assets.win.json` — build asset catalog.
- `dist/velopack/RELEASES` — legacy Squirrel-format manifest.

**Outputs (additional, on `--upload`)**

- A published GitHub Release at the resolved tag (e.g. `v0.1.0`),
  with all artifacts above attached and the channel manifest live for
  the `UpdateManager` to consume.

**Config keys and defaults**

| Key | Default | Override |
|---|---|---|
| `packId` | `mix-calculator` | not exposed in this iteration |
| `packTitle` | `Mix Calculator` | not exposed in this iteration |
| `packAuthors` | `Dan Moisan` | not exposed in this iteration |
| `channel` | `win` | not exposed in this iteration |
| `version` | read from `pyproject.toml` `tool.poetry.version` | `--version <semver>` |
| `release-dir` | `dist/velopack` | `--release-dir <path>` |

## API / CLI Surface

```text
poetry run build-velopack [--dry-run] [--clean] [--version <semver>]
                          [--upload] [--release-dir <path>]
```

Example invocations:

- `poetry run build-velopack --dry-run` — print the resolved vpk pack
  argv and exit 0.
- `poetry run build-velopack` — produce
  `dist/velopack/mix-calculator-Setup.exe` and siblings.
- `poetry run build-velopack --clean` — wipe `dist/velopack/` first.
- `poetry run build-velopack --upload` — pack, then publish to GitHub
  Releases at tag `v<version>`.
- `poetry run build-velopack --version 0.2.0-rc.1 --upload` — release
  a pre-release with an explicit SemVer override.

Validation rules:

- Version: must match SemVer2 (`MAJOR.MINOR.PATCH[-prerelease][+buildmeta]`).
  Four-part versions rejected. Invalid versions cause exit 2 before
  any subprocess call.
- `--upload`: requires `GITHUB_TOKEN` in the environment. Absence
  causes exit 2 with a clear message before any subprocess call.
- Pre-flight: `dist/nuitka/app.dist/app.exe` and
  `packaging/velopack/icon.ico` must both exist. Absence causes exit 2.

## Data & State

The build script has no persistent state. Each invocation is
idempotent against a clean `dist/velopack/` (use `--clean`) or against
an existing `dist/velopack/` containing prior packs (Velopack reads
prior `.nupkg` files in `--outputDir` to compute the delta package).

GitHub Releases state IS persistent. `--upload` creates a release at
the resolved tag. GitHub Releases are immutable once published; a
second `--upload` at the same tag fails. The script does not
auto-bump versions, does not delete prior releases, and does not
overwrite existing releases. The user is responsible for choosing the
version.

## Constraints & Risks

- **`vpk` external tool dependency.** `vpk` is a .NET global tool
  installed via `dotnet tool install -g vpk`. The bootstrap script
  installs it; users who skip the bootstrap will see a clear error.
- **Unsigned installer.** No code-signing certificate is available.
  Users will see a SmartScreen "Windows protected your PC" warning on
  first run; the warning resets with each new release executable
  version per Velopack's documented signing posture. Code signing is
  tracked as a follow-up PR.
- **Per-machine install not supported.** Velopack's default
  `Setup.exe` always installs to `%LocalAppData%\<packId>\`. A
  per-machine variant requires a separate MSI build path (WiX 5);
  out of scope.
- **Runtime SDK call is required, not optional.** The
  `velopack.App().run()` call in `src/gui/app.py:main()` is required
  for installer first-run and uninstall flows. Omitting it produces
  an installer that places files but leaves no working Start Menu
  shortcut or uninstall entry.
- **GitHub Releases are immutable.** Re-running `--upload` at the
  same version fails. The script does not retry, delete, or
  overwrite.
- **`build-velopack` does not run `build-exe` automatically.** The
  user must run `build-exe` first. This is intentional: the Nuitka
  compile takes minutes and should be a separate, observable step.

## Implementation Strategy

**Implementation scope**

- New: `src/build_velopack.py`, `tests/test_build_velopack.py`,
  `packaging/velopack/icon.ico`, `packaging/velopack/README.md`.
- Modified: `src/gui/app.py` (`main()` adds Velopack bootstrap line),
  `tests/gui/test_app_composition.py` (patches Velopack bootstrap and
  asserts call ordering),
  `scripts/dev-tools/Initialize-DevEnvironment.ps1`,
  `scripts/dev-tools/DevEnvironment.psm1`, `pyproject.toml`,
  `quality-tiers.yml`. Pester tests under
  `tests/scripts/dev-tools/` updated to cover vpk requirement.

**New classes / functions**

- `src.build_velopack.resolve_version(pyproject_path: Path, override: str | None) -> str`
- `src.build_velopack.validate_semver2(version: str) -> None`
- `src.build_velopack.resolve_pack_command(version: str, release_dir: Path) -> list[str]`
- `src.build_velopack.resolve_upload_command(version: str, repo_url: str, token: str) -> list[str]`
- `src.build_velopack.redact_token(argv: list[str], token: str) -> list[str]`
- `src.build_velopack.main(argv: Sequence[str] | None = None, *, run_vpk: ... | None = None, remove_tree: ... | None = None) -> int`
- PowerShell: `Invoke-DotnetExe` wrapper, `Test-VpkRequirementSatisfied`,
  `Install-VpkRequirement`, and updates to `Get-DevRequirementDefinition`
  and `Test-RequirementPresent`.

**Dependency changes**

- Add `velopack = ">=1.0.1,<2.0"` to `[tool.poetry.dependencies]`
  (runtime, not dev). Rationale: `velopack.App().run()` is invoked at
  runtime by the GUI entry point and must ship in the compiled
  Nuitka binary.

**Logging / telemetry**

- The script writes structured progress to stdout via `logging`
  (INFO level): which mode it is in, which command it is about to
  invoke (with token redacted), and the return code received.

**Rollout plan**

- Single PR ships the full feature.
- No feature flag. The new `build-velopack` script is opt-in by
  invocation. The `velopack.App().run()` call in `main()` is inert
  when the app is not installed via Velopack (per Velopack's
  documented "harmless when unmanaged" semantics) and adds no
  user-visible behavior to dev runs.
- Follow-up PRs (out of scope for this issue): code signing,
  in-app update-check UI, CI workflow that auto-packs and uploads
  on tag push.

## Acceptance Criteria

- [x] AC1: A new Python module `src/build_velopack.py` exists with a
      `main()` function and an `argparse`-based CLI accepting
      `--dry-run`, `--clean`, `--version <semver>`, `--upload`, and
      `--release-dir <path>`.
- [x] AC2: `pyproject.toml` declares the Poetry entry point
      `build-velopack = "src.build_velopack:main"` and adds
      `velopack = ">=1.0.1,<2.0"` under `[tool.poetry.dependencies]`.
- [x] AC3: `poetry run build-velopack --dry-run` prints the
      fully-resolved `vpk pack` argv to stdout and exits 0 without
      invoking the seam.
- [x] AC4: The resolved `vpk pack` argv contains, in order: `vpk`,
      `pack`, `--packId mix-calculator`, `--packVersion <version>`,
      `--packDir <REPO_ROOT>/dist/nuitka/app.dist`,
      `--mainExe app.exe`, `--packTitle "Mix Calculator"`,
      `--packAuthors "Dan Moisan"`,
      `--outputDir <REPO_ROOT>/dist/velopack`,
      `--icon <REPO_ROOT>/packaging/velopack/icon.ico`,
      `--channel win`. Verified by unit tests.
- [x] AC5: `poetry run build-velopack` propagates the seam's
      returncode unchanged. A unit test verifies non-zero propagation.
- [x] AC6: `poetry run build-velopack --clean` removes the
      `dist/velopack/` directory tree before invoking the seam. A
      unit test verifies removal happens on the clean path and is a
      no-op when the directory is absent.
- [x] AC7: `poetry run build-velopack --upload` resolves to an
      `vpk upload github` argv with `--repoUrl https://github.com/drmoisan/mix-calculator`,
      `--publish`, `--tag v<version>`,
      `--releaseName "mix-calculator <version>"`, and
      `--token <GITHUB_TOKEN>`. A unit test verifies argv shape and
      that the logged form of the command has the token replaced by
      `<REDACTED>`.
- [x] AC8: `--upload` without `GITHUB_TOKEN` in the environment exits
      2 before any seam call, with a clear stderr message naming the
      missing variable. A unit test verifies the exit code and
      message.
- [x] AC9: Version resolution defaults to the `tool.poetry.version`
      string in `pyproject.toml`. `--version <semver>` overrides.
      Invalid SemVer2 (including four-part `1.0.0.0`) exits 2 before
      any seam call. Unit tests cover default, override, and rejection.
- [x] AC10: `src/gui/app.py:main()` calls `velopack.App().run()` as
      the first statement, before logging configuration. A unit test
      in `tests/gui/test_app_composition.py` patches `velopack.App`
      and asserts the call happens before `QApplication`
      construction.
- [x] AC11: `scripts/dev-tools/Initialize-DevEnvironment.ps1` and
      `scripts/dev-tools/DevEnvironment.psm1` recognize `vpk` as a
      fifth requirement. Pester tests cover the present, absent, and
      installed paths.
- [x] AC12: `packaging/velopack/icon.ico` is committed; the file is
      a valid Windows ICO container (verifiable via the file's
      `0x00 0x00 0x01 0x00` magic bytes).
- [x] AC13: `packaging/velopack/README.md` documents the packId,
      title, authors, channel, icon location, and replacement
      procedure; references the `contents: write` token permission
      required for `--upload`.
- [x] AC14: `quality-tiers.yml` classifies `src/build_velopack.py`
      as T4 (Scaffolding).
- [x] AC15: Unit-test coverage on `src/build_velopack.py` is
      >= 85% line and >= 75% branch.
- [x] AC16: `src/build_velopack.py` and
      `tests/test_build_velopack.py` are each under 500 lines.
- [x] AC17: Full mandatory toolchain passes in a single loop:
      Black -> Ruff -> Pyright -> Pytest for the Python files;
      PoshQC format -> analyze -> Pester for the PowerShell files.
      No suppressions introduced beyond the pre-authorized
      `# noqa: S603` on the subprocess seam.

## Definition of Done

- [ ] All AC1-AC17 are checked.
- [ ] All three audit artifacts (policy, code, feature) are produced
      by `feature-review` with zero blocking findings.
- [ ] CI required checks at the PR head SHA are SUCCESS.
- [ ] PR body produced via the `pr-author` skill with a matching
      receipt at `artifacts/pr_body_31.receipt.json`.

## Seeded Test Conditions (from potential)

- [ ] argparse contract (`--dry-run`, `--clean`, `--version`,
      `--upload`, `--release-dir`).
- [ ] `vpk pack` argv resolution: all required arguments present in
      the correct order, paths anchored off `REPO_ROOT`.
- [ ] `vpk upload` argv resolution: token redacted from log output,
      repo URL hardcoded to `https://github.com/drmoisan/mix-calculator`
      (matches the verified remote in
      `artifacts/research/2026-05-29-velopack-installer-landscape.md`).
- [ ] Version resolution: defaults from `pyproject.toml`, override via
      `--version`, rejection of malformed SemVer2 strings including
      four-part versions.
- [ ] Subprocess seam invocation: `--dry-run` does not call the seam;
      non-dry path calls it once for `vpk pack`; non-dry + `--upload`
      calls it twice (once for pack, once for upload).
- [ ] Exit-code propagation: non-zero pack code propagates and
      suppresses the upload step.
- [ ] `--clean` removes `dist/velopack/` tree only when it exists.
- [ ] PowerShell: `Initialize-DevEnvironment.ps1` detects `vpk`
      presence, installs when absent, reports the result.
- [ ] GUI: `main()` calls `velopack.App().run()` before
      `QApplication` construction.

## Out-of-Scope Follow-ups

- Code signing of `Setup.exe` and the bundled executables once a
  code-signing certificate (commercial or EV) is available.
- In-app update-check UI (`UpdateManager.check_for_updates` and
  related flow), exposed via a Help -> Check for updates menu entry.
- CI workflow that builds and uploads on tag push.
- Replacement of the placeholder icon with a designed icon.
- Multi-channel publishing (e.g. a `beta` channel in parallel to
  `win`).
