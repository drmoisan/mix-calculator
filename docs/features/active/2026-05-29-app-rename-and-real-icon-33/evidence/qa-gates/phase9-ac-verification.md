# Phase 9 — AC1-AC11 verification matrix

Timestamp: 2026-05-29T20-50

| AC | Artifact(s) | Status |
|---|---|---|
| AC1 | evidence/qa-gates/phase2-build-exe-tests.md | PASS — `resolve_nuitka_command()` emits `--output-filename=MixCalculator.exe`, `--windows-icon-from-ico=<REPO_ROOT>/packaging/velopack/icon.ico`, and `--include-data-file=<...>/icon.ico=icon.ico` in ordered membership. Verified by `test_resolve_nuitka_command_contains_icon_flags`. |
| AC2 | evidence/qa-gates/phase3-build-velopack-tests.md | PASS — `resolve_pack_command()` argv contains `--packId MixCalculator`, `--mainExe MixCalculator.exe`, and `--packTitle "Mix Calculator"` (unchanged). Verified by `test_resolve_pack_command_contains_required_argv`. |
| AC3 | evidence/qa-gates/phase3-build-velopack-tests.md | PASS — `resolve_upload_command()` argv contains `--releaseName "Mix Calculator 0.1.0"`. Verified by `test_resolve_upload_command_argv_shape`. |
| AC4 | evidence/qa-gates/phase6-icon-source-fingerprint.md | PASS — `packaging/velopack/icon-source.svg` SHA256 equals the Phase 0 baseline of `artifacts/realgood_calculator_icon.svg` (4632e3...3aab42); file starts with `<svg `. |
| AC5 | evidence/qa-gates/phase6-icon-fingerprint.md | PASS — Generated `packaging/velopack/icon.ico` is 12813 bytes; magic header `00000100`; frames {(16,16),(32,32),(48,48),(256,256)}. |
| AC6 | evidence/qa-gates/phase5-convert-icon-tests.md | PASS — `packaging/velopack/convert_icon.py` exists with a `main()` returning 0; uses QSvgRenderer + Pillow ICO assembly; 358 lines (< 500). Three unit tests cover conversion, CLI seam round-trip, and invalid-SVG rejection. |
| AC7 | evidence/qa-gates/phase4-poetry-lock.md + phase4-poetry-install.md + phase4-pil-import.md | PASS — `pyproject.toml` adds `pillow = "^12.0"`; `poetry lock` succeeded; `poetry install` succeeded; Pillow 12.2.0 importable. |
| AC8 | evidence/qa-gates/phase7-gui-tests.md | PASS — `src/gui/app.py::build_application()` resolves the icon via `resolve_icon_path()` and drives `QApplication.setWindowIcon(QIcon(<resolved-path>))`; `main()` independently sets the icon on the production QApplication. Two new tests in `tests/gui/test_app_composition.py`. |
| AC9 | evidence/qa-gates/phase8-readme-tokens.md | PASS — `packaging/velopack/README.md` contains all required tokens (`MixCalculator`, `MixCalculator.exe`, `Mix Calculator`, `icon-source.svg`, `convert_icon.py`, `Pillow`); pack-identity, outputs, icon sections updated; new "Icon source and regeneration" section added. |
| AC10 | evidence/qa-gates/phase9-black.md + phase9-ruff.md + phase9-pyright.md + phase9-pytest.md + phase9-coverage-changed-modules.md | PASS — Black/Ruff/Pyright clean across the whole repo; 497 tests passing; total line and branch coverage 99%; coverage on changed modules (build_exe, build_velopack, gui/app, gui/_icon) >= 97% line / >= 92% branch; no new suppressions added beyond pre-authorized patterns. |
| AC11 | evidence/qa-gates/phase9-file-size.md | PASS — All 11 new/modified files under 500 lines (max: tests/test_build_velopack.py at 496, src/gui/app.py at 456). |

All 11 acceptance criteria verified PASS.
