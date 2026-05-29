# nuitka-build-exe-script (Issue #29)

- Date captured: 2026-05-29
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/nuitka-build-exe-script/ (Issue #29)

- Issue: #29
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/29
- Last Updated: 2026-05-29
## Problem / Why

The repository declares `nuitka = "^4.1.1"` as a dev dependency and exposes
a PySide6 GUI via the `mix-pipeline-gui` Poetry script (entry point
`src.gui.app:main`). End-user distribution requires producing a standalone
Windows `.exe` for the GUI, but no reproducible invocation of Nuitka is
checked in. Developers must reconstruct the correct flag set by memory each
time, which is error-prone for a multi-package project (PySide6, pandas,
openpyxl) where plug-in selection and data-file inclusion are non-obvious.

## Proposed Behavior

Add a Python build script invoked via a Poetry entry point that:

1. Resolves the GUI entry module (`src/gui/app.py`).
2. Invokes Nuitka with `--standalone`, the PySide6 plug-in enabled,
   pandas/openpyxl module inclusion, and an output directory under
   `dist/nuitka/`.
3. Defaults to the MSVC C++ back-end on Windows when present (just verified
   at `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC`).
4. Surfaces Nuitka's exit code so CI or developers can detect failure.
5. Supports `--dry-run` to print the resolved Nuitka command without
   executing the compile, and a `--clean` flag to remove `dist/nuitka/`
   before building.

## Acceptance Criteria (early draft)

- [ ] AC1: `poetry run build-exe --dry-run` prints the fully-resolved
      Nuitka command line and exits 0 without invoking the compiler.
- [ ] AC2: `poetry run build-exe` (no flags) invokes Nuitka with
      `--standalone --enable-plugin=pyside6 --output-dir=dist/nuitka` and
      produces `dist/nuitka/app.dist/app.exe` on a host with MSVC present.
- [ ] AC3: The script exits non-zero when Nuitka exits non-zero, surfacing
      the underlying exit code.
- [ ] AC4: `poetry run build-exe --clean` removes the existing
      `dist/nuitka/` tree before building; the flag has no effect on a
      fresh tree.
- [ ] AC5: The script has unit tests covering: argument parsing,
      command-line resolution, dry-run path, clean-tree path, and
      exit-code propagation. Coverage on the new module is >= 85% line
      and >= 75% branch (uniform threshold per `quality-tiers.md`).
- [ ] AC6: The script does not exceed 500 lines and complies with the
      mandatory toolchain loop (Black -> Ruff -> Pyright -> Pytest).

## Constraints & Risks

- The Nuitka C compile is environment-dependent. On a fresh clone without
  MSVC, the script will fail at the back-end compile stage. The script
  must not attempt to install MSVC itself; that remains the responsibility
  of `scripts/dev-tools/Initialize-DevEnvironment.ps1`.
- PySide6 plug-in inclusion is mandatory for the GUI to start; omitting it
  produces a binary that exits silently at startup. The script must enable
  the plug-in unconditionally.
- The pandas wheel ships compiled extensions that Nuitka must include via
  `--include-package=pandas` (and similar for openpyxl). The script must
  declare these inclusions explicitly rather than relying on Nuitka's
  auto-detection.
- Output directory (`dist/nuitka/`) is not currently in `.gitignore`. The
  active feature should confirm whether `dist/` requires an ignore entry.

## Test Conditions to Consider

- [ ] Unit: argparse contract (`--dry-run`, `--clean`, default flags).
- [ ] Unit: command-line resolution emits the expected Nuitka argv with
      `--standalone`, `--enable-plugin=pyside6`, `--output-dir=dist/nuitka`,
      `src/gui/app.py`, and pandas/openpyxl `--include-package` flags.
- [ ] Unit: subprocess seam is invoked exactly once on the non-dry path and
      not invoked on the dry path.
- [ ] Unit: `--clean` deletes `dist/nuitka/` only when it exists; no error
      when absent.
- [ ] Unit: non-zero Nuitka exit code is propagated.
- [ ] No integration test runs the actual Nuitka compile in CI (compile is
      multi-minute and environment-gated); this is documented in the spec.

## Next Step

- [x] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/nuitka-build-exe-script/` folder from the template