# Code Review — mix-pipeline-gui v2 (Issue #19)

- **Timestamp:** 2026-05-28T23-20
- **Branch:** feature/mix-pipeline-gui-19
- **Base:** main (working-tree comparison includes uncommitted v2 changes)
- **Reviewer scope:** Modified and new production/test code under `src/gui/` and `tests/gui/` for the v2 execution.

## Executive Summary

The v2 implementation delivers the runner abstraction, view-protocol
extensions, preview-sink wiring, and Export-defect fixes specified in
`v2/spec.md`. Code is type-annotated under Pyright strict, Black/Ruff
clean, and verified by 416 passing tests at 99% line / 99% branch
coverage. One Blocking issue: a behavioral export test wires the real
`CsvExporter` and writes files to the repository working directory. Several
non-blocking findings address file-size headroom, a production-source test
seam, a silent fall-through in `default_export_runner`, and minor
documentation accuracy. Recommendation: address the Blocking finding and
proceed.

## Summary

The v2 execution delivers the runner abstraction, view-protocol extensions,
preview-sink wiring, and Export-defect fixes specified in `v2/spec.md`. The
code is type-annotated under Pyright strict, formatted by Black, lint-clean
under Ruff, and verified by 416 passing tests at 99% line and 99% branch
coverage. The architecture remains MVP with pure-Python presenters and a thin
Qt widget layer. The composition root in `src/gui/app.py` is dense; a
helper split into `src/gui/_wiring.py` keeps both files under the 500-line
cap.

One Blocking issue: a behavioral export test bypasses the in-memory CSV writer
seam and writes real files into the repository working directory. Several
non-blocking observations relate to file-size headroom, a production-source
test seam, and documentation accuracy.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocking | tests/gui/integration/test_behavioral_dialogs.py | test_export_csv_routes_destination_to_csv_exporter, lines 150-181 | The wired CSV-export click path uses the real `CsvExporter` with the default `_default_open_writer`, which calls `open(path, "w", ...)`. With `export_dialog_runner` returning `("CSV", "results.csv")`, the test writes `results_LE.csv`, `results_aop.csv`, and `results_sku_lu.csv` to the working directory. | Inject a fake exporter (or fake `open_writer`) via a new `csv_exporter` / `exporter_registry` keyword on `build_application`; OR drop the click-through and keep only the existing registry-resolution assertion (line 181); OR pass `destination_path` to a `tmp_path` fixture and capture the write under a pytest temp dir (note: spec forbids temp files in unit tests, so the in-memory seam is preferred). | `.claude/rules/general-unit-test.md` "Creation and use of temporary files in tests is strictly prohibited"; `.claude/rules/python.md` "no runtime filesystem temp files in unit tests"; spec v2 Constraints reiterates the same. | `git status` shows the three CSV files as untracked working-tree artifacts; their contents (`KEY`/`k1`/`SKU`/`SKU-001`) match `_fake_imports()` at line 30-37. |
| Major | src/gui/presenters/pipeline_presenter.py | `set_imported_tables_for_test`, line 124 | A test-only mutator (`set_imported_tables_for_test(self, tables)`) lives on the production presenter and is called by behavioral tests to bootstrap state. The name advertises its intent, but `general-code-change.md` favors test-driven seams that do not bleed test concerns into production. | Replace with constructor injection of initial state OR with an `apply_open_result(...)` style method that production code also uses (Open already populates `_imported_tables` through `on_open_db`; tests could use that path). | Production code carries a method whose only purpose is to support tests; this is a smell against "Isolate I/O / test concerns" and increases the public surface unnecessarily. | grep `set_imported_tables_for_test` finds one definition in production and four call sites in `tests/gui/integration/test_behavioral_dialogs.py` and `test_behavioral_pipeline_run.py`. |
| Minor | src/gui/app.py | whole file, 492 lines | The composition-root file is 8 lines below the 500-line cap. Phase 7 already split the dialog defaults into `src/gui/_wiring.py`. Any future addition will require another split. | Plan a second split (e.g., move `MainWindowPipelineView` into `src/gui/_main_window_view.py`) before the next composition change. | `.claude/rules/general-code-change.md` 500-line cap; safety margin is small. | `wc -l src/gui/app.py` = 492. |
| Minor | src/gui/presenters/pipeline_presenter.py | whole file, 496 lines | The presenter is 4 lines below the cap. Any new state field or button-state push will exceed it. | Plan a split (e.g., factor `_last_imported_path` and `on_file_path_changed` / `working_tables` into `_pipeline_state.py`) before the next addition. | Same cap; even smaller margin. | `wc -l` = 496. |
| Minor | tests/gui/integration/test_behavioral_dialogs.py | imports and docstring | The behavioral docstring claims to assert AC-9 CSV name-mangling end-to-end but the actual assertion (line 181) is `wired.registry.get("CSV").format_name == "CSV"`, which is a registry-resolution check, not a name-mangling check. The name-mangling rule is correctly unit-tested in `test_csv_exporter.py`. | Reword the docstring to "asserts the registry resolves CSV"; remove the misleading "CSV name-mangling end-to-end" framing. | Avoid claims about coverage the test does not actually provide; matches `tonality.md` evidence-first wording. | Read `test_behavioral_dialogs.py:150-181`. |
| Minor | src/gui/runners.py | `SynchronousRunner.run`, broad `except Exception` | The broad catch is documented as a deliberate boundary at module level, but the `try`/`except` itself lacks a docstring or inline note pointing back to the boundary contract. | Add a one-line inline comment in the body: "Broad catch: protocol contract requires re-routing any task exception to on_error." | `.claude/rules/general-code-change.md` and `python.md` permit broad handlers at well-defined boundaries but require the rationale at the site. | Read `src/gui/runners.py` around the catch. |
| Minor | src/gui/_wiring.py | `default_export_runner`, line 79-95 | The fall-through on an unrecognized filter defaults silently to `"Excel"`. The docstring describes this; the body does not log or warn. | Add a logger.warning when the filter string is neither `*.xlsx` nor `*.csv`; the silent default is a future debugging blind spot. | `.claude/rules/general-code-change.md` "Fail fast and explicitly". | Read `src/gui/_wiring.py:78-96`. |
| Minor | docs/features/.../v2/evidence/qa-gates/ | phase10-qa, phase11-qa absent | The plan's Phase 10 and Phase 11 acceptance artifacts are split across `tier-classification.2026-05-28T22-10.md`, `dod-traceability.2026-05-28T22-10.md`, `coverage-delta.2026-05-28T22-10.md`, and the four `final-*` files instead of single `phase10-qa.md` / `phase11-qa.md` files. The required schema fields are present in each individual artifact, but the per-phase aggregation expected by the plan is absent. | Document this re-grouping explicitly in the dod-traceability artifact OR add stub phase10/phase11 artifacts that point at the split files. | The plan's structure assumes a per-phase QA artifact; verifiers may search for it and find nothing. | `ls v2/evidence/qa-gates/` contains phase1-qa through phase9-qa but no phase10/11 entries; tier and coverage-delta artifacts cover the same scope. |
| Informational | quality-tiers.yml | added entries | `src/gui/runners.py: T2` (matches a presenter-protocol seam) and `src/gui/_wiring.py: T4` (composition-root chooser helpers). | None — accepted classifications. | Tier choices are appropriate per `.claude/rules/quality-tiers.md`. | `grep runners quality-tiers.yml`. |
| Informational | tests/gui/test_pipeline_presenter_v2.py | new test file (244 lines) | The split from `test_pipeline_presenter.py` keeps both files under the cap per plan P4-T2; the boundary between the v1 and v2 test files is by phase/feature, not by behavior. | None — accepted; document the split rationale in the file's module docstring if not already present. | Test organization invariant; no policy violation. | `wc -l` = 244. |

