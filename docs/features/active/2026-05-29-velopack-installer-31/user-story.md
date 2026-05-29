# `velopack-installer` — User Story

- Issue: #31
- Owner: drmoisan
- Status: Draft
- Last Updated: 2026-05-29T13-32

## Story Statement

- As a ..., I want ..., so that ...
- As a ..., I want ..., so that ...

## Problem / Why

Issue #29 added `build-exe` which compiles the PySide6 GUI to a 285 MB
standalone folder (`dist/nuitka/app.dist/`). End-user distribution from
that folder is awkward: no installer UX, no Start Menu entry, no clean
uninstall, no auto-update path. The user requirement is to install to a
per-user folder (`%LocalAppData%\<AppName>\`) without admin privileges.

Sideloaded MSIX is unsuitable because the signing certificate must be
trusted in `LocalMachine\TrustedPeople`, which requires admin on each
target machine. Velopack (the maintained successor to
Squirrel.Windows; used by Slack, Discord, GitHub Desktop, VS Code's
User Installer) installs to `%LocalAppData%\<AppId>\` with no UAC, no
admin, and ships built-in delta auto-update from a remote channel
(GitHub Releases supported natively).


## Personas & Scenarios

- Persona: ...
  - who the user is
  - what they care about
  - their constraints
  - their goals and frustrations
  - their context and motivations
- Scenario: ...
  - A concrete, step-by-step narrative that describes how a user accomplishes a goal in a real-world context using the system.
  - who is acting?
  - what triggered the action?
  - what steps do they take?
  - what obstacles or decisions occur?
  - what outcome do they expect?


## Acceptance Criteria

- [ ] `poetry run build-velopack --dry-run` prints the resolved `vpk pack`
- [ ] argv to stdout and exits 0 without invoking `vpk`.
- [ ] `poetry run build-velopack` produces a working
- [ ] `dist/velopack/<AppName>-Setup.exe` on a host with `vpk` installed.
- [ ] `poetry run build-velopack --upload` invokes `vpk upload github`
- [ ] with the resolved repo URL when `GITHUB_TOKEN` is present.
- [ ] `poetry run build-velopack --clean` removes `dist/velopack/`
- [ ] before building.
- [ ] Non-zero `vpk` exit codes propagate.
- [ ] Version defaults to `pyproject.toml` `version`.
- [ ] `Initialize-DevEnvironment.ps1` installs `vpk` when absent.
- [ ] Unit-test coverage on `src/build_velopack.py` is >= 85% line and
- [ ] >= 75% branch.
- [ ] File-size cap (500 lines) is satisfied for every new file.
- [ ] Full mandatory toolchain (Black / Ruff / Pyright / Pytest +
- [ ] PoshQC for the PowerShell changes) passes in a single loop.
- [ ] Spec.md documents the SmartScreen warning behavior on first run
- [ ] and tracks code-signing as a follow-up.


## Non-Goals

Call out what is explicitly excluded from this feature.
