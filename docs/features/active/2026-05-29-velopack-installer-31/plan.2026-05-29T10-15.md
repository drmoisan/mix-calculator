# Atomic Implementation Plan — Velopack Installer (Issue #31)

- Feature: velopack-installer
- Issue: #31
- Feature folder: `docs/features/active/2026-05-29-velopack-installer-31/`
- Work Mode: full-feature
- AC source: `docs/features/active/2026-05-29-velopack-installer-31/spec.md` (AC1–AC17)
- Plan created: 2026-05-29T10-15
- Owner: drmoisan

This plan delivers the full Velopack installer feature: a new Python build orchestration module (`src/build_velopack.py`), corresponding tests, runtime SDK integration in `src/gui/app.py`, PowerShell bootstrap of the `vpk` tool, and the supporting distribution assets. The plan respects the per-batch caps (Python: 3 production + 3 test files per batch; PowerShell: 3 production + 3 test files per batch) and the 500-line file cap. Every phase ends with the toolchain stages (Black/Ruff/Pyright for Python; PoshQC format/analyze for PowerShell) silent on the touched files and with the targeted test set green.

All evidence is written under the canonical evidence root `docs/features/active/2026-05-29-velopack-installer-31/evidence/<kind>/` per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. The plan rejects any non-canonical evidence path supplied by callers.

---

### Phase 0 — Compliance & Baseline Capture

- [x] [P0-T1] Read repository policy files in the canonical order and record the read list at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/phase0-instructions-read.2026-05-29T10-15.md`. Required reads in order: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/powershell.md`, `.claude/rules/tonality.md`, `.claude/rules/benchmark-baselines.md`, `.claude/rules/ci-workflows.md`. Artifact fields: `Timestamp:`, `Policy Order:`, `Files Read:`.

- [x] [P0-T2] Read the feature inputs and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/phase0-feature-inputs-read.2026-05-29T10-15.md`. Required reads: `docs/features/active/2026-05-29-velopack-installer-31/spec.md`, `docs/features/active/2026-05-29-velopack-installer-31/issue.md`, `artifacts/research/2026-05-29-velopack-installer-landscape.md`, `pyproject.toml`, `src/build_exe.py`, `tests/test_build_exe.py`, `src/gui/app.py`, `tests/gui/test_app_composition.py`, `scripts/dev-tools/Initialize-DevEnvironment.ps1`, `scripts/dev-tools/DevEnvironment.psm1`, `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1`, `quality-tiers.yml`. Artifact fields: `Timestamp:`, `Files Read:`.

- [x] [P0-T3] Capture Python format baseline. Run `poetry run black --check .` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/black-check.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (pass/fail status and count of files reformatted, if any).

- [x] [P0-T4] Capture Python lint baseline. Run `poetry run ruff check .` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/ruff-check.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count or "All checks passed").

- [x] [P0-T5] Capture Python type-check baseline. Run `poetry run pyright` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/pyright.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error / warning / information counts).

- [x] [P0-T6] Capture Python test + coverage baseline. Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/pytest-cov.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` containing numeric line and branch coverage totals, total test count, and pass/fail tally.

- [x] [P0-T7] Capture PowerShell format baseline. Invoke `mcp__drm-copilot__run_poshqc_format` (check-only mode) and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/poshqc-format.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (files reformatted count, or zero).

- [x] [P0-T8] Capture PowerShell analyze baseline. Invoke `mcp__drm-copilot__run_poshqc_analyze` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/poshqc-analyze.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (rule violation counts by severity).

- [x] [P0-T9] Capture PowerShell Pester baseline. Invoke `mcp__drm-copilot__run_poshqc_test` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/baseline/pester.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (passed / failed / skipped counts, line and branch coverage).

---

### Phase 1 — Python build module: argparse contract and version/pack resolvers (test-first)

Files touched in this phase:
- New (test): `tests/test_build_velopack.py`
- New (production): `src/build_velopack.py`

This phase introduces the new module skeleton, the argparse CLI surface, the `resolve_version` and `validate_semver2` functions, the `resolve_pack_command` resolver, and the baseline test set covering those resolvers. The subprocess seam is declared but not yet exercised here; the dry-run / clean / upload paths land in Phase 2 and Phase 3.

