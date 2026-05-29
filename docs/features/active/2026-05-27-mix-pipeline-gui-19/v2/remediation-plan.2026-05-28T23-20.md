# Atomic Remediation Plan — mix-pipeline-gui (Issue #19) v2

- **Issue:** #19
- **Cycle:** 1 (first remediation cycle of v2)
- **Status:** Draft
- **Feature folder:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
- **Work Mode:** full-feature (resolved from `v2/issue.md` metadata marker `- Work Mode: full-feature`)
- **Plan generated:** 2026-05-28T23-20
- **Requirements sources:** `v2/remediation-inputs.2026-05-28T23-20.md`, `v2/policy-audit.2026-05-28T23-20.md`, `v2/code-review.2026-05-28T23-20.md`, `v2/feature-audit.2026-05-28T23-20.md`, `v2/spec.md`
- **Implementing worker:** `atomic-executor` (strict-handoff protocol; preflight then execute)
- **Per-batch budget (hard):** at most 3 production files AND 3 test files per phase
- **Language in scope:** Python (Black -> Ruff -> Pyright strict -> Pytest with coverage)
- **Coverage gate:** line >= 85%, branch >= 75%, no regression on changed lines

## Evidence Location Invariant

All remediation evidence artifacts for this cycle are written under the canonical v2
evidence root: `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/<kind>/`
per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Cycle 1 evidence sits
alongside the original v2 execution evidence; the new artifacts use the
`2026-05-28T23-20` timestamp to distinguish them from the `2026-05-28T22-10` execution
artifacts. Non-canonical locations (`artifacts/baselines/`, `artifacts/baseline/`,
`artifacts/qa/`, `artifacts/qa-gates/`, `artifacts/evidence/`, `artifacts/coverage/`)
are forbidden. Any supplied non-canonical path is rejected and replaced with the
canonical path; the override is recorded as
`EVIDENCE_LOCATION_OVERRIDE_REJECTED: <supplied> replaced with <canonical>`.

## Reused Modules (do not duplicate; modify only as listed)

Cycle 1 is a remediation on the v2 HEAD. The following modules are touched:

Production (modified in place):

- `src/gui/app.py` (492/500 lines at HEAD) — extend `build_application` with optional `exporter_registry` keyword parameter; update `WiredApplication` docstring `Attributes:` block to note registry source.
- `src/gui/presenters/pipeline_presenter.py` (496/500 lines at HEAD) — remove the production-source test seam `set_imported_tables_for_test`.

Tests (modified in place):

- `tests/gui/integration/test_behavioral_dialogs.py` — rewrite the CSV behavioral test for in-memory capture; replace four `set_imported_tables_for_test` call sites with `FakePipelineService`-driven imports through `on_import_one`; reword the docstring on `test_export_csv_routes_destination_to_csv_exporter` to match the new assertions.
- `tests/gui/integration/test_behavioral_pipeline_run.py` — replace two `set_imported_tables_for_test` call sites with `FakePipelineService`-driven imports through `on_import_one`.
- `tests/gui/test_app_wiring.py` — add one positive test asserting an injected `exporter_registry` is used by `build_application`.

Reused (unchanged this cycle):

- `tests/gui/fakes/fake_exporters.py` — existing recording fake remains; may be reused by the rewritten CSV behavioral test for in-memory capture if its surface is suitable, otherwise the test constructs `CsvExporter(open_writer=<in-memory capture>)` directly.
- `tests/gui/fakes/fake_services.py` — `FakePipelineService` already supports `import_le` / `import_aop` / `import_skulu` / `open_db` injection from v2; no changes required.
- `src/gui/exporters/csv_exporter.py` — unchanged; the existing `open_writer` constructor seam is the injection point used by the rewritten behavioral test.
- `src/gui/exporters/registry.py` — unchanged.
- All other v2 modules unchanged.

## Confidentiality Invariant (per-phase acceptance check)

No real `SKU Description` or `Category` values, customer names, SKU numbers,
prices, or discounts may appear in any new or modified source file, test file,
fixture, or doc. Fabricated values only (for example `Acme Foods`, `SKU-1001`,
`Example-A`, `Category X`). The `Country` values `US` and `Canada` are not
secret.

## Dependency and Tier Invariants

