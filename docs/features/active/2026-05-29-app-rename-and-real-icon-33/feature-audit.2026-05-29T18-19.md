# Feature Audit: App Rename and Real Icon (#33)

**Audit Date:** 2026-05-29
**Feature Folder:** `docs/features/active/2026-05-29-app-rename-and-real-icon-33`
**Base Branch:** `main`
**Head Branch:** `feature/app-rename-and-real-icon-33`
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `9e5f8836b3fc1eff0320213ccd849d772843bd9e`)
- **Head branch/commit:** `feature/app-rename-and-real-icon-33` (commit `ee5f2778a260c16112b41ea224d963b625a433de`)
- **Merge base:** `9e5f8836b3fc1eff0320213ccd849d772843bd9e`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-29-app-rename-and-real-icon-33/evidence/`
  - Additional evidence: `docs/features/active/2026-05-29-app-rename-and-real-icon-33/issue.md`, `plan.2026-05-29T00-00.md`
- **Feature folder used:** `docs/features/active/2026-05-29-app-rename-and-real-icon-33`
- **Requirements source:** `issue.md` (per the work-mode marker `- Work Mode: minor-audit` on line 9; only the explicit `## Acceptance Criteria` section in `issue.md` is treated as the AC source).
- **Work mode resolution note:** The work-mode marker in `issue.md` is `minor-audit`. Per the work-mode routing in this agent's contract, the only AC source for minor-audit is the explicit `## Acceptance Criteria` section of `issue.md`. `spec.md` and `user-story.md` are not consulted for AC content.
- **Scope note:** Audit covers the full branch diff against the resolved base (47 files, +1781 / -115 lines). The orchestrator prompt did not attempt to narrow scope; the scope invariant is respected.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-29-app-rename-and-real-icon-33/issue.md` — only source

### Acceptance criteria

1. AC1: `src/build_exe.py` resolves a Nuitka argv that includes, in order alongside the existing flags: `--output-filename=MixCalculator.exe`, `--windows-icon-from-ico=<REPO_ROOT>/packaging/velopack/icon.ico`, and `--include-data-file=<REPO_ROOT>/packaging/velopack/icon.ico=icon.ico`. A unit test verifies ordered membership of all three flags.
2. AC2: `src/build_velopack.py` resolves a `vpk pack` argv where `--packId` is `MixCalculator` and `--mainExe` is `MixCalculator.exe`. The `--packTitle` argument is unchanged at `Mix Calculator`. A unit test verifies the new values.
3. AC3: `src/build_velopack.py` resolves a `vpk upload github` argv where `--releaseName` is `"Mix Calculator <version>"`. A unit test verifies the new value.
4. AC4: `packaging/velopack/icon-source.svg` is committed as a copy of the user-supplied SVG at `artifacts/realgood_calculator_icon.svg`. The file is a valid SVG (starts with `<svg`).
5. AC5: `packaging/velopack/icon.ico` is a multi-size Windows ICO container with frames at 16x16, 32x32, 48x48, and 256x256. The magic bytes are `0x00 0x00 0x01 0x00`. Verified by a pytest-driven probe of the binary header.
6. AC6: `packaging/velopack/convert_icon.py` exists as a self-contained one-shot script with a `main()` returning exit 0 on success. It uses PySide6's `QSvgRenderer` to rasterize each size and Pillow's `Image.save(..., format='ICO')` to assemble the multi-size ICO. The script does not exceed 500 lines. A unit test exercises the conversion with a small synthetic SVG fixture (no external assets).
7. AC7: `pyproject.toml` adds `pillow = "^12.0"` under `[tool.poetry.group.dev.dependencies]`. `poetry.lock` is regenerated. `poetry install` resolves cleanly.
8. AC8: `src/gui/app.py:build_application()` calls `QApplication.setWindowIcon(QIcon(<resolved path>))` after the QApplication is constructed, where the path is resolved by a new `resolve_icon_path()` helper that probes compiled-mode and dev-mode locations in order. A unit test patches `QIcon` and asserts the call is made with the expected path string.
9. AC9: `packaging/velopack/README.md` documents the new packId, mainExe, output filename, releaseName, the icon source path, the conversion command, and the dependency on Pillow as a dev-only build-time tool.
10. AC10: All modified Python files and the new conversion script pass Black, Ruff, Pyright, and Pytest with no new suppressions beyond pre-authorized patterns. Coverage on changed modules remains >= 85% line / >= 75% branch. The full Python suite remains green with no regressions.
11. AC11: File-size cap (500 lines) is satisfied for every new and modified file.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC1: Nuitka argv contains `--output-filename=MixCalculator.exe`, `--windows-icon-from-ico=<icon-abs-path>`, `--include-data-file=<icon-abs-path>=icon.ico` in ordered membership. | PASS | `src/build_exe.py:133-141` emits all three flags between `--output-dir=` and the trailing `app.py` positional. `tests/test_build_exe.py::test_resolve_nuitka_command_contains_icon_flags` asserts ordered membership; `tests/test_build_exe.py::test_main_dry_run_prints_argv_and_does_not_invoke_seam` asserts the three flag prefixes appear in the printed dry-run. | `env -u VIRTUAL_ENV poetry run pytest tests/test_build_exe.py -q` | Evidence: `evidence/qa-gates/phase2-build-exe-tests.md` exit 0. |
| 2 | AC2: `vpk pack` argv has `--packId MixCalculator`, `--mainExe MixCalculator.exe`, `--packTitle "Mix Calculator"` unchanged. | PASS | `src/build_velopack.py:207-225` emits the new values. `tests/test_build_velopack.py::test_resolve_pack_command_contains_required_argv` asserts each pair. | `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -q` | Evidence: `evidence/qa-gates/phase3-build-velopack-tests.md` exit 0. |
| 3 | AC3: `vpk upload github` argv has `--releaseName "Mix Calculator <version>"`. | PASS | `src/build_velopack.py:252-253` emits `f"Mix Calculator {version}"`. `tests/test_build_velopack.py::test_resolve_upload_command_argv_shape` asserts the value. | `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -q` | Evidence: `evidence/qa-gates/phase3-build-velopack-tests.md` exit 0. |
| 4 | AC4: `packaging/velopack/icon-source.svg` committed as byte-exact copy of `artifacts/realgood_calculator_icon.svg`; valid SVG. | PASS | The committed SVG has SHA256 matching the Phase 0 baseline of the source artifact per `evidence/qa-gates/phase6-icon-source-fingerprint.md`; the file starts with `<?xml ... <svg`. | `env -u VIRTUAL_ENV poetry run python -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('packaging/velopack/icon-source.svg').read_bytes()).hexdigest())"` | Evidence: `evidence/qa-gates/phase6-icon-source-fingerprint.md` exit 0. |
| 5 | AC5: `packaging/velopack/icon.ico` is a multi-size ICO with frames at 16/32/48/256 and magic `0x00 0x00 0x01 0x00`. | PASS | Direct verification: file is 12813 bytes; first four bytes `00 00 01 00`. `evidence/qa-gates/phase6-icon-fingerprint.md` records the SHA256 and sorted frame-size set `{(16,16),(32,32),(48,48),(256,256)}`. | `python -c "import pathlib;b=pathlib.Path('packaging/velopack/icon.ico').read_bytes();print(len(b), b[:4].hex())"` | Evidence: `evidence/qa-gates/phase6-icon-fingerprint.md` exit 0. |
| 6 | AC6: `packaging/velopack/convert_icon.py` is a one-shot script with `main()` returning 0; uses QSvgRenderer + Pillow ICO assembly; under 500 lines; covered by a synthetic-fixture unit test. | PASS | File is 358 lines; `main()` returns 0 on the seam-substituted path. Three tests in `tests/test_convert_icon.py` cover conversion bytes, CLI seam round-trip, and invalid-SVG rejection. | `env -u VIRTUAL_ENV poetry run pytest tests/test_convert_icon.py -q` | Evidence: `evidence/qa-gates/phase5-convert-icon-tests.md` exit 0. |
| 7 | AC7: `pyproject.toml` adds `pillow = "^12.0"` under `[tool.poetry.group.dev.dependencies]`; lockfile regenerated; `poetry install` clean. | PASS | `pyproject.toml` diff `+1` line; `poetry.lock` diff `+111/-...`; Pillow 12.2.0 imports cleanly under the venv. | `env -u VIRTUAL_ENV poetry lock`; `env -u VIRTUAL_ENV poetry install`; `env -u VIRTUAL_ENV poetry run python -c "from PIL import Image; print(Image.__version__)"` | Evidence: `evidence/qa-gates/phase4-poetry-lock.md`, `phase4-poetry-install.md`, `phase4-pil-import.md` all exit 0. |
| 8 | AC8: `build_application()` calls `QApplication.setWindowIcon(QIcon(<resolved path>))`; `resolve_icon_path()` probes compiled-mode then dev-mode; unit test patches `QIcon`. | PASS | `src/gui/app.py:298-302` and `:449` drive `setWindowIcon`. `src/gui/_icon.py::resolve_icon_path` implements compiled-mode-then-dev-mode probing with `FileNotFoundError` when both miss. Three probe-branch tests in `tests/gui/test_icon.py`; two AC8 wiring tests in `tests/gui/test_app_composition.py`. | `env -u VIRTUAL_ENV poetry run pytest tests/gui/test_icon.py tests/gui/test_app_composition.py -q` | Evidence: `evidence/qa-gates/phase1-icon-tests.md` and `phase7-gui-tests.md` exit 0. |
| 9 | AC9: README documents new packId, mainExe, output filename, releaseName, icon source, conversion command, and Pillow as dev-only build-time dep. | PASS | README diff `+75/-...` lines. Token-presence probe confirms all six required strings present (`MixCalculator`, `MixCalculator.exe`, `Mix Calculator`, `icon-source.svg`, `convert_icon.py`, `Pillow`). New `## Icon source and regeneration` section. | `env -u VIRTUAL_ENV poetry run python -c "import pathlib;t=pathlib.Path('packaging/velopack/README.md').read_text();print(all(s in t for s in ['MixCalculator','MixCalculator.exe','Mix Calculator','icon-source.svg','convert_icon.py','Pillow']))"` | Evidence: `evidence/qa-gates/phase8-readme-tokens.md` exit 0. |
| 10 | AC10: Black/Ruff/Pyright/Pytest clean; no new suppressions outside pre-authorized; coverage on changed modules >= 85% line / >= 75% branch; full suite green. | PASS | Toolchain stages all exit 0 in a single iteration. Repo-wide coverage 99%/99%. Per-changed-module coverage: `build_exe` 97/100, `build_velopack` 98/96, `_icon` 100/100, `gui/app` 99/92. Suppression scan (see `policy-audit.2026-05-29T18-19.md` section 8) finds only pre-authorized S603/S105/S106 patterns plus one defensive `# type: ignore[unused-ignore]` on a meta-Pyright warning. | `env -u VIRTUAL_ENV poetry run black --check .`; `env -u VIRTUAL_ENV poetry run ruff check .`; `env -u VIRTUAL_ENV poetry run pyright`; `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | Evidence: `evidence/qa-gates/phase9-black.md`, `phase9-ruff.md`, `phase9-pyright.md`, `phase9-pytest.md`, `phase9-coverage-changed-modules.md` all exit 0. |
| 11 | AC11: 500-line file-size cap satisfied for every new and modified file. | PASS | Direct verification: max 496 lines (`tests/test_build_velopack.py`); 11 changed Python files all under 500. `src/gui/app.py` at 456 lines and `src/gui/_main_window_view.py` at 108 lines are the result of the `MainWindowPipelineView` extraction. | `python -c "import pathlib;files=['src/build_exe.py','src/build_velopack.py','src/gui/app.py','src/gui/_icon.py','src/gui/_main_window_view.py','packaging/velopack/convert_icon.py','tests/test_build_exe.py','tests/test_build_velopack.py','tests/gui/test_app_composition.py','tests/gui/test_icon.py','tests/test_convert_icon.py'];[print(f, sum(1 for _ in pathlib.Path(f).open())) for f in files]"` | Evidence: `evidence/qa-gates/phase9-file-size.md`. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 11 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. None required for merge readiness. Optional: re-run `env -u VIRTUAL_ENV poetry run build-velopack --dry-run` against the head branch to confirm the resolved `vpk pack` argv still references the regenerated `icon.ico` by absolute path (already covered by unit tests; included here only as a redundancy check).
2. Optional follow-up tracked outside this PR: CI workflow that invokes `build-exe` + `build-velopack` on tag push; code signing of `Setup.exe`; in-app update-check UI (all listed under "Out-of-Scope Follow-ups" in `issue.md`).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** may be checked off in the authoritative source file(s) if they are represented as markdown checkboxes and are not already checked.
- Criteria evaluated as **PARTIAL**, **FAIL**, or **UNVERIFIED** must remain unchecked.

All 11 acceptance criteria in `issue.md` `## Acceptance Criteria` (lines 114-161) are already represented as `- [x]` checkboxes — they were checked off by the executor as each phase completed. This reviewer confirms every `[x]` is supported by the verification evidence cited above; no rollback or new check-off is required.

### AC Status Summary

- Source: `docs/features/active/2026-05-29-app-rename-and-real-icon-33/issue.md`
- Total AC items: 11
- Checked off (delivered): 11
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-29-app-rename-and-real-icon-33/issue.md` | 11 | 11 | 0 | Checkbox-backed AC source for the `minor-audit` work mode. All 11 items were check-marked by the executor; this audit confirms each check-mark is supported by evidence. No source-file checkbox change was made by this audit because all items were already `[x]` and the reviewer's evaluation matches. |