- [x] [P1-T1] Author the failing test scaffolding in `tests/test_build_velopack.py`. Add the module-docstring, `_RunVpkRecorder` stub seam (signature `(argv: Sequence[str]) -> subprocess.CompletedProcess[str]`), `_RemoveTreeRecorder`, `_OrderedCallLog`, and the test bodies for: (a) argparse exposes `--dry-run`, `--clean`, `--version`, `--upload`, `--release-dir`; (b) `REPO_ROOT` anchors to the directory containing `pyproject.toml`; (c) `validate_semver2` accepts canonical SemVer2 and rejects four-part versions; (d) `resolve_version` defaults to `tool.poetry.version` and honors the `--version` override; (e) `resolve_pack_command` returns the AC4 argv shape with `--packId mix-calculator`, `--packVersion <version>`, `--packDir <REPO_ROOT>/dist/nuitka/app.dist`, `--mainExe app.exe`, `--packTitle "Mix Calculator"`, `--packAuthors "Dan Moisan"`, `--outputDir <REPO_ROOT>/dist/velopack`, `--icon <REPO_ROOT>/packaging/velopack/icon.ico`, `--channel win`. Use docstrings per `.claude/rules/self-explanatory-code-commenting.md`. Acceptance: the file is under 500 lines and is rejected by pytest with `ModuleNotFoundError` for `src.build_velopack` (fail-before evidence captured in P1-T2).

- [x] [P1-T2] Capture the fail-before evidence for Phase 1. Run `poetry run pytest tests/test_build_velopack.py -x` and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/p1-fail-before-pytest.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` confirming the expected `ModuleNotFoundError` for `src.build_velopack`. Tag: `[expect-fail]`. Acceptance: artifact exists; expected failure documented.

- [x] [P1-T3] Author `src/build_velopack.py` with the module docstring, `REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]`, `build_argument_parser()` returning the AC1 argparse parser (flags: `--dry-run`, `--clean`, `--version`, `--upload`, `--release-dir`), `validate_semver2(version: str) -> None` raising `ValueError` on malformed inputs (including four-part), `resolve_version(pyproject_path: Path, override: str | None) -> str` reading `tool.poetry.version` from `pyproject.toml` via `tomllib` and honoring `--version`, and `resolve_pack_command(version: str, release_dir: Path) -> list[str]` returning the AC4 argv. No subprocess seam invocation yet. File must stay under 500 lines.

- [x] [P1-T4] Run the Phase 1 toolchain loop. Execute, in order: `poetry run black src/build_velopack.py tests/test_build_velopack.py`, `poetry run ruff check src/build_velopack.py tests/test_build_velopack.py`, `poetry run pyright src/build_velopack.py tests/test_build_velopack.py`, `poetry run pytest tests/test_build_velopack.py -x`. Restart from Black on any failure or auto-fix. Record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p1-toolchain.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` for each stage. Acceptance: all four stages PASS with EXIT_CODE 0 in a single loop pass.

---

### Phase 2 — Python build module: dry-run, clean, and subprocess seam orchestration

Files touched in this phase:
- Modified (production): `src/build_velopack.py`
- Modified (test): `tests/test_build_velopack.py`

This phase wires the four pack-side execution paths: `--dry-run` (print argv via `shlex.join` and exit 0 without invoking the seam), `--clean` (delete `dist/velopack/` when present and proceed), default (invoke seam and propagate returncode), and the pre-flight check that `dist/nuitka/app.dist/app.exe` and `packaging/velopack/icon.ico` exist before non-dry runs.

- [x] [P2-T1] Extend `tests/test_build_velopack.py` with failing tests for: (a) `--dry-run` prints the resolved `vpk pack` argv (via `shlex.join`) and does not invoke the seam (AC3); (b) `--clean` triggers `remove_tree` exactly once when the directory exists and is a no-op when it does not; (c) default path calls the seam once with the AC4 argv and propagates returncodes 0, 1, 2, 137 (AC5); (d) `--clean` without `--dry-run` removes the tree before invoking the seam (ordering assertion via shared call-log); (e) pre-flight: when `dist/nuitka/app.dist/app.exe` is absent (forced via a seam), `main` exits 2 with a stderr message mentioning `build-exe`; (f) pre-flight: when `packaging/velopack/icon.ico` is absent (forced via a seam), `main` exits 2 with a stderr message mentioning the icon. Use `monkeypatch` and recorder stubs only. Acceptance: file stays under 500 lines; new tests fail because the production behavior is not yet implemented.