- Cycle 1 adds no new dependency. PySide6 and `pytest-qt` are already declared.
- No new module is created; `quality-tiers.yml` requires no change this cycle.
- Headless Qt tests continue to run under `QT_QPA_PLATFORM=offscreen` via `tests/gui/conftest.py`.

## Toolchain Loop (run per implementation phase, in order)

`poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` ->
`QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`.
Restart from Black if any step fails or changes files. Per
`.claude/rules/general-unit-test.md`, the banned APIs `time.sleep`,
`QThread.sleep`, `QTest.qWait`, and `qtbot.waitUntil` must not appear in the
modified behavioral test code.

---

### Phase 0 — Baseline Capture and Policy Reads

Budget: 0 production files, 0 test files (capture only).

- [x] [P0-T1] Read repository policy files in the required order and record an evidence artifact at `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/other/phase0-instructions-read.2026-05-28T23-20.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`. Acceptance: artifact exists with all three fields populated.
- [x] [P0-T2] Capture the four-tool baseline of the v2 HEAD (post-execution working tree) by running, in order, `poetry run black --check .`, `poetry run ruff check .`, `poetry run pyright`, and `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write a single combined artifact at `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/baseline/baseline.2026-05-28T23-20.md` containing one section per command, each with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. The pytest section's `Output Summary:` MUST record numeric line-coverage % and branch-coverage % and the passed/failed counts. Acceptance: artifact exists; every command section has the four schema fields; pytest section's coverage values are numeric (not placeholders); confirm that `git status` after the pytest run is clean (the cycle's premise is that this baseline already leaks `results_*.csv` — if so, record the leak in `Output Summary:` and remove the leaked files before continuing). If the `offscreen` plugin does not load or any baseline value cannot be captured, the phase outcome is remediation-required, not PASS.

---

### Phase 1 — `build_application` registry-injection seam

Budget: 1 production file (`src/gui/app.py`), 1 test file (`tests/gui/test_app_wiring.py`). DAG layer: composition-root seam enabling the cycle-1 behavioral test to inject an in-memory CSV writer.

- [x] [P1-T1] Update `src/gui/app.py::build_application` to add a new keyword-only parameter `exporter_registry: ExporterRegistry | None = None` (place it at the end of the existing keyword block, after `workbook_reader`). Update the body so the local `registry` assignment becomes `registry = exporter_registry if exporter_registry is not None else _build_registry()`. Update the `build_application` docstring `Args:` block to document the new parameter with rationale (test seam for in-memory CSV capture; defaults to the production `_build_registry()` so production wiring is unchanged). Update `WiredApplication.registry` `Attributes:` docstring line to note that the registry may be the injected one when supplied. Full type hints; Google-style docstrings. No other behavior change. Acceptance: `grep -n "exporter_registry" src/gui/app.py` shows the new parameter on `build_application` and the `if ... is not None else _build_registry()` resolution; `src/gui/app.py` remains <= 500 lines; `poetry run pyright src/gui/app.py` exits 0; the production `main()` path still constructs the registry via `_build_registry()` (no production call passes `exporter_registry`).
- [x] [P1-T2] Extend `tests/gui/test_app_wiring.py` with one new positive test `test_build_application_uses_injected_exporter_registry`: construct an `ExporterRegistry` whose `"CSV"` entry is a `CsvExporter(open_writer=<lambda path: io.StringIO()>)`; call `build_application(qt_app=qtbot.qapp, runner=SynchronousRunner(), save_path_chooser=lambda: None, open_path_chooser=lambda: None, export_dialog_runner=lambda d: None, exporter_registry=injected)`; assert `wired.registry is injected`; assert `wired.registry.get("CSV") is injected.get("CSV")`. Add a complementary assertion that when `exporter_registry is None`, `wired.registry.available_formats() == ["Excel", "CSV"]` (existing behavior preserved). Use Arrange-Act-Assert. No banned APIs. Acceptance: the new test plus the complementary default-path assertion pass; `tests/gui/test_app_wiring.py` remains <= 500 lines; the existing tests in that file continue to pass.
- [x] [P1-T3] Run the toolchain loop and persist per-command evidence to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/phase1-qa.2026-05-28T22-10` is the v2 execution artifact; this cycle's artifact is `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/phase1-qa.2026-05-28T23-20.md` with one section per command, each carrying `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Order: Black -> Ruff -> Pyright -> `QT_QPA_PLATFORM=offscreen` Pytest with coverage. Restart from Black on any failure/change. Acceptance: all four commands exit 0 in one pass; coverage line >= 85% and branch >= 75% with no regression on changed lines; no unauthorized suppressions; confidentiality check passes.

