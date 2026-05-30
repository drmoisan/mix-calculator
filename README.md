# mix-calculator

End-to-end tooling for the LE-versus-AOP gross-to-net mix and rate
decomposition. The project ships a CLI (`mix-pipeline`), a PySide6
desktop GUI (`mix-pipeline-gui`), and a build pipeline that compiles
the GUI into a per-user Windows installer (`build-exe` plus
`build-velopack`).

## Contents

- [Development setup](#development-setup)
- [Importing source workbooks](#importing-source-workbooks)
- [Running the mix-decomposition pipeline](#running-the-mix-decomposition-pipeline)
- [Building a Windows distribution](#building-a-windows-distribution)
- [Quality-control toolchain](#quality-control-toolchain)
- [Confidentiality](#confidentiality)

## Development setup

### Prerequisites bootstrap (`Initialize-DevEnvironment.ps1`)

On a fresh clone, run the dev-environment bootstrap. It checks each
host prerequisite in order, asks for confirmation, and installs any
that are missing:

```pwsh
pwsh ./scripts/dev-tools/Initialize-DevEnvironment.ps1 -AutoApprove
```

The bootstrap manages five requirements:

| Requirement | Purpose | Install path |
|---|---|---|
| Python 3.12-3.14 | Runtime / `poetry run ...` | `winget install Python.Python.3.12` |
| Poetry | Dependency manager | Official `install.python-poetry.org` installer |
| MSVC C++ build tools | Backing C compiler used by Nuitka (`build-exe`) | VS Installer modify -> `Microsoft.VisualStudio.Workload.NativeDesktop`, or winget BuildTools |
| vpk (Velopack CLI) | Used by `build-velopack` to produce the installer | `dotnet tool install -g vpk` |
| Project environment | Materializes the in-project `.venv` | `poetry install` |

The MSVC step requires Administrator (the bootstrap triggers UAC for
exactly that child process). `-AutoApprove` (alias `-Force`) skips
all interactive prompts; pass `-DryRun` (or `-WhatIf`) to see what
would change without installing.

### Poetry install

`poetry install` is idempotent and is also the final step run by
the bootstrap. To re-sync after a dependency change:

```sh
poetry install
```

This project uses an in-project virtualenv (`./.venv`). The dev-time
environment additionally depends on `nuitka` (build-exe back-end) and
`pillow` (build-time helper for `convert_icon.py`).

## Importing source workbooks

### LE normalization (`normalize-le`)

`src/normalize_le.py` replicates the as-built Excel "LE-8 + 4"
normalization pipeline. It reads the source sheet into a pandas
DataFrame, validates the schema, rebuilds the `KEY` column, collapses
each `(Customer, SKU #, Type)` key's YTD/YTG rows into a single
full-year row, derives the `YTG` (`sum(May..Dec)`) column, and
persists the result to a SQLite database.

```sh
poetry run normalize-le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE]
```

- `--output` is required and must point at a SQLite database file;
  SQLite is the only output sink. An existing table of the same name
  is dropped and rewritten.
- `--source-sheet` defaults to `"LE-8 + 4"`; `--table-name` defaults
  to `LE`.
- A validation/tie-out summary is printed to stdout; the command
  exits non-zero on any schema or tie-out failure.

See [docs/features/active/2026-05-25-etl-le-topline-input-2/](docs/features/active/2026-05-25-etl-le-topline-input-2/)
for the full specification and acceptance criteria (issue #2).

### AOP load (`load-aop`)

`src/load_aop.py` is a sibling ETL over the `AOP1` sheet. It reads
the sheet into a pandas DataFrame, resolves the schema
position-independently (position pass then fuzzy match >= 0.85),
reconciles the `(Customer, SKU #, Type)` `KEY` via the shared
policy, validates the per-row total identities
(`YTD`, `Q1`..`Q4`, `YTG` against their constituent months),
optionally applies a caller-supplied transform, and persists the
result to a SQLite table with lookup indexes. Unlike `normalize_le`,
it does not collapse rows by `KEY`.

```sh
poetry run load-aop <input.xlsx> --output <path.db> \
  [--source-sheet "AOP1"] [--table-name aop] \
  [--key-mismatch {prompt,trust,overwrite}] \
  [--if-exists {replace,append,fail}] [--snake-case]
```

- `--output` is required and must point at a SQLite database file.
  `--source-sheet` defaults to `"AOP1"`; `--table-name` defaults to
  `aop`.
- `--key-mismatch` (default `prompt`) selects how a present `KEY`
  column that diverges from the rebuilt pattern is resolved;
  `--if-exists` (default `replace`) is passed through to the SQLite
  write boundary.
- `--snake-case` renames columns to snake_case before writing; by
  default the original headers (including the intentional
  `SKU Descripiton` typo) are preserved.
- A load summary is printed to stdout; the command exits non-zero on
  any column-resolution, `KEY`-resolution, or validation failure.

An importable API is also available:

```python
from src.load_aop import load_aop, persist_aop

df = load_aop("path/to/workbook.xlsx", sheet="AOP1")
persist_aop(df, db_path="aop.db", table="aop", if_exists="replace")
```

Both ETLs share domain-agnostic leaf modules —
`src/etl_columns.py`, `src/etl_key.py`, `src/etl_totals.py`, and
`src/pandas_io.py` — so column resolution, `KEY` reconciliation,
blank-total filling, total/months validation, and the pandas
read/write boundary are defined once.

See [docs/features/active/2026-05-26-load-aop-sheet-7/](docs/features/active/2026-05-26-load-aop-sheet-7/)
for the full specification and acceptance criteria (issue #7).

## Running the mix-decomposition pipeline

### CLI (`mix-pipeline`)

`src/mix_pipeline.py` runs the LE-versus-AOP gross-to-net mix and
rate decomposition end-to-end. It reuses the `normalize_le`,
`load_aop`, and `load_skulu` loaders to import the `LE`, `aop`, and
`sku_lu` tables, then runs a chain of pure pandas transforms
(`src/mix_transforms.py`, `src/mix_lookups.py`,
`src/mix_rate_impacts.py`, `src/mix_rollups.py`, `src/mix_q1.py`)
in topological order and persists every derived table into the same
SQLite database. The orchestrator performs all I/O through
`src/pandas_io.py`; the transform modules are pure.

```sh
poetry run python -m src.mix_pipeline --input <workbook.xlsx> \
  --output <database.db> \
  [--le-sheet "LE-8 + 4"] [--aop-sheet "AOP1"] \
  [--skulu-input <workbook.xlsx>] [--skulu-sheet "SKU_LU"]
```

- `--input` and `--output` are required. `--input` supplies the
  `AOP1` and `LE-8 + 4` sheets; the decomp workbook also contains
  `SKU_LU`, so a single `--input` can run the whole pipeline
  end-to-end.
- `--le-sheet` defaults to `"LE-8 + 4"`; `--aop-sheet` defaults to
  `"AOP1"`.
- `--skulu-input` defaults to the value of `--input`;
  `--skulu-sheet` defaults to `"SKU_LU"`. The `SKU_LU` load renames
  `International` to `Country` and maps the `0`/`1` codes to
  `US`/`Canada`.
- A summary of the tables written and their row counts is printed
  to stdout; the command exits `0` on success and `1` on a loader
  column/`KEY`/validation failure.

The pipeline writes the two import tables (`aop`, `LE`) plus
twenty-three derived tables: `le_wide`, `aop_wide`, `customer_lu`,
`sku_lu`, `aop_norm`, `le_norm`, `aop_vs_le`, `mix_base`,
`rate_impacts`, `mix_rollup_1`, `mix_1_sku`, `mix_rollup_2`,
`mix_2_category`, `mix_rollup_3`, `mix_3_customer`, `mix_rollup_4`
(a single-row scalar table), `mix_4_country`, `mix_0_detail`,
`mix_2_sku_bottomsup`, `mix_3_category_bottomsup`,
`mix_4_customer_bottomsup`, `q1_results_by_sku`, and `nrr_summary`
(the appended final summary table).

The three `*_bottomsup` tables (issue #18) decompose the
gross-to-net mix shift at the SKU, category, and customer grains.

`nrr_summary` (issue #15) replicates the workbook's `NRR_Summary`
tab as a tidy long table built purely from the frames above
(`aop_vs_le`, `rate_impacts`, and the four `mix_*` levels). It has
one row per source-tab label, in source order, with columns
`section` (one of `attribute_summary`, `net_revenue_realization`,
`net_pricing_breakdown`, `mix_breakdown`, `reconciliation`),
`metric` (the row label), `aop`, `le`, `value` (the `Abs` change
or `NR $`), `pct` (the `%` change or `%NR`), and `check`. The
final `Check` row carries `"CHECK"` in its `check` column when
the realization-derived Price/Mix and the pricing-plus-mix
build-up reconcile (for both `NR $` and `%NR`), and `"ERROR"`
otherwise. Example shape (fabricated values):

| section | metric | aop | le | value | pct | check |
| --- | --- | --- | --- | --- | --- | --- |
| attribute_summary | Net-Revenue $ | 100.0 | 130.0 | 30.0 | 0.30 | |
| net_revenue_realization | Price/Mix | | | 10.0 | 0.10 | |
| reconciliation | Check | | | | | CHECK |

Joins on `Customer` between the AOP and LE sources are
case-insensitive and whitespace-insensitive (issue #35).
`Winco`, `WINCO`, and `winco` all merge into a single
`(Customer, SKU)` row. The displayed `Customer` casing in the
output frames carries the AOP-side casing when both sides match;
LE-only orphans retain LE casing. The original Customer string is
preserved (no `.title()` / `.upper()` mutation).

See [docs/features/active/2026-05-26-mix-decomp-transforms-9/](docs/features/active/2026-05-26-mix-decomp-transforms-9/)
for the full specification and acceptance criteria (issue #9).

### GUI (`mix-pipeline-gui`)

`src/gui/` provides a PySide6 desktop GUI for the mix-decomposition
pipeline. It uses an MVP (Model-View-Presenter) passive-view
structure: presenters hold the GUI logic (no Qt imports), widgets
are thin views, and services (`PipelineService`, `WorkbookReader`,
`DbService`, `ExporterRegistry`) are constructor-injected at the
composition root. The existing `mix-pipeline` CLI is unchanged;
the GUI calls the same loaders and transform chain through a
service seam.

```sh
poetry run mix-pipeline-gui
```

The main window hosts a per-input file/sheet selector for LE, AOP,
and SKU_LU with the default sheet names pre-filled:

- LE default sheet: `"LE-8 + 4"`
- AOP default sheet: `"AOP1"`
- SKU_LU default sheet: `"SKU_LU"`

Workflow:

1. Select an Excel workbook and pick a worksheet tab for each
   input. Selecting a file populates the tab dropdown. An optional
   "render tab" checkbox shows a bounded preview (200 rows) of the
   chosen tab.
2. Import one selected input or all selected inputs.
3. Run the pipeline. The run executes off the UI thread via a
   `QObject` worker on a `QThread`; the status bar reflects the
   running state.
4. Save the working tables to a SQLite `.db` file. Save uses
   `if_exists="replace"` table semantics, matching the CLI output
   sink.
5. Open an existing `.db` to repopulate the working tables.
6. Export selected tables via the Export dialog (per-table
   checklist plus an Export-All control). Excel writes one
   worksheet per selected table; CSV writes one CSV file per
   selected table into a destination directory. The format set is
   extensible by registering a new exporter — no presenter change
   required.

Headless testing uses the offscreen Qt platform plugin:

```sh
QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui
```

The repository's `tests/gui/conftest.py` pins
`QT_QPA_PLATFORM=offscreen` for the whole session so widget and
worker tests run without a display server.

The running GUI sets its window icon at startup via
`QApplication.setWindowIcon(QIcon(resolve_icon_path()))`. The
helper at `src/gui/_icon.py` probes the compiled-mode location
(`Path(sys.executable).parent / "icon.ico"`) first, then falls
back to the dev-mode location
(`<repo>/packaging/velopack/icon.ico`).

See [docs/features/active/2026-05-27-mix-pipeline-gui-19/](docs/features/active/2026-05-27-mix-pipeline-gui-19/)
for the full specification and acceptance criteria (issue #19).

## Building a Windows distribution

The build pipeline produces a per-user Windows installer in two
steps: first `build-exe` compiles the GUI into a standalone folder
distribution, then `build-velopack` wraps that folder into an
installer. The Velopack installer drops the application into
`%LocalAppData%\MixCalculator\` without requesting admin
privileges and supports built-in delta auto-update via GitHub
Releases.

### Standalone executable (`build-exe`)

`src/build_exe.py` invokes Nuitka to compile `src/gui/app.py` into
a Windows binary called `MixCalculator.exe` plus a folder of
bundled DLLs and Python runtime. The invocation pins the flag set
(no auto-detection, no flag drift):

```sh
poetry run build-exe [--dry-run] [--clean]
```

- `--dry-run` prints the resolved Nuitka argv to stdout and exits
  `0` without invoking Nuitka.
- `--clean` removes the existing `dist/nuitka/` tree before
  building.
- The default invocation pins
  `--standalone --enable-plugin=pyside6 --include-package=pandas
  --include-package=openpyxl --output-dir=dist/nuitka
  --output-filename=MixCalculator.exe
  --windows-icon-from-ico=packaging/velopack/icon.ico
  --include-data-file=packaging/velopack/icon.ico=icon.ico`.

On a Windows host with MSVC installed, the compile typically
takes several minutes and produces:

| Path | Role |
|---|---|
| `dist/nuitka/MixCalculator.dist/MixCalculator.exe` | The compiled binary (icon embedded as a Win32 resource) |
| `dist/nuitka/MixCalculator.dist/icon.ico` | The bundled icon for runtime `setWindowIcon` lookups |
| `dist/nuitka/MixCalculator.dist/` (rest) | CPython runtime, PySide6/Qt DLLs, pandas/numpy/openpyxl binaries |
| `dist/nuitka/MixCalculator.build/` | Scratch C source + object files (deletable after the build) |

Subprocess seam: `src/build_exe.py` calls
`subprocess.run([sys.executable, "-m", "nuitka", ...])` via an
injected callable so tests can substitute a recorder. Tests never
invoke the real Nuitka binary.

See [docs/features/active/2026-05-27-nuitka-build-exe-script-29/](docs/features/active/2026-05-27-nuitka-build-exe-script-29/)
for the full specification and acceptance criteria (issue #29).

### Per-user installer (`build-velopack`)

`src/build_velopack.py` wraps the standalone Nuitka folder into a
Velopack installer (`vpk` CLI). The resulting `Setup.exe` installs
to `%LocalAppData%\MixCalculator\` without UAC and ships built-in
delta auto-update from a remote channel.

```sh
poetry run build-velopack [--dry-run] [--clean] [--version <semver>] \
                          [--upload] [--release-dir <path>]
```

- `--dry-run` prints the resolved `vpk pack` argv and exits `0`.
- `--clean` removes `dist/velopack/` before building.
- `--version <semver>` overrides the version embedded in the
  installer. Defaults to the `tool.poetry.version` value in
  `pyproject.toml`. Four-part versions (`1.0.0.0`) are rejected
  per Velopack's documented constraint.
- `--release-dir <path>` overrides the default
  `dist/velopack/` output directory.
- `--upload` invokes `vpk upload github` after a successful pack
  to publish the release to the project's GitHub Releases. Requires
  `GITHUB_TOKEN` in the environment with `contents: write`
  permission. The logged form of the command has the token replaced
  by `<REDACTED>`; the executed argv keeps the real token.

The script does NOT run `build-exe` itself. Run `build-exe` first;
`build-velopack` exits `2` with a clear message if
`dist/nuitka/MixCalculator.dist/MixCalculator.exe` is missing.

The pack step produces, in `dist/velopack/`:

| File | Role |
|---|---|
| `MixCalculator-Setup.exe` | The bootstrap installer for end users (no admin) |
| `MixCalculator-<version>-full.nupkg` | Complete update package |
| `MixCalculator-<version>-delta.nupkg` | Incremental delta against the prior release (second release onward) |
| `MixCalculator-Portable.zip` | Portable archive for users who do not want the installer |
| `releases.win.json` | Channel manifest read by Velopack's `UpdateManager` at runtime |
| `assets.win.json`, `RELEASES` | Bookkeeping / legacy Squirrel manifest |

The unsigned `Setup.exe` triggers a Windows SmartScreen warning on
first run ("Windows protected your PC" → "More info" → "Run
anyway"). Code-signing is a follow-up.

See [docs/features/active/2026-05-29-velopack-installer-31/](docs/features/active/2026-05-29-velopack-installer-31/)
for the full specification and acceptance criteria (issue #31)
and [docs/features/active/2026-05-29-app-rename-and-real-icon-33/](docs/features/active/2026-05-29-app-rename-and-real-icon-33/)
for the MixCalculator rename and icon work (issue #33).

### Regenerating the application icon (`convert_icon`)

The committed `packaging/velopack/icon.ico` is generated from
`packaging/velopack/icon-source.svg` via a one-shot Python script.
Pillow (a dev dependency) is required:

```sh
poetry run python packaging/velopack/convert_icon.py \
  [--input packaging/velopack/icon-source.svg] \
  [--output packaging/velopack/icon.ico]
```

The script rasterizes the SVG at 16, 32, 48, and 256 px via
PySide6's `QSvgRenderer` (a runtime dependency) and assembles the
multi-size ICO via Pillow's native ICO writer
(`Image.save(..., format='ICO', sizes=[(16,16),(32,32),(48,48),(256,256)])`).
No native Cairo library is required. After regenerating, commit
the updated ICO and run `build-exe` + `build-velopack` to rebuild
the installer.

The icon embeds in three places: the compiled binary's Win32
resource (via Nuitka's `--windows-icon-from-ico`), the standalone
tree's root (via `--include-data-file=...icon.ico=icon.ico` for
runtime `setWindowIcon` lookups), and the Velopack `Setup.exe`
(via `vpk pack --icon`).

## Quality-control toolchain

Run in order; restart from the top if any step modifies files:

```sh
poetry run black .                                  # 1. format
poetry run ruff check .                             # 2. lint
poetry run pyright                                  # 3. type-check
poetry run pytest --cov=src --cov-branch --cov-report=term-missing  # 4. test
```

Coverage thresholds are uniform across all module tiers (T1-T4)
per [.claude/rules/quality-tiers.md](.claude/rules/quality-tiers.md):

| Gate | Threshold |
|---|---|
| Line coverage | >= 85% |
| Branch coverage | >= 75% |
| No regression on changed lines | required |

PowerShell sources under `scripts/dev-tools/` use the PoshQC
toolchain (format -> analyze -> Pester) via the bundled MCP
commands. PowerShell follows the same uniform coverage thresholds.

Poetry quirk: on some hosts the ambient `VIRTUAL_ENV` environment
variable points at the global Python instead of the in-project
`.venv`. Prefix Poetry invocations with `env -u VIRTUAL_ENV` so
installs and runs target the project venv:

```sh
env -u VIRTUAL_ENV poetry install
env -u VIRTUAL_ENV poetry run pytest
```

## Confidentiality

The source workbooks (for example
`artifacts/LE v AOP Gross to Net Decomp.xlsx`,
`artifacts/Input Files.xlsx`) and any output `.db` are gitignored
and must remain untracked.

`SKU Description` and `Category` values from `SKU_LU` are
confidential and never appear in tests, fixtures, or docs; only
fabricated examples (for example `SKU-001`, `Widget A`,
`Category X`, `Acme Foods`) are used.

The `US`/`Canada` country values and the public customer names
that appear in the canonical training workbook are not secret.

Computed workbook aggregates (mix totals, sums) are also treated as
confidential and must be described qualitatively rather than
quoted with concrete figures in committed files.