- [x] [P2-T2] Capture the fail-before evidence for Phase 2. Run `poetry run pytest tests/test_build_velopack.py -x` and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/p2-fail-before-pytest.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` confirming the new tests fail (failing test names listed). Tag: `[expect-fail]`.

- [x] [P2-T3] Extend `src/build_velopack.py` with: (a) `_pre_flight_paths()` returning a pair of `Path` predicates (`app_exe_exists`, `icon_exists`) so tests can substitute results; (b) `_dist_velopack_exists()` predicate seam; (c) `main(argv, *, run_vpk=None, remove_tree=None) -> int` containing the orchestration: parse args, validate-version-or-exit-2, pre-flight-check-or-exit-2 (skipped on dry-run), optional clean, dry-run branch (print + return 0), and default seam call with `# noqa: S603 - static analysis can't verify runtime validation`. The seam default resolves to `subprocess.run` at call time. The function returns the seam's `.returncode` on the default path. Logging via `logging.getLogger(__name__).info(...)` records mode, argv (token-redacted version not yet introduced), and returncode. Add an `if __name__ == "__main__": raise SystemExit(main())` guard. File must stay under 500 lines.

- [x] [P2-T4] Run the Phase 2 toolchain loop. Execute, in order: `poetry run black src/build_velopack.py tests/test_build_velopack.py`, `poetry run ruff check src/build_velopack.py tests/test_build_velopack.py`, `poetry run pyright src/build_velopack.py tests/test_build_velopack.py`, `poetry run pytest tests/test_build_velopack.py -x`. Restart from Black on any failure or auto-fix. Record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p2-toolchain.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` for each stage. Acceptance: all four stages PASS with EXIT_CODE 0 in a single loop pass.

---

### Phase 3 — Python build module: upload command, token redaction, GITHUB_TOKEN validation

Files touched in this phase:
- Modified (production): `src/build_velopack.py`
- Modified (test): `tests/test_build_velopack.py`

This phase adds the `--upload` path: the `vpk upload github` argv resolver, `GITHUB_TOKEN` environment-variable validation, the log-line token redactor, the orchestration that runs pack first and only invokes upload on a zero-exit pack, and the corresponding tests. No real tokens are embedded; tests use the fixture string `ghp_test_TOKEN_VALUE_DO_NOT_USE` declared with `# noqa: S105 - test fixture data`.

- [x] [P3-T1] Extend `tests/test_build_velopack.py` with failing tests for: (a) `resolve_upload_command(version, repo_url, token)` returns argv `['vpk', 'upload', 'github', '--repoUrl', 'https://github.com/drmoisan/mix-calculator', '--publish', '--tag', f'v{version}', '--releaseName', f'mix-calculator {version}', '--token', token]` (AC7); (b) `redact_token(argv, token)` replaces every occurrence of `token` with `<REDACTED>` in the returned argv (deep copy, never mutates input); (c) `--upload` without `GITHUB_TOKEN` exits 2 with a stderr message naming the missing environment variable, and the seam is never invoked (AC8); (d) `--upload` with `GITHUB_TOKEN` set invokes the seam twice (pack then upload), and the second seam call contains the upload argv; (e) when the pack seam returns non-zero, `--upload` does NOT invoke the upload seam and the pack returncode is propagated; (f) `--version <invalid>` (including `1.0.0.0`) exits 2 before any seam call (AC9). Use `monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_TOKEN_VALUE_DO_NOT_USE")  # noqa: S105 - test fixture data`. Acceptance: file stays under 500 lines; new tests fail because the production behavior is not yet implemented.

- [x] [P3-T2] Capture the fail-before evidence for Phase 3. Run `poetry run pytest tests/test_build_velopack.py -x` and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/p3-fail-before-pytest.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` confirming the new tests fail. Tag: `[expect-fail]`.

- [x] [P3-T3] Extend `src/build_velopack.py` with: (a) `_REPO_URL: Final[str] = "https://github.com/drmoisan/mix-calculator"`; (b) `resolve_upload_command(version: str, repo_url: str, token: str) -> list[str]`; (c) `redact_token(argv: list[str], token: str) -> list[str]` returning a new list with every element equal to `token` replaced by `"<REDACTED>"`; (d) `main` upload-branch logic: when `args.upload` is set, read `os.environ.get("GITHUB_TOKEN")`; if absent, write a clear error to `sys.stderr` and return 2; on a successful pack (returncode == 0), resolve and invoke the upload seam; log the upload command using `redact_token`; propagate the upload returncode. File must stay under 500 lines.

- [x] [P3-T4] Run the Phase 3 toolchain loop. Execute, in order: `poetry run black src/build_velopack.py tests/test_build_velopack.py`, `poetry run ruff check src/build_velopack.py tests/test_build_velopack.py`, `poetry run pyright src/build_velopack.py tests/test_build_velopack.py`, `poetry run pytest tests/test_build_velopack.py -x --cov=src/build_velopack --cov-branch --cov-report=term-missing`. Restart from Black on any failure or auto-fix. Record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p3-toolchain.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` for each stage; include the numeric line and branch coverage for `src/build_velopack.py` in the pytest summary. Acceptance: all four stages PASS, line coverage on `src/build_velopack.py` >= 85%, branch coverage >= 75% (AC15).