---

### Phase 2 — Remove `PipelinePresenter.set_imported_tables_for_test`

Budget: 1 production file (`src/gui/presenters/pipeline_presenter.py`), 2 test files (`tests/gui/integration/test_behavioral_dialogs.py`, `tests/gui/integration/test_behavioral_pipeline_run.py`). DAG layer: remove the production-source test seam and migrate all callers to the standard injectable paths.

- [x] [P2-T1] Update `src/gui/presenters/pipeline_presenter.py` to delete the `set_imported_tables_for_test` method (currently at line 124). Remove any docstring or comment that references the removed method. Confirm no other production module imports or calls the method (`grep -n "set_imported_tables_for_test" src/` returns no matches after the edit). Acceptance: `grep -n "set_imported_tables_for_test" src/gui/presenters/pipeline_presenter.py` returns no matches; the file remains <= 500 lines; `poetry run pyright src/gui/presenters/pipeline_presenter.py` exits 0; no production caller of the removed method remains in `src/`.
- [x] [P2-T2] Update `tests/gui/integration/test_behavioral_pipeline_run.py` to replace the two `set_imported_tables_for_test` call sites (lines 63 and 78 at HEAD) with `FakePipelineService`-driven imports through the standard presenter path. For each affected test: configure the `FakePipelineService` with `import_result=_fake_imports()` (the v2 fake already supports this); after constructing `wired`, drive `wired.pipeline_presenter.on_import_one("LE", ImportSpec(le_path=..., aop_path=None, skulu_path=None))` (and analogous calls for `"aop"` and `"sku_lu"`) OR drive `wired.pipeline_presenter.on_import_all(ImportSpec(le_path=..., aop_path=..., skulu_path=...))` so that `_imported_tables` is populated through the production path. Preserve every existing positive and negative assertion in those tests. No banned APIs (`time.sleep`, `qtbot.waitUntil`, `QTest.qWait`, `QThread.sleep`). Acceptance: `grep -n "set_imported_tables_for_test" tests/gui/integration/test_behavioral_pipeline_run.py` returns no matches; the file remains <= 500 lines; all tests in that file pass under `QT_QPA_PLATFORM=offscreen`.
- [x] [P2-T3] Update `tests/gui/integration/test_behavioral_dialogs.py` to replace the four `set_imported_tables_for_test` call sites (lines 69, 80, 143, 173 at HEAD) with `FakePipelineService`-driven imports through the standard presenter path, using the same `on_import_one` / `on_import_all` pattern as P2-T2. The CSV behavioral test at line 150 will be fully rewritten in P3-T1 — replacing its call site here is acceptable because the line will be overwritten in P3; nevertheless, the other three call sites in this file MUST be migrated in this task. Preserve all existing assertions. No banned APIs. Acceptance: after P2-T3 (before P3-T1), `grep -n "set_imported_tables_for_test" tests/gui/integration/test_behavioral_dialogs.py` returns either no matches OR only the one residual occurrence inside `test_export_csv_routes_destination_to_csv_exporter` which P3-T1 will remove; the file remains <= 500 lines; all tests in that file pass under `QT_QPA_PLATFORM=offscreen`.
- [x] [P2-T4] Run the toolchain loop and persist per-command evidence to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/phase2-qa.2026-05-28T23-20.md` with one section per command. Order: Black -> Ruff -> Pyright -> `QT_QPA_PLATFORM=offscreen` Pytest with coverage. Restart from Black on any failure/change. Acceptance: all four commands exit 0 in one pass; coverage line >= 85% and branch >= 75% with no regression on changed lines; `grep -n "set_imported_tables_for_test" src tests` returns at most the one residual occurrence in `test_export_csv_routes_destination_to_csv_exporter` (to be removed in P3); confidentiality check passes.

---

### Phase 3 — Rewrite the CSV behavioral test for in-memory capture

Budget: 0 production files, 1 test file (`tests/gui/integration/test_behavioral_dialogs.py`). DAG layer: remediate R-1 by eliminating the CSV disk-write side effect and asserting the per-table writes via captured payloads.

- [x] [P3-T1] Rewrite `tests/gui/integration/test_behavioral_dialogs.py::test_export_csv_routes_destination_to_csv_exporter` so that no `results_*.csv` files are written to disk during the test. Concretely: (a) construct an in-memory writer capture as `captured_writes: dict[str, io.StringIO] = {}` and a closure `def _capture_open_writer(path: str) -> io.StringIO: buf = io.StringIO(); captured_writes[path] = buf; return buf`; (b) build an `ExporterRegistry` whose `"Excel"` entry is the production `ExcelExporter()` (or a recording fake) and whose `"CSV"` entry is `CsvExporter(open_writer=_capture_open_writer)`; (c) call `build_application(runner=SynchronousRunner(), pipeline_service=service, workbook_reader=fake_reader, save_path_chooser=lambda: None, open_path_chooser=lambda: None, export_dialog_runner=_runner, exporter_registry=injected)` where `_runner` returns `("CSV", "C:/tmp/results.csv")` after `dialog.select_all_tables()`; (d) drive imports via `FakePipelineService` and the standard `on_import_all` (or three `on_import_one`) calls so that `_imported_tables` contains the three fabricated tables (replacing the residual `set_imported_tables_for_test` call); (e) `_click(qtbot, wired.window.export_btn)`; (f) assert `set(captured_writes.keys()) == {os.path.join("C:/tmp", "results_LE.csv"), os.path.join("C:/tmp", "results_aop.csv"), os.path.join("C:/tmp", "results_sku_lu.csv")}` (build the expected paths with `os.path.join` to remain OS-independent); (g) assert each captured `StringIO.getvalue()` is non-empty (the exporter wrote table content). Reword the test docstring to: "AC-9 CSV behavioral path: the export click path routes the dialog's CSV format/path through `ExportPresenter` and the registry to `CsvExporter`, which writes one per-table file via the injected in-memory `open_writer`. Verifies the per-table key set and that each capture is non-empty; the name-mangling unit contract is covered by `tests/gui/test_csv_exporter.py`." No banned APIs (`time.sleep`, `qtbot.waitUntil`, `QTest.qWait`, `QThread.sleep`); confidentiality invariant honored (fabricated values only). After the test runs, `git status` MUST show no untracked `results_*.csv` (or other test-output) files. Acceptance: the rewritten test passes under `QT_QPA_PLATFORM=offscreen`; `grep -n "set_imported_tables_for_test" tests/gui/integration/test_behavioral_dialogs.py` returns no matches; `grep -nE "results_LE\.csv|results_aop\.csv|results_sku_lu\.csv" tests/gui/integration/test_behavioral_dialogs.py` matches the three expected file names inside the assertions; the file remains <= 500 lines; `git status` after the pytest run shows no untracked `results_*.csv`.
- [x] [P3-T2] Run the toolchain loop and persist per-command evidence to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/phase3-qa.2026-05-28T23-20.md` with one section per command. Order: Black -> Ruff -> Pyright -> `QT_QPA_PLATFORM=offscreen` Pytest with coverage. Restart from Black on any failure/change. Acceptance: all four commands exit 0 in one pass; coverage line >= 85% and branch >= 75% with no regression on changed lines; pytest `Output Summary:` records numeric post-cycle coverage values; the pytest run leaves no untracked `results_*.csv` (record this observation under `Output Summary:`).

