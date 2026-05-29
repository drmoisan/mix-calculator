# Phase 8 — AC1-AC17 verification

Timestamp: 2026-05-29T10-15

Source of AC: `docs/features/active/2026-05-29-velopack-installer-31/spec.md` (AC1-AC17).

| AC | Status | Verification |
|---|---|---|
| AC1 | PASS | `tests/test_build_velopack.py::test_build_argument_parser_exposes_required_flags` exercises all five flags; final pytest in `evidence/qa-gates/p8-pytest-cov.2026-05-29T10-15.md` records pass. |
| AC2 | PASS | `pyproject.toml` adds `velopack = ">=1.0.1,<2.0"` under `[tool.poetry.dependencies]` and `build-velopack = "src.build_velopack:main"` under `[tool.poetry.scripts]`; `evidence/qa-gates/p4-poetry-install.2026-05-29T10-15.md` records `velopack (1.0.1)` installed. |
| AC3 | PASS | `tests/test_build_velopack.py::test_main_dry_run_prints_argv_and_does_not_invoke_seam`. |
| AC4 | PASS | `tests/test_build_velopack.py::test_resolve_pack_command_contains_required_argv` asserts every flag/value pair. |
| AC5 | PASS | `tests/test_build_velopack.py::test_main_propagates_seam_returncode` (parametrized over codes 0/1/2/137). |
| AC6 | PASS | `tests/test_build_velopack.py::test_main_clean_removes_dist_velopack` (both branches) and `test_main_clean_then_invokes_seam` (ordering). |
| AC7 | PASS | `tests/test_build_velopack.py::test_resolve_upload_command_argv_shape` and `test_redact_token_replaces_token_in_argv`. |
| AC8 | PASS | `tests/test_build_velopack.py::test_upload_without_github_token_exits_two`. |
| AC9 | PASS | `tests/test_build_velopack.py::test_validate_semver2_accepts_canonical_versions`, `test_validate_semver2_rejects_invalid_versions` (parametrized incl. `1.0.0.0`), `test_resolve_version_defaults_to_pyproject`, `test_resolve_version_honors_override`, `test_resolve_version_rejects_invalid_override`, `test_main_rejects_invalid_version_before_any_seam_call`. |
| AC10 | PASS | `tests/gui/test_app_composition.py::test_main_calls_velopack_app_run_before_qapplication` and the call-ordering assertion in `test_main_entry_point_runs_event_loop`. Implementation in `src/gui/app.py:main()` invokes `run_velopack_bootstrap()` (which calls `velopack.App().run()`) as the very first statement. |
| AC11 | PASS | `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1` `Describe 'vpk requirement (issue #31)'` covers Test-VpkRequirementSatisfied true/false, Install-VpkRequirement -> dotnet tool install -g vpk, Invoke-RequirementInstall dispatch, Test-RequirementPresent vpk arm, orchestrator Installed/Satisfied. `Get-DevRequirementDefinition` test asserts the 5-entry list. |
| AC12 | PASS | `evidence/qa-gates/p7-ico-magic.2026-05-29T10-15.md` records EXIT_CODE 0 confirming the first four bytes of `packaging/velopack/icon.ico` are `0x00 0x00 0x01 0x00`. |
| AC13 | PASS | `packaging/velopack/README.md` documents `--packId` (`mix-calculator`), `--packTitle` (`Mix Calculator`), `--packAuthors` (`Dan Moisan`), `--channel` (`win`), icon location, the 4-step icon replacement procedure, the magic-byte verification command, and the `contents: write` token permission requirement. |
| AC14 | PASS | `quality-tiers.yml` adds `src/build_velopack.py: T4` alongside `src/build_exe.py: T4` with an explanatory comment referencing issue #31. |
| AC15 | PASS | `evidence/qa-gates/p8-pytest-cov.2026-05-29T10-15.md`: `src/build_velopack.py` line 98% (Stmts 91, Miss 1) >= 85%; branch ~95.8% (Branch 24, BrPart 1) >= 75%. |
| AC16 | PASS | `evidence/qa-gates/p8-file-size-cap.2026-05-29T10-15.md`: every code/test file at or under 500 lines. `src/build_velopack.py` 411 lines, `tests/test_build_velopack.py` 496 lines. |
| AC17 | PASS | Full toolchain green in a single loop per `evidence/qa-gates/p8-black`, `p8-ruff`, `p8-pyright`, `p8-pytest-cov`, `p8-poshqc-format`, `p8-poshqc-analyze`, `p8-pester`. Only pre-authorized `# noqa: S603 - static analysis can't verify runtime validation` (twice on the subprocess seam), pre-authorized `# noqa: S105` and `# noqa: S106` on test fixture token strings, and pre-authorized `# type: ignore[import-untyped]` on the velopack import. No new ad-hoc suppressions introduced. |

All AC1-AC17 marked PASS with citations. Zero PARTIAL, FAIL, or UNVERIFIED.
