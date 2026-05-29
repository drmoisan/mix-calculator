# nuitka-build-exe-script (Issue #29)

- Date captured: 2026-05-29
- Author: Dan Moisan
- Status: Active -> docs/features/active/2026-05-29-nuitka-build-exe-script-29/
- Issue: #29
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/29
- Last Updated: 2026-05-29
- Work Mode: minor-audit
- Promotion Type: feature

## Summary

Add a Python build script, invoked via the Poetry entry point `build-exe`,
that compiles the existing `mix-pipeline-gui` PySide6 application into a
standalone Windows `.exe` using Nuitka. The script encapsulates the correct
flag set (`--standalone`, PySide6 plug-in, pandas/openpyxl inclusions,
output directory) so end-user distribution is reproducible and not subject
to flag drift across developers or CI runs.

This work depends on no other open feature. The Nuitka dependency is
already declared (`nuitka = "^4.1.1"` in `pyproject.toml`). MSVC C++ tools
are installed at `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\`
(verified 2026-05-29); Nuitka auto-detects MSVC via `vswhere` and no
explicit `--msvc` flag is required.

## Environment

- OS: Windows 10/11 (PySide6 distribution target)
- Python: 3.12 - 3.13 (per `pyproject.toml` `python = ">=3.12,<4.0"`)
- Nuitka: ^4.1.1 (already in dev dependencies)
- C compiler: MSVC 14.51.36231 (verified present)
- Entry point being compiled: `src/gui/app.py` (Poetry script `mix-pipeline-gui`)

## Scope

In scope:

- A new module `src/build_exe.py` implementing `main()` and the
  command-resolution and subprocess-invocation logic.
- A new Poetry script entry `build-exe = "src.build_exe:main"` in
  `pyproject.toml`.
- A new test module `tests/test_build_exe.py` exercising argument parsing,
  command resolution, dry-run path, clean-tree path, and exit-code
  propagation.
- A `.gitignore` entry for `dist/nuitka/` if not already covered.

Out of scope:

- Installing or upgrading MSVC C++ tools (owned by
  `scripts/dev-tools/Initialize-DevEnvironment.ps1`).
- Compiling the CLI entry points (`normalize-le`, `load-aop`). Only the
  GUI is compiled by this script.
- A CI workflow that runs the actual Nuitka compile. Compile time and
  environment dependence (multi-minute, MSVC-gated) make CI invocation
  premature; this is documented in the issue and may be revisited.
- A `--onefile` distribution mode. This issue ships `--standalone` only;
  onefile can be added later behind a flag.

## Acceptance Criteria

- [x] AC1: A new Python module `src/build_exe.py` exists with a `main()`
      function and an `argparse`-based CLI accepting at minimum
      `--dry-run` and `--clean`.
- [x] AC2: `pyproject.toml` declares the Poetry entry point
      `build-exe = "src.build_exe:main"` in `[tool.poetry.scripts]`.
- [x] AC3: `poetry run build-exe --dry-run` prints the fully-resolved
      Nuitka command line to stdout and exits 0 without invoking Nuitka.
- [x] AC4: The resolved Nuitka command (verified by AC3 output and by
      unit tests) contains all of the following arguments, in any order:
      `--standalone`, `--enable-plugin=pyside6`, `--include-package=pandas`,
      `--include-package=openpyxl`, `--output-dir=dist/nuitka`, and a
      trailing positional `src/gui/app.py`.
- [x] AC5: `poetry run build-exe --clean` removes the `dist/nuitka/`
      directory tree before building. A unit test verifies the deletion
      happens on the clean path and is a no-op when the directory does
      not exist.
- [x] AC6: When Nuitka exits with a non-zero code, `build-exe` exits
      with the same non-zero code. A unit test verifies propagation via
      a mocked subprocess seam.
- [x] AC7: `tests/test_build_exe.py` exercises: argument parsing,
      command resolution, the dry-run path (no subprocess call), the
      clean path (directory removal), and the exit-code propagation
      path. Line coverage on `src/build_exe.py` is >= 85%; branch
      coverage is >= 75%.
- [x] AC8: `src/build_exe.py` does not exceed 500 lines per
      `.claude/rules/general-code-change.md`. `tests/test_build_exe.py`
      does not exceed 500 lines.
- [x] AC9: The full mandatory toolchain passes on the changed paths in
      a single loop: Black (format) -> Ruff (lint) -> Pyright (type) ->
      Pytest (unit). No suppressions are introduced.
- [x] AC10: `.gitignore` excludes `dist/nuitka/` (or `dist/` if no
      `dist/` entry already exists). The Nuitka output tree is not
      committed.

## Design Notes (for the planner)

- **Subprocess seam**: introduce a thin seam (e.g. a default
  `run_nuitka` callable injected with `subprocess.run` so tests can
  substitute a stub). Tests must not invoke the real Nuitka binary.
- **Entry-module resolution**: the script must resolve
  `src/gui/app.py` from the repository root deterministically (via
  `pathlib.Path(__file__).resolve().parents[1]` or equivalent). The
  resolution must not rely on the current working directory.
- **Output-directory resolution**: identical resolution rule applied to
  `dist/nuitka/`. The directory is created (or its parent confirmed) on
  the non-dry path.
- **Compiler selection**: the script does not pass `--msvc=` explicitly.
  Nuitka 4.x auto-detects MSVC via `vswhere`. If a future requirement
  forces an explicit selection, add a `--compiler {auto,msvc,mingw64}`
  argument with `auto` as default.
- **PySide6 plug-in flag**: use `--enable-plugin=pyside6` (Nuitka's
  canonical flag for PySide6 standalone packaging).
- **Pandas/openpyxl inclusions**: pass `--include-package=pandas` and
  `--include-package=openpyxl` explicitly; do not rely on Nuitka's
  module-graph auto-detection.

## Test Strategy

Unit tests only. No integration test invokes the real Nuitka binary,
because:

- the Nuitka C compile is multi-minute and environment-gated, and
- no CI runner currently has MSVC installed, so an integration test
  would either be skipped uniformly (offering no signal) or would fail
  uniformly (a false negative).

The subprocess seam is the test surface. Tests verify that the correct
argv is passed to the seam, that the seam is or is not invoked depending
on `--dry-run`, that the seam's return code is propagated, and that
`--clean` removes the output tree.

## Out-of-Scope Follow-ups (tracked elsewhere if needed)

- A `--onefile` flag and a separate Poetry entry for onefile builds.
- A CI workflow that runs the full Nuitka compile on a self-hosted
  runner with MSVC pre-installed.
- Compilation of the CLI entry points (`normalize-le`, `load-aop`).