---

### Phase 4 — Final QA Loop, Coverage Delta, and DoD Verification

Budget: 0 production files, 0 test files (verification and coverage-delta only).

- [x] [P4-T1] Run `poetry run black .` on the post-remediation HEAD and write the result to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/final-black.2026-05-28T23-20.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact exists with all four fields; `EXIT_CODE: 0`; `Output Summary:` reports no files reformatted.
- [x] [P4-T2] Run `poetry run ruff check .` on the post-remediation HEAD and write the result to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/final-ruff.2026-05-28T23-20.md` with the four schema fields. Acceptance: `EXIT_CODE: 0`; `Output Summary:` reports 0 errors; any suppression present matches a pre-authorized pattern in `.claude/rules/python-suppressions.md`.
- [x] [P4-T3] Run `poetry run pyright` on the post-remediation HEAD and write the result to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/final-pyright.2026-05-28T23-20.md` with the four schema fields. Acceptance: `EXIT_CODE: 0`; `Output Summary:` reports 0 errors and 0 warnings; no `Any` introduced and no strictness reduction.
- [x] [P4-T4] Run `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` on the post-remediation HEAD and write the result to `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md` with the four schema fields. Verify via `git status` (recorded in `Output Summary:`) that no untracked `results_*.csv` files were created by the test run. Acceptance: `EXIT_CODE: 0`; `Output Summary:` records numeric post-remediation line-coverage % and branch-coverage % and the passed/failed test counts; line >= 85% and branch >= 75%; `git status` excerpt in the summary shows no `results_*.csv` artifacts.
- [x] [P4-T5] Compute the coverage delta against the v2 execution baseline (`v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md`) and against the cycle-1 baseline (`v2/evidence/baseline/baseline.2026-05-28T23-20.md`) and write `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/coverage-delta.2026-05-28T23-20.md` reporting: v2 execution baseline line/branch %, cycle-1 baseline line/branch %, post-remediation line/branch %, and the deltas. Baseline and post values are read from on-disk evidence; no hard-coded numbers in the plan or artifact. Acceptance: artifact exists with `Timestamp:`, the three measured points, and the deltas; confirms line >= 85% / branch >= 75% repository-wide and no regression on changed lines. If any required coverage value is unavailable, the outcome is remediation-required, not PASS.
- [x] [P4-T6] Verify the v2 Definition of Done holds after remediation by re-checking that AC-1 through AC-12 in `v2/issue.md` each map to at least one passing test, and that AC-9's behavioral verification is now disk-free. Write `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/other/dod-traceability.2026-05-28T23-20.md` with `Timestamp:` and a table mapping each AC to its verifying unit/integration test(s) AND its verifying behavioral integration test file(s), with pass status for each. AC-9's row MUST explicitly note "disk-free; per-table writes captured via injected in-memory `open_writer`." The confidentiality invariant (no `SKU Description`/`Category` values, no real customer/SKU data) is confirmed across all modified test files. Acceptance: artifact exists; every AC-1 through AC-12 maps to at least one passing test; AC-9 row shows the disk-free verification path; no DoD item is unverified.