## Design Principles Review

- **Simplicity first:** The runner abstraction is minimal (one method, two
  implementations); button-state semantics live entirely in the presenter
  through the new view-protocol methods. The `default_export_runner`
  filter-string parse is straightforward.
- **Reusability:** `SynchronousRunner` is reused across five behavioral test
  files. The `working_tables` property unifies the three call sites that
  previously inlined the same selection expression in v1.
- **Extensibility:** New exporter format names continue to flow through
  `ExporterRegistry`; the `RunnerProtocol` is `runtime_checkable` so
  alternative runners (e.g., asyncio-backed) could be added without changing
  `build_application`.
- **Separation of concerns:** Presenters carry no Qt imports;
  `PipelinePresenter.set_imported_tables_for_test` is the one test-only seam
  in production code (flagged Major).

## API and Compatibility

- `PipelineViewProtocol` gained four `set_*_button_enabled` methods
  (additive). All implementations (`MainWindowPipelineView`, `FakePipelineView`)
  were updated.
- `build_application` gained six keyword-only parameters (`runner`,
  `save_path_chooser`, `open_path_chooser`, `export_dialog_runner`,
  `pipeline_service`, `workbook_reader`), all defaulting to `None`. No
  existing caller breaks.
- `SourceSelectionPresenter` gained an optional keyword-only `preview_sink`
  parameter defaulting to `None`. v1 callers are unaffected.
- `MainWindow` promoted four button attributes from private (`_import_*_btn`)
  to public (`import_*_btn`). External callers (none in v1 outside the
  composition root and behavioral tests) gain access; no caller is broken.

## Dependencies

No new dependency added. `pytest-qt` and PySide6 already declared in v1.

## Determinism

Behavioral tests use `SynchronousRunner` injection and `button.click()` (a
typed call) plus direct attribute/state assertions. Zero polling primitives
in `tests/gui/integration/`. `qtbot.waitSignal` is confined to the
worker-isolation test and three widget tests outside `integration/` per
explicit spec and plan permissions.

## Testing Quality

- Arrange-Act-Assert structure visible in every reviewed test file.
- Fakes (`FakePipelineService`, `FakeWorkbookReader`, `FakeExporter`, et al.)
  provide controlled inputs and recording surfaces; `# noqa: ARG002` usage is
  authorized.
- Property test for `on_file_path_changed` (Hypothesis) satisfies the T2
  density requirement.
- Coverage 99/99 with 416 tests confirms the surface is exercised.

## Documentation

Docstrings present on all classes, functions, and methods in new and modified
v2 modules. Google-style with `Args:`, `Returns:`, `Side effects:`, and
`Raises:` sections per `self-explanatory-code-commenting.md`. Loops carry
intent comments. Branches in `default_export_runner`,
`on_file_path_changed`, and `working_tables` carry decision comments.

## Overall Assessment

The v2 code change is architecturally sound and meets the specified contract.
It must not merge until the blocking behavioral-test temp-file leak is
addressed. The non-blocking findings should be acted on but do not by
themselves require remediation.
