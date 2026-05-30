# app-rename-and-real-icon (Issue #33)

- Date captured: 2026-05-29
- Author: Dan Moisan
- Status: Active -> docs/features/active/2026-05-29-app-rename-and-real-icon-33/
- Issue: #33
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/33
- Last Updated: 2026-05-29
- Work Mode: minor-audit
- Promotion Type: feature

## Summary

Coordinated three-way alignment of end-user-facing identifiers, plus
replacement of the placeholder application icon with the designed
icon at `artifacts/realgood_calculator_icon.svg`.

Three coordinated changes ship in this single PR:

1. **Nuitka output exe** is renamed from `app.exe` to
   `MixCalculator.exe` via `--output-filename=MixCalculator.exe` in
   `src/build_exe.py`. The new icon is embedded in the exe via
   `--windows-icon-from-ico=...icon.ico` and bundled into the
   standalone tree via `--include-data-file=...icon.ico=icon.ico` so
   the running GUI can load it.
2. **Velopack identifiers align** to the new branding in
   `src/build_velopack.py`: `--packId mix-calculator` becomes
   `--packId MixCalculator`, `--mainExe app.exe` becomes
   `--mainExe MixCalculator.exe`, and `--releaseName "mix-calculator
   <version>"` becomes `--releaseName "Mix Calculator <version>"`.
   The `--packTitle "Mix Calculator"` is unchanged (already
   correctly cased for the display name).
3. **Real icon replaces the placeholder** at
   `packaging/velopack/icon.ico`, derived from the committed source
   SVG at `packaging/velopack/icon-source.svg`. The running GUI sets
   `QApplication.setWindowIcon(QIcon(...))` so the icon also appears
   in the taskbar, title bar, and Alt-Tab preview.

Routed via the minor-audit lifecycle (small path). AC source is this
issue.md (per minor-audit convention).

## Timing constraint

The Velopack `--packId` rename must land BEFORE the first
`vpk upload github` runs. Velopack treats different packIds as
different apps and does not auto-update across them. Once the first
release ships under packId `mix-calculator`, installed users would not
upgrade to a future `MixCalculator` build.

Verified: `gh release list` returns empty for `drmoisan/mix-calculator`.
The rename window is open.

## Environment

- OS: Windows 10/11 (PySide6 distribution target)
- Python: 3.12 - 3.13
- Nuitka: ^4.1.1 (declared in dev deps; consumes
  `--output-filename`, `--windows-icon-from-ico`, `--include-data-file`)
- PySide6: ^6.11.1 (runtime; provides `QtSvg.QSvgRenderer` for the
  SVG -> PNG raster step, and `QtGui.QIcon` for the window icon)
- Pillow: ^12.0 (NEW dev dep; provides multi-size ICO assembly via
  `Image.save(..., format='ICO', sizes=[...])`)