---

## Acceptance-Criteria Coverage Map (v2/issue.md, post-remediation)

| AC | Title | Cycle 1 impact | Verifying unit/integration test(s) | Verifying behavioral test (tests/gui/integration/) |
|---|---|---|---|---|
| AC-1 | Render Tab renders an image of the selected worksheet | unchanged | `test_source_selection_presenter`, `test_source_input_widget`, `test_preview_widget` | `test_behavioral_preview.py` |
| AC-2 | Import LE wires to pipeline and disables on success | unchanged | `test_pipeline_presenter` | `test_behavioral_import_buttons.py` |
| AC-3 | Import AOP wires to pipeline and disables on success | unchanged | `test_pipeline_presenter` | `test_behavioral_import_buttons.py` |
| AC-4 | Import SKU_LU wires to pipeline and disables on success | unchanged | `test_pipeline_presenter` | `test_behavioral_import_buttons.py` |
| AC-5 | Import All runs all three imports and disables all four | unchanged | `test_pipeline_presenter` | `test_behavioral_import_buttons.py` |
| AC-6 | Run executes transformation end-to-end | bootstrap via `on_import_one`/`on_import_all` instead of removed test seam (P2-T2) | `test_runners`, `test_pipeline_presenter`, `test_pipeline_worker`, `test_pipeline_service` | `test_behavioral_pipeline_run.py` |
| AC-7 | Save persists working tables to SQLite `.db` | bootstrap via `on_import_*` instead of removed test seam (P2-T3) | `test_pipeline_presenter`, `test_app_wiring` | `test_behavioral_dialogs.py` |
| AC-8 | Open loads tables and reflects load state on import buttons | unchanged | `test_pipeline_presenter`, `test_app_wiring` | `test_behavioral_dialogs.py` |
| AC-9 | Export opens file dialog with Excel/CSV format choices and exports through registry | behavioral verification is now disk-free (P3-T1); injected registry seam added (P1-T1, P1-T2) | `test_export_dialog`, `test_app_wiring_defaults`, `test_csv_exporter` (name-mangling unit contract), `test_export_presenter`, `test_app_wiring` (registry injection) | `test_behavioral_dialogs.py` (in-memory `open_writer` capture) |
| AC-10 | Composition root wires all signals to behavioral handlers | unchanged | `test_app_wiring`, `test_app_composition` | `test_behavioral_composition.py` |
| AC-11 | Presentation logic remains testable without a live Qt event loop | strengthened: production seam `set_imported_tables_for_test` removed (P2-T1); tests use injectable service path | every `test_*_presenter.py`; `test_runners.py` | n/a (unit invariant) |
| AC-12 | Full toolchain passes and coverage thresholds hold | reverified at `2026-05-28T23-20` | `final-black`, `final-ruff`, `final-pyright`, `final-pytest-coverage`, `coverage-delta` | n/a (gate) |

