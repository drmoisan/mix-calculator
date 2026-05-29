# Feature Audit: velopack-installer (issue #31)

- Feature: `2026-05-29-velopack-installer-31`
- Branch: `feature/velopack-installer-31` @ `abd5601`
- Base branch: `main` @ `9188fd6f7815fbc35c0fba5082eda98d77d67e6c`
- Audit date: 2026-05-29
- Work mode: `full-feature` (per issue.md `- Work Mode: full-feature` marker)
- AC sources resolved: `spec.md` (binding 17-item set) and `user-story.md` (15-item draft set)
- Reviewer: feature-review agent (Claude Opus 4.7)

## Scope and Baseline

The audit compares the feature branch against the resolved base `main` at merge-base `9188fd6` (PR #30 merge commit), per the SKILL scope invariant. Scope was determined by the agent from `artifacts/pr_context.summary.txt` (`Range: 9188fd6..abd5601`); no caller narrowing was applied.

Changed-file overview (from `git diff --name-status 9188fd6..HEAD`):

- 7 core code files modified or added (build orchestrator, GUI bootstrap, GUI entry-point, PowerShell dev-env scripts).
- 3 test files added or modified (Python + Pester).
- 3 config files modified (`pyproject.toml`, `poetry.lock`, `quality-tiers.yml`).
- 2 assets added (`packaging/velopack/icon.ico`, `packaging/velopack/README.md`).
- 37 docs/evidence files added under `docs/features/active/2026-05-29-velopack-installer-31/`.

Verification evidence consulted:

- All Phase 1-8 QA-gate evidence files at timestamp `2026-05-29T10-15`.
- Live re-verification on 2026-05-29T14-40-14-45 (Black --check, Ruff, Pyright, Pytest with coverage, PoshQC format/analyze/test, ICO magic-byte check, evidence-location scan, workflow-rule trigger check).

## Acceptance Criteria Inventory

### Binding AC source (`spec.md`, full-feature work mode)

17 items, AC1 through AC17, listed under `## Acceptance Criteria`. All items state-tracked as `- [x]` in the source file.

### Secondary AC source (`user-story.md`)

15 draft items (paragraph-split into individual `- [ ]` lines). The user-story file is a Draft and its checkboxes were never persisted to `- [x]` because the AC content is split mid-sentence in the source file. The binding spec.md set covers every behavior referenced in the user-story draft.

### Acceptance criteria

AC numbering matches spec.md.

## Acceptance Criteria Evaluation

| AC | Description (abridged) | Verdict | Evidence |
|----|------------------------|---------|----------|
| AC1 | `src/build_velopack.py` with `main()` + argparse CLI (`--dry-run`, `--clean`, `--version`, `--upload`, `--release-dir`). | PASS | `src/build_velopack.py` lines 67-126 (`build_argument_parser`); `tests/test_build_velopack.py::test_build_argument_parser_exposes_required_flags`. |
| AC2 | `pyproject.toml` declares `build-velopack` script entry and `velopack >= 1.0.1,<2.0` runtime dep. | PASS | `pyproject.toml` diff lines 17-18 (runtime dep) and 36-37 (script entry); `poetry.lock` regenerated. |
| AC3 | `--dry-run` prints resolved argv and exits 0 without invoking the seam. | PASS | `src/build_velopack.py` lines 343-347; `tests/test_build_velopack.py` dry-run tests. |
| AC4 | Resolved `vpk pack` argv has the documented order and value set. | PASS | `src/build_velopack.py::resolve_pack_command` lines 182-220; unit test compares against the literal argv. |
| AC5 | `vpk` returncode propagated unchanged. | PASS | `src/build_velopack.py` lines 384-390; unit test asserts non-zero propagation. |
| AC6 | `--clean` removes `dist/velopack/` tree on present, no-op on absent. | PASS | `src/build_velopack.py` lines 336-341; unit tests cover both branches. |
| AC7 | `--upload` argv has documented shape; token redacted in log output. | PASS | `src/build_velopack.py::resolve_upload_command` lines 223-249; `redact_token` lines 252-270; unit tests verify both. |
| AC8 | `--upload` without `GITHUB_TOKEN` exits 2 with clear stderr message before any seam call. | PASS | `src/build_velopack.py` lines 369-378; unit test asserts exit code and stderr text. |
| AC9 | Version resolution defaults to pyproject, override via `--version`, invalid SemVer2 (incl. four-part) exits 2 before seam. | PASS | `src/build_velopack.py::validate_semver2` lines 129-144; `resolve_version` lines 147-179; parametrized rejection table. |
| AC10 | `src/gui/app.py:main()` calls `velopack.App().run()` first, before logging config. | PASS | `src/gui/app.py` lines 482-489 (diff lines 478-489 show the new first-call); `tests/gui/test_app_composition.py::test_main_calls_velopack_app_run_before_qapplication` asserts `events[:2] == ["velopack_run", "qapplication_init"]`. |
| AC11 | `Initialize-DevEnvironment.ps1` and `DevEnvironment.psm1` recognize `vpk` as the fifth requirement; Pester covers present/absent/installed paths. | PASS | `scripts/dev-tools/DevEnvironment.psm1` diff (+vpk entry); `scripts/dev-tools/Initialize-DevEnvironment.ps1` diff (+Invoke-DotnetExe, +Test-VpkRequirementSatisfied, +Install-VpkRequirement, +vpk arms in dispatch); `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1` 7+ It blocks under `Describe 'vpk requirement (issue #31)'`. |
| AC12 | `packaging/velopack/icon.ico` is committed and a valid ICO container (magic `0x00 0x00 0x01 0x00`). | PASS | `od -An -t x1 -N 4 packaging/velopack/icon.ico` -> `00 00 01 00`; `evidence/qa-gates/p7-ico-magic.2026-05-29T10-15.md`. |
| AC13 | `packaging/velopack/README.md` documents packId/title/authors/channel/icon and the `contents: write` token permission. | PASS | `packaging/velopack/README.md` lines 12-26 (pack identity table); 28-49 (icon section); 51-70 (GitHub Releases token permission). |
| AC14 | `quality-tiers.yml` classifies `src/build_velopack.py` as T4. | PASS | `quality-tiers.yml` diff: `src/build_velopack.py: T4` with a comment block citing issue #31 and the parallel to `src/build_exe.py`. |
| AC15 | Unit-test coverage on `src/build_velopack.py` >= 85% line and >= 75% branch. | PASS | 98% line (91 stmts, 1 missed), 95.8% branch (23/24); both well above thresholds. Evidence: `evidence/qa-gates/p8-pytest-cov.2026-05-29T10-15.md` plus live re-run 2026-05-29T14-40. |
| AC16 | `src/build_velopack.py` and `tests/test_build_velopack.py` each < 500 lines. | PASS | 411 lines and 496 lines respectively; verified by live `wc -l`. |
| AC17 | Full mandatory toolchain green in a single loop; no new suppressions beyond pre-authorized `# noqa: S603`. | PASS | Live re-run: Black --check 115 files unchanged; Ruff `All checks passed!`; Pyright 0 errors; Pytest 488 passed; PoshQC format/analyze/test all `ok:true`. New suppressions: `# noqa: S603` x2 (pre-authorized) and `# type: ignore[import-untyped]` x1 (pre-authorized). |

### User-story acceptance criteria (informational; binding set is spec.md)

The user-story file uses sentence-split `- [ ]` checkboxes that map back to spec.md AC numbers. The mapping below confirms full coverage; the user-story file itself is not updated by this audit because the spec.md set is binding for full-feature mode per the work-mode contract.

| user-story line(s) | Maps to spec AC | Verdict |
|---|---|---|
| `--dry-run` prints argv | AC3 | PASS |
| `build-velopack` produces `<AppName>-Setup.exe` on a host with `vpk` installed | AC4 (default-path argv resolution); end-to-end validation is out of scope (no real `vpk` invocation in unit tests, by spec) | PASS (spec-bounded) |
| `--upload` invokes `vpk upload github` with GITHUB_TOKEN | AC7, AC8 | PASS |
| `--clean` removes dist/velopack | AC6 | PASS |
| Non-zero vpk codes propagate | AC5 | PASS |
| Version defaults to pyproject | AC9 | PASS |
| `Initialize-DevEnvironment.ps1` installs vpk when absent | AC11 | PASS |
| Coverage >= 85% line / >= 75% branch | AC15 | PASS |
| File-size cap | AC16 | PASS |
| Full toolchain in a single loop | AC17 | PASS |
| Spec.md documents SmartScreen warning + tracks code-signing follow-up | Verified in `spec.md` Constraints & Risks section | PASS |

## Summary

All 17 binding spec.md acceptance criteria are PASS. All informational user-story criteria are PASS through their spec.md mapping. The branch is feature-complete relative to the issue #31 scope as documented in spec.md.

Verdict counts:
- PASS: 17 / 17 (binding spec.md set)
- PARTIAL: 0
- FAIL: 0
- UNVERIFIED: 0

Outstanding work explicitly documented as out-of-scope follow-ups (tracked in spec.md):
- Code signing of `Setup.exe`
- In-app `Check for Updates` UI
- CI workflow for tag-pushed build-and-upload
- Replacement of placeholder icon with designed icon
- Multi-channel publishing

These follow-ups are not policy violations; they are explicit scope-out decisions documented in the spec.

## Acceptance Criteria Check-off

The 17 spec.md AC items are already checked off at the `- [x]` state in `spec.md` and `issue.md`. This audit confirms the existing state matches the verdict above; no source-file mutation is performed because every AC was checked off by the executor agent at task completion (per `acceptance-criteria-tracking` SKILL).

The user-story.md file remains in its Draft state with `- [ ]` checkboxes. Per the work-mode contract (`full-feature` -> spec.md is binding), this audit does NOT mutate the user-story.md AC checkboxes; they are tracked as informational only.

### AC Status Summary

- Source: `docs/features/active/2026-05-29-velopack-installer-31/spec.md` (binding) and `docs/features/active/2026-05-29-velopack-installer-31/user-story.md` (informational draft)
- Total AC items (binding spec.md set): 17
- Checked off (delivered): 17
- Remaining (unchecked): 0
- Items remaining: none

User-story.md (informational, Draft):
- Total checkbox lines: 15 (sentence-split)
- Checked off: 0 (file remains in Draft state)
- All informational items map to PASS verdicts in the binding spec.md set above; the file itself is not mutated by this audit per the work-mode contract.