- Velopack CLI: vpk 1.0.1 (no change to vpk version)
- Source icon: `artifacts/realgood_calculator_icon.svg` (47,010 bytes,
  680x460 viewBox; will be cropped to the 680x460 frame's content via
  the SVG's existing clipPath)

## Scope

In scope:

- Modify `src/build_exe.py`: add three Nuitka flags
  (`--output-filename`, `--windows-icon-from-ico`,
  `--include-data-file=...icon.ico=icon.ico`).
- Modify `src/build_velopack.py`: change `--packId`, `--mainExe`, and
  `--releaseName` values.
- Modify `src/gui/app.py` (`build_application()`): call
  `QApplication.setWindowIcon(QIcon(<resolved path>))` with the
  resolved icon path. Resolution probes the compiled-mode location
  first (`Path(sys.executable).parent / "icon.ico"`) and falls back
  to the dev-mode location
  (`Path(__file__).parents[2] / "packaging" / "velopack" / "icon.ico"`).
- Add a new helper `src/gui/_icon.py` (or extend an existing wiring
  module) hosting `resolve_icon_path()` so the resolution logic is
  testable without instantiating a `QApplication`.
- Add `packaging/velopack/convert_icon.py`: a one-shot Python script
  that consumes `packaging/velopack/icon-source.svg` and produces
  `packaging/velopack/icon.ico` via PySide6.QtSvg + Pillow at sizes
  16, 32, 48, 256.
- Commit `packaging/velopack/icon-source.svg` (copied from the
  user-supplied path at `artifacts/realgood_calculator_icon.svg`).
- Regenerate and commit `packaging/velopack/icon.ico` (replacing the
  placeholder).
- Update `packaging/velopack/README.md` to document the rename,
  the icon source, and the conversion command.
- Add `pillow = "^12.0"` under `[tool.poetry.group.dev.dependencies]`
  in `pyproject.toml`. Run `poetry lock` and `poetry install`.
- Modify `tests/test_build_exe.py`, `tests/test_build_velopack.py`,
  and `tests/gui/test_app_composition.py` to reflect the new
  constants and the icon-set behavior.

Out of scope:

- Replacement of the SVG source (the user-supplied SVG is final for
  this PR).
- The Velopack `--packTitle` string (already correctly cased).
- The Python package name in `pyproject.toml`
  (`[tool.poetry] name = "mix-calculator"`); developer-facing only.
- Code signing of `Setup.exe` (still tracked as a separate follow-up).
- In-app update-check UI (still tracked as a separate follow-up).

## Acceptance Criteria

- [x] AC1: `src/build_exe.py` resolves a Nuitka argv that includes,
      in order alongside the existing flags:
      `--output-filename=MixCalculator.exe`,
      `--windows-icon-from-ico=<REPO_ROOT>/packaging/velopack/icon.ico`,
      and `--include-data-file=<REPO_ROOT>/packaging/velopack/icon.ico=icon.ico`.
      A unit test verifies ordered membership of all three flags.
- [x] AC2: `src/build_velopack.py` resolves a `vpk pack` argv where
      `--packId` is `MixCalculator` and `--mainExe` is
      `MixCalculator.exe`. The `--packTitle` argument is unchanged
      at `Mix Calculator`. A unit test verifies the new values.
- [x] AC3: `src/build_velopack.py` resolves a `vpk upload github`
      argv where `--releaseName` is `"Mix Calculator <version>"`.
      A unit test verifies the new value.
- [x] AC4: `packaging/velopack/icon-source.svg` is committed as a
      copy of the user-supplied SVG at
      `artifacts/realgood_calculator_icon.svg`. The file is a valid
      SVG (starts with `<svg`).
- [x] AC5: `packaging/velopack/icon.ico` is a multi-size Windows ICO
      container with frames at 16x16, 32x32, 48x48, and 256x256. The
      magic bytes are `0x00 0x00 0x01 0x00`. Verified by a
      pytest-driven probe of the binary header.
- [x] AC6: `packaging/velopack/convert_icon.py` exists as a
      self-contained one-shot script with a `main()` returning
      exit 0 on success. It uses PySide6's `QSvgRenderer` to
      rasterize each size and Pillow's `Image.save(..., format='ICO')`
      to assemble the multi-size ICO. The script does not exceed 500
      lines. A unit test exercises the conversion with a small
      synthetic SVG fixture (no external assets).
- [x] AC7: `pyproject.toml` adds `pillow = "^12.0"` under
      `[tool.poetry.group.dev.dependencies]`. `poetry.lock` is
      regenerated. `poetry install` resolves cleanly.
- [x] AC8: `src/gui/app.py:build_application()` calls
      `QApplication.setWindowIcon(QIcon(<resolved path>))` after the
      QApplication is constructed, where the path is resolved by a
      new `resolve_icon_path()` helper that probes compiled-mode and
      dev-mode locations in order. A unit test patches `QIcon` and
      asserts the call is made with the expected path string.
- [x] AC9: `packaging/velopack/README.md` documents the new packId,
      mainExe, output filename, releaseName, the icon source path,
      the conversion command, and the dependency on Pillow as a
      dev-only build-time tool.
- [x] AC10: All modified Python files and the new conversion script
      pass Black, Ruff, Pyright, and Pytest with no new suppressions
      beyond pre-authorized patterns. Coverage on changed modules
      remains >= 85% line / >= 75% branch. The full Python suite
      remains green with no regressions.
- [x] AC11: File-size cap (500 lines) is satisfied for every new and
      modified file.

## Test Strategy

- Unit tests for the build argv resolvers
  (`src/build_exe.py:resolve_nuitka_command()`,
  `src/build_velopack.py:resolve_pack_command()`,
  `src/build_velopack.py:resolve_upload_command()`).
- GUI test patches `PySide6.QtGui.QIcon` (and the `QApplication`
  setter) and asserts the resolved path string. No real ICO is
  required for the test to pass.
- Conversion-script test uses a small synthetic in-memory SVG
  fixture (one `<rect>` element), invokes the converter, and verifies
  the produced ICO has the expected magic bytes and frame count via
  Pillow's `Image.open(...).info`.
- No integration test invokes the real Nuitka or vpk binaries
  (consistent with prior PRs #30 and #32).

## Reference Artifacts

- Prior PR #30 (issue #29, Nuitka build pipeline) — established the
  `src/build_exe.py` shape that this PR modifies.
- Prior PR #32 (issue #31, Velopack installer) — established the
  `src/build_velopack.py` shape and the `packaging/velopack/`
  asset folder.
- User-supplied SVG: `artifacts/realgood_calculator_icon.svg`
  (47,010 bytes; black rounded-square app icon depicting a calculator
  with the Realgood Foods logo on the screen and an amber accent
  key).

## Out-of-Scope Follow-ups (tracked elsewhere if needed)

- Code signing of `Setup.exe` (separate PR once a certificate is in
  hand).
- In-app update-check UI.
- CI workflow that builds and uploads on tag push.
- Multi-channel publishing.