---

### Phase 4 — pyproject.toml and quality-tiers.yml updates

Files touched in this phase:
- Modified: `pyproject.toml`
- Modified: `quality-tiers.yml`

- [x] [P4-T1] Edit `pyproject.toml` to add `velopack = ">=1.0.1,<2.0"` under `[tool.poetry.dependencies]` (after the existing `openpyxl` line) and to add `build-velopack = "src.build_velopack:main"` under `[tool.poetry.scripts]` (after the existing `build-exe` line). Acceptance: TOML is valid; both entries appear exactly once; existing entries are unchanged.

- [x] [P4-T2] Run `poetry lock --no-update` then `poetry install` to materialize the `velopack` runtime dep into `.venv`. Record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p4-poetry-install.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (installed version of `velopack`, lockfile updated yes/no). Acceptance: `poetry install` exits 0 and the installed `velopack` version satisfies `>=1.0.1,<2.0`.

- [x] [P4-T3] Edit `quality-tiers.yml` to add `src/build_velopack.py: T4` under the existing T4-Scaffolding section near `src/build_exe.py: T4`, with a brief comment indicating it is the Velopack pack-orchestration sibling of `build_exe.py` (issue #31). Acceptance: YAML parses; the new entry is the only added line; existing entries are unchanged (AC14).

- [x] [P4-T4] Run a smoke pytest pass to confirm the lockfile and tier file changes do not regress anything. Execute `poetry run pytest -x` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p4-pytest-smoke.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (total tests passed, failures, line/branch coverage totals). Acceptance: EXIT_CODE 0; no test regressions versus the Phase 0 baseline.

---

### Phase 5 — GUI runtime integration: velopack.App().run() bootstrap

Files touched in this phase:
- Modified (production): `src/gui/app.py`
- Modified (test): `tests/gui/test_app_composition.py`

This phase adds the mandatory Velopack runtime SDK bootstrap as the first statement of `src/gui/app.py:main()` and updates the existing `test_main_entry_point_runs_event_loop` test to patch `velopack.App` and assert the call ordering (Velopack bootstrap precedes `QApplication` construction) per AC10.

- [x] [P5-T1] Author a failing addition in `tests/gui/test_app_composition.py`. Modify `test_main_entry_point_runs_event_loop` to: (a) declare an `events: list[str] = []` ordered call-log; (b) `monkeypatch.setattr("velopack.App", lambda: _RecorderApp(events))` where `_RecorderApp.run` appends `"velopack_run"` to `events`; (c) wrap `_existing_qapp` so it appends `"qapplication_init"` to `events` before returning the instance; (d) assert `events == ["velopack_run", "qapplication_init"]` after `main([])` returns. Add a second new test `test_main_calls_velopack_app_run_before_qapplication` that explicitly asserts this ordering invariant in isolation. Acceptance: both tests fail until P5-T3 lands; existing passing tests are not weakened.

- [x] [P5-T2] Capture the fail-before evidence for Phase 5. Run `poetry run pytest tests/gui/test_app_composition.py -x` and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/p5-fail-before-pytest.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` confirming both new tests fail. Tag: `[expect-fail]`.

- [x] [P5-T3] Modify `src/gui/app.py:main()` to insert `velopack.App().run()` as the very first statement of the function body (before `logging.basicConfig`). Add the corresponding `import velopack` at the top of the module; if Pyright reports `velopack` as untyped, append `# type: ignore[import-untyped]` with the comment `velopack runtime SDK; no py.typed marker`. Do not alter the existing return value semantics. Acceptance: file stays under 500 lines; no other lines in `main()` are reordered.

- [x] [P5-T4] Run the Phase 5 toolchain loop. Execute, in order: `poetry run black src/gui/app.py tests/gui/test_app_composition.py`, `poetry run ruff check src/gui/app.py tests/gui/test_app_composition.py`, `poetry run pyright src/gui/app.py tests/gui/test_app_composition.py`, `poetry run pytest tests/gui/test_app_composition.py -x`. Restart from Black on any failure or auto-fix. Record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p5-toolchain.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` for each stage. Acceptance: all four stages PASS with EXIT_CODE 0 in a single loop pass.

---

### Phase 6 — PowerShell: vpk dev-environment requirement

Files touched in this phase:
- Modified (production): `scripts/dev-tools/DevEnvironment.psm1`, `scripts/dev-tools/Initialize-DevEnvironment.ps1`
- Modified (test): `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1`

This phase adds `vpk` as the fifth dev-environment requirement, with `Invoke-DotnetExe` as the wrapper seam, `Test-VpkRequirementSatisfied` for command-availability detection, `Install-VpkRequirement` driving `dotnet tool install -g vpk`, and Pester tests covering the present, absent, and post-install paths. The per-batch cap is honored (2 production, 1 test file). Mock signature parity uses `param([string[]]$DotnetArgs)` for `Invoke-DotnetExe`.

- [x] [P6-T1] Author failing additions to `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1`. Add a new `Describe 'vpk requirement'` block with `It` cases covering: (a) `Get-DevRequirementDefinition` returns an array containing a fifth element with `Id = 'vpk'`, `Name = 'Velopack CLI (vpk)'`, `RequiresElevation = $false`; (b) `Test-VpkRequirementSatisfied` returns `$true` when `Test-CommandAvailable -Name 'vpk'` is mocked to return `$true`; (c) `Test-VpkRequirementSatisfied` returns `$false` when the same mock returns `$false`; (d) `Install-VpkRequirement` invokes `Invoke-DotnetExe -DotnetArgs @('tool', 'install', '-g', 'vpk')` exactly once (mock signature `param([string[]]$DotnetArgs)`); (e) the orchestrator, when the vpk requirement is absent and confirmed, calls `Install-VpkRequirement` and records `Installed`; (f) the orchestrator, when the vpk requirement is present, records `Satisfied` and does not invoke `Invoke-DotnetExe`. Acceptance: file stays under 500 lines; new tests fail until P6-T3/P6-T4 land.

- [x] [P6-T2] Capture the fail-before evidence for Phase 6. Invoke `mcp__drm-copilot__run_poshqc_test` filtered to `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1` and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/p6-fail-before-pester.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` confirming the new tests fail. Tag: `[expect-fail]`.

- [x] [P6-T3] Edit `scripts/dev-tools/DevEnvironment.psm1` to extend `Get-DevRequirementDefinition` with the fifth hashtable entry `@{ Id = 'vpk'; Name = 'Velopack CLI (vpk)'; RequiresElevation = $false }` immediately after the existing `project` entry. Update `Export-ModuleMember` only if any new helper functions are added in this file (none are required for the definition update). Acceptance: file stays under 500 lines; PowerShell parses without error; the only added line is the new requirement entry plus an optional brief comment referencing issue #31.

- [x] [P6-T4] Edit `scripts/dev-tools/Initialize-DevEnvironment.ps1` to add: (a) the `Invoke-DotnetExe` wrapper function (signature `function Invoke-DotnetExe { [CmdletBinding()] param([Parameter(Mandatory)][string[]] $DotnetArgs) & dotnet @DotnetArgs 2>&1 }` per `.claude/rules/powershell.md`), only if a sibling `Invoke-DotnetExe` is not already present; (b) `Test-VpkRequirementSatisfied` calling `Test-CommandAvailable -Name 'vpk'`; (c) `Install-VpkRequirement` invoking `Invoke-DotnetExe -DotnetArgs @('tool', 'install', '-g', 'vpk')` with `SupportsShouldProcess`; (d) a dispatch arm added to `Invoke-RequirementInstall` for `'vpk'` that delegates to `Install-VpkRequirement`; (e) a dispatch arm added to `Test-RequirementPresent` for `'vpk'` that delegates to `Test-VpkRequirementSatisfied`. Acceptance: file stays under 500 lines; new functions follow the existing wrapper-seam and ShouldProcess pattern.

- [x] [P6-T5] Run the Phase 6 PowerShell toolchain loop. Invoke, in order: `mcp__drm-copilot__run_poshqc_format` scoped to the changed files; `mcp__drm-copilot__run_poshqc_analyze` scoped to the changed files; `mcp__drm-copilot__run_poshqc_test` scoped to `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1`. Restart from format on any failure or auto-fix. Record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p6-toolchain.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` for each stage; include line and branch coverage on the modified PowerShell files. Acceptance: all three stages PASS; line coverage >= 85%, branch coverage >= 75% on changed lines (AC11).

---

### Phase 7 — Distribution assets

Files touched in this phase:
- New (asset): `packaging/velopack/icon.ico`
- New (doc): `packaging/velopack/README.md`

- [x] [P7-T1] Generate `packaging/velopack/icon.ico` as a valid 256x256 ICO container with a flat background and a centered "MC" text mark. Method: use Pillow (verify availability with `poetry run python -c "import PIL"` first; if Pillow is not installed, add `pillow = ">=10.0"` to `[tool.poetry.group.dev.dependencies]` in `pyproject.toml` and run `poetry install`). The generator script is one-shot and is NOT committed (per the throwaway-script exception in `.claude/rules/general-code-change.md`); only the resulting `icon.ico` is committed. Verify the file's first four bytes are `0x00 0x00 0x01 0x00` (the ICO magic) by running `python -c "import sys; b=open('packaging/velopack/icon.ico','rb').read(4); sys.exit(0 if b==b'\\x00\\x00\\x01\\x00' else 1)"` and record the exit code at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p7-ico-magic.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (file size in bytes and magic-byte check pass/fail). Acceptance: EXIT_CODE 0 (AC12).

- [x] [P7-T2] Author `packaging/velopack/README.md` documenting: the `--packId` (`mix-calculator`), `--packTitle` (`Mix Calculator`), `--packAuthors` (`Dan Moisan`), `--channel` (`win`), the icon location (`packaging/velopack/icon.ico`), the icon replacement procedure (overwrite with a 256x256 multi-size ICO of the same path), and the GitHub Releases token permission requirement (`contents: write` scope for `--upload`). Reference `docs/features/active/2026-05-29-velopack-installer-31/spec.md` and `artifacts/research/2026-05-29-velopack-installer-landscape.md`. Tone per `.claude/rules/tonality.md`. Acceptance: file is under 500 lines; covers every documented item in the AC13 checklist; no marketing or hyperbolic language.

- [x] [P7-T3] Capture the asset verification evidence. Run `poetry run pytest -x` to confirm no Python tests were impacted, and record at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p7-pytest-smoke.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (total tests, line/branch coverage totals). Acceptance: EXIT_CODE 0; no regressions versus Phase 4.

---

### Phase 8 — Final QA Loop and AC Verification

This phase executes the full mandatory toolchain across every changed file in a single uninterrupted loop, records the post-change coverage delta, verifies all 17 acceptance criteria with citations, and confirms the 500-line cap on every changed file.

- [x] [P8-T1] Run final Python format stage. Execute `poetry run black .` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-black.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (count of files reformatted, expected 0). Acceptance: EXIT_CODE 0; no files reformatted. If files were reformatted, restart from this task.

- [x] [P8-T2] Run final Python lint stage. Execute `poetry run ruff check .` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-ruff.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` ("All checks passed" or error count). Acceptance: EXIT_CODE 0; zero errors. If any error fires, fix and restart from P8-T1.

- [x] [P8-T3] Run final Python type-check stage. Execute `poetry run pyright` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-pyright.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (errors / warnings / informations). Acceptance: EXIT_CODE 0; zero errors. If any error fires, fix and restart from P8-T1.

- [x] [P8-T4] Run final Python test + coverage stage. Execute `poetry run pytest --cov --cov-branch --cov-report=term-missing` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-pytest-cov.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` containing: total tests passed, failures, total line coverage %, total branch coverage %, per-file line coverage for `src/build_velopack.py`, per-file branch coverage for `src/build_velopack.py`. Acceptance: EXIT_CODE 0; total line coverage >= 85%; total branch coverage >= 75%; line coverage on `src/build_velopack.py` >= 85%; branch coverage on `src/build_velopack.py` >= 75%; no test failures (AC15, AC17).

- [x] [P8-T5] Run final PoshQC format stage. Invoke `mcp__drm-copilot__run_poshqc_format` against the full PowerShell tree and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-poshqc-format.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (files reformatted). Acceptance: EXIT_CODE 0; zero files reformatted.

- [x] [P8-T6] Run final PoshQC analyze stage. Invoke `mcp__drm-copilot__run_poshqc_analyze` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-poshqc-analyze.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (rule violation counts by severity). Acceptance: EXIT_CODE 0; zero Error- and Warning-severity violations on touched files.

- [x] [P8-T7] Run final Pester stage. Invoke `mcp__drm-copilot__run_poshqc_test` and record evidence at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-pester.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (passed / failed / skipped, line and branch coverage on the modified PowerShell files). Acceptance: EXIT_CODE 0; all tests pass; line coverage >= 85% and branch coverage >= 75% on changed lines.

- [x] [P8-T8] Verify the 500-line cap on every changed and new file. Run `python -c "import sys, pathlib; cap=500; files=['src/build_velopack.py','tests/test_build_velopack.py','src/gui/app.py','tests/gui/test_app_composition.py','scripts/dev-tools/DevEnvironment.psm1','scripts/dev-tools/Initialize-DevEnvironment.ps1','tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1','packaging/velopack/README.md']; over=[(f,sum(1 for _ in open(f, encoding='utf-8'))) for f in files if sum(1 for _ in open(f, encoding='utf-8')) > cap]; sys.exit(0 if not over else 1)"` and record the per-file line counts at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-file-size-cap.2026-05-29T10-15.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (line counts per file; flag any file > 500 lines). Acceptance: EXIT_CODE 0; no file exceeds 500 lines (AC16).

- [x] [P8-T9] Verify the coverage no-regression invariant. Compare the Phase 0 pytest coverage baseline (`evidence/baseline/pytest-cov.2026-05-29T10-15.md`) with the Phase 8 final pytest coverage (`evidence/qa-gates/p8-pytest-cov.2026-05-29T10-15.md`) and record a delta report at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-coverage-delta.2026-05-29T10-15.md` with `Timestamp:`, `Command:` (`coverage report`), `EXIT_CODE:`, `Output Summary:` containing: baseline total line %, baseline total branch %, post-change total line %, post-change total branch %, per-file new-code coverage for `src/build_velopack.py`, and a no-regression assertion. Acceptance: post-change line and branch coverage are each >= baseline; new-code line coverage on `src/build_velopack.py` >= 85% and branch coverage >= 75%.

- [x] [P8-T10] Author the AC1–AC17 verification table at `docs/features/active/2026-05-29-velopack-installer-31/evidence/qa-gates/p8-ac-verification.2026-05-29T10-15.md`. Each row lists the AC number, the AC text (abbreviated), the verification command or test name, and the evidence-artifact path. Required mappings: AC1 → `tests/test_build_velopack.py::test_build_argument_parser_exposes_required_flags` plus `p3-toolchain` artifact; AC2 → `pyproject.toml` diff plus `p4-poetry-install` artifact; AC3 → `tests/test_build_velopack.py::test_main_dry_run_prints_argv_and_does_not_invoke_seam`; AC4 → `tests/test_build_velopack.py::test_resolve_pack_command_contains_required_argv`; AC5 → `tests/test_build_velopack.py::test_main_propagates_seam_returncode` parameterized; AC6 → `tests/test_build_velopack.py::test_main_clean_removes_dist_velopack`; AC7 → `tests/test_build_velopack.py::test_resolve_upload_command_argv_shape` and `test_redact_token_replaces_token_in_argv`; AC8 → `tests/test_build_velopack.py::test_upload_without_github_token_exits_two`; AC9 → `tests/test_build_velopack.py::test_resolve_version_default_override_and_rejects_four_part`; AC10 → `tests/gui/test_app_composition.py::test_main_calls_velopack_app_run_before_qapplication`; AC11 → `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1` `Describe 'vpk requirement'`; AC12 → `p7-ico-magic` artifact; AC13 → `packaging/velopack/README.md` diff; AC14 → `quality-tiers.yml` diff; AC15 → `p8-pytest-cov` artifact; AC16 → `p8-file-size-cap` artifact; AC17 → `p8-black`, `p8-ruff`, `p8-pyright`, `p8-pytest-cov`, `p8-poshqc-format`, `p8-poshqc-analyze`, `p8-pester` artifacts. Acceptance: every AC1–AC17 row marked PASS with citations; zero ACs marked partial or fail.
