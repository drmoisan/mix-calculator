# velopack-installer (Issue #31)

- Date captured: 2026-05-29
- Author: Dan Moisan
- Status: Active -> docs/features/active/2026-05-29-velopack-installer-31/
- Issue: #31
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/31
- Last Updated: 2026-05-29
- Work Mode: full-feature

## Summary

Wrap the existing Nuitka standalone build (`dist/nuitka/app.dist/`,
produced by `poetry run build-exe` from issue #29) in a Velopack-based
Windows installer that installs to `%LocalAppData%\mix-calculator\`
without admin privileges and supports built-in delta auto-update via
GitHub Releases.

This work depends on issue #29 being merged (it is — PR #30 merged
2026-05-29). MSVC 14.51.36231 is installed; .NET SDK 10.0.300 is
installed; `vpk` (Velopack CLI) is not yet installed and will be added
to the `Initialize-DevEnvironment.ps1` bootstrap.

The work_mode is `full-feature`, routed via the large path. The AC
source is `spec.md` (per the full-feature convention).

## Environment

- OS: Windows 10/11 (PySide6 distribution target)
- Python: 3.12 - 3.13 (per `pyproject.toml`)
- Nuitka: ^4.1.1 (declared in dev deps; produces `app.dist/` input)
- Velopack CLI: vpk 1.0.1 (current stable, requires .NET 8.0+)
- Velopack Python SDK: velopack 1.0.1 (PyPI; required runtime call)
- .NET SDK: 10.0.300 (already installed; satisfies vpk's .NET 8 requirement)
- C compiler: MSVC 14.51.36231 (already installed; not directly used by Velopack)
- GitHub remote: drmoisan/mix-calculator
- Entry point being wrapped: `src/gui/app.py` -> `dist/nuitka/app.dist/app.exe`

## Scope

In scope:

- New module `src/build_velopack.py` exposing `main()` with the
  CLI surface defined in spec.md.
- New Poetry entry `build-velopack = "src.build_velopack:main"`.
- New runtime dependency `velopack = ">=1.0.1,<2.0"` in
  `[tool.poetry.dependencies]`.
- Source modification to `src/gui/app.py:main()` to add the
  required `velopack.App().run()` bootstrap call as the first
  statement.
- Test modifications to `tests/gui/test_app_composition.py` to
  patch the Velopack bootstrap and assert call ordering.
- New test module `tests/test_build_velopack.py` covering AC1-AC9
  and AC15-AC16.
- PowerShell modifications to
  `scripts/dev-tools/Initialize-DevEnvironment.ps1` and
  `scripts/dev-tools/DevEnvironment.psm1` to add `vpk` as the
  fifth dev-environment requirement.
- Pester test additions/modifications under `tests/scripts/dev-tools/`
  covering the new requirement.
- New asset `packaging/velopack/icon.ico` (placeholder 256x256 ICO).
- New doc `packaging/velopack/README.md`.
- Config edits: `pyproject.toml`, `quality-tiers.yml` (classifies
  `src/build_velopack.py` as T4).

Out of scope (tracked as follow-ups):

- Code signing of `Setup.exe` and the bundled executables (no cert
  available).
- In-app update-check UI (`UpdateManager.check_for_updates` flow,
  Help -> Check for Updates menu entry).
- CI workflow that builds and uploads on tag push.
- Replacement of the placeholder icon with a designed icon.
- Per-machine MSI installer variant (requires WiX 5; not the user
  requirement).

## Acceptance Criteria

The binding AC set for full-feature mode lives in
[spec.md](spec.md) as AC1 through AC17. The issue body
summarizes the AC headings here for cross-reference:

- [x] AC1: `src/build_velopack.py` with argparse CLI.
- [x] AC2: `pyproject.toml` entry + `velopack` runtime dep.
- [x] AC3: `--dry-run` prints argv and exits 0.
- [x] AC4: Resolved `vpk pack` argv has the expected shape.
- [x] AC5: Non-zero seam exit code propagates.
- [x] AC6: `--clean` removes `dist/velopack/`.
- [x] AC7: `--upload` resolves to the expected `vpk upload github`
      argv with token redacted in log output.
- [x] AC8: `--upload` without `GITHUB_TOKEN` exits 2 with clear
      message.
- [x] AC9: Version defaults to `pyproject.toml`; `--version` overrides;
      invalid SemVer2 rejected.
- [x] AC10: `src/gui/app.py:main()` calls `velopack.App().run()` first.
- [x] AC11: Bootstrap installs `vpk` as the fifth requirement.
- [x] AC12: `packaging/velopack/icon.ico` is a valid ICO container.
- [x] AC13: `packaging/velopack/README.md` documents the packaging
      conventions and token permission.
- [x] AC14: `quality-tiers.yml` classifies the new module as T4.
- [x] AC15: Unit-test coverage >= 85% line / >= 75% branch on the
      new module.
- [x] AC16: 500-line cap satisfied for every new file.
- [x] AC17: Full mandatory toolchain green in a single loop; no new
      suppressions beyond the pre-authorized `# noqa: S603`.

## Test Strategy

- Unit tests only for the Python module. No integration test invokes
  the real `vpk` binary because (a) `vpk` is a dev-machine tool, not
  a runtime dep of the test suite, and (b) the only useful integration
  test (a full pack + install on a clean machine) is multi-minute and
  environment-gated.
- The subprocess seam is the test surface; tests assert argv shape,
  invocation count, and exit-code propagation.
- PowerShell Pester tests cover the bootstrap's vpk requirement path
  using the existing wrapper-seam pattern (`Invoke-DotnetExe`).
- GUI test modification covers the call-ordering invariant added in
  `src/gui/app.py:main()`.

## Reference Artifact

- Research findings:
  [artifacts/research/2026-05-29-velopack-installer-landscape.md](../../../../artifacts/research/2026-05-29-velopack-installer-landscape.md)
- Spec:
  [spec.md](spec.md) (AC source)
- User story:
  [user-story.md](user-story.md)

## Out-of-Scope Follow-ups (tracked elsewhere if needed)

- Code signing (separate PR once a certificate is in hand).
- In-app update-check UI.
- CI workflow.
- Designed icon.
- Multi-channel publishing.