## Per-Phase File-Budget Check (hard cap: 3 production AND 3 test files)

| Phase | Production files | Test/non-code files | Within 3+3 cap |
|---|---|---|---|
| P0 | 0 | 0 (evidence only) | Yes |
| P1 | 1 (`src/gui/app.py`) | 1 (`tests/gui/test_app_wiring.py`) | Yes |
| P2 | 1 (`src/gui/presenters/pipeline_presenter.py`) | 2 (`tests/gui/integration/test_behavioral_pipeline_run.py`, `tests/gui/integration/test_behavioral_dialogs.py`) | Yes |
| P3 | 0 | 1 (`tests/gui/integration/test_behavioral_dialogs.py`) | Yes |
| P4 | 0 | 0 (evidence only) | Yes |

The two near-cap production files at HEAD are `src/gui/app.py` (492/500) and
`src/gui/presenters/pipeline_presenter.py` (496/500). Per-task acceptance
criteria require a line-count check (`<= 500 lines`) after each modification.
P1-T1's addition to `build_application` is small (one parameter, one
expression, and docstring updates) and is expected to net at or under 500
lines. P2-T1 removes a method and is expected to reduce
`pipeline_presenter.py` below its current 496 lines. If either modification
would push a file over the cap, the implementing worker stops and reports the
condition for re-planning rather than proceeding.

## Test Plan

- **Unit/widget (no behavioral disk side effect):** `tests/gui/test_app_wiring.py` extended in P1-T2 with the registry-injection positive test.
- **Behavioral integration (Qt; `QT_QPA_PLATFORM=offscreen`; NO `qtbot.waitUntil`, NO `QTest.qWait`, NO `time.sleep`):** the three `tests/gui/integration/` files modified in P2-T2, P2-T3, P3-T1 to bootstrap state via the standard service path and to capture CSV writes in-memory.
- **Coverage evidence:** cycle-1 baseline `v2/evidence/baseline/baseline.2026-05-28T23-20.md`; post-remediation `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md`; comparison `v2/evidence/qa-gates/coverage-delta.2026-05-28T23-20.md` referencing the v2 execution baseline at `v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md`.
- **Disk-cleanliness check:** P3-T2 and P4-T4 both record the `git status` excerpt in their `Output Summary:` to confirm the post-remediation pytest run leaves no `results_*.csv` artifacts.

## Out of Scope (deferred to a future cycle)

- Non-blocking #2 (logger warning in `default_export_runner` for unknown filter): deferred to a future v2.1 ticket. The current default-to-Excel is silent but not incorrect.
- Non-blocking #3 (proactive split of `src/gui/app.py` and `pipeline_presenter.py` ahead of cap pressure): deferred. The cycle-1 changes must not push either file over 500 lines (enforced by per-task acceptance checks). A speculative refactor without a behavior change is outside this cycle.
- Any change to `v1/` artifacts (the v1 audit and evidence set must not be modified).
- Any change to `.github/workflows/_python-quality.yml`.
- Any change to pure-transform modules (`src/mix_pipeline.py`, `src/mix_pipeline_run.py`, `src/mix_lookups.py`, `src/mix_transforms.py`).

Non-blocking #4 (rewording the docstring on `test_export_csv_routes_destination_to_csv_exporter`) is bundled into P3-T1 as part of the rewrite (no separate task required).

## Open Questions / Notes

None — remediation-inputs is fully resolved by Suggested Remediation Path #1
and the bundled non-blocking #1 (test-seam removal). No user input is required
before atomic-executor preflight.
