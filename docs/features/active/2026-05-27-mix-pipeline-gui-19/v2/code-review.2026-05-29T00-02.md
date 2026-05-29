# Code Review — mix-pipeline-gui v2 EXIT (Issue #19)

- **Timestamp:** 2026-05-29T00-02
- **Cycle:** 1 EXIT audit (post-remediation)
- **Branch:** feature/mix-pipeline-gui-19
- **Base:** main (working-tree comparison includes uncommitted v2 + cycle-1 changes)
- **Reviewer scope:** Cycle-1 production and test diffs over the v2 head, in the context of the v2 surface as a whole.

## Executive Summary

Cycle 1 closes the single Blocking finding from the cycle-0 entry audit (R-1: CSV behavioral test wrote real files) and the bundled non-blocking #1 (production-source test seam). The remediation adds a minimal `exporter_registry` keyword to `build_application` and uses it from a rewritten behavioral test that captures CSV writes through an in-memory `_CapturingStringIO` subclass. The production-source `set_imported_tables_for_test` mutator has been removed; all four call sites migrated to standard `on_import_all` / `on_import_one` paths against `FakePipelineService`. Black/Ruff/Pyright strict remain 0/0/0; Pytest 417 passed; coverage 99/99. One non-blocking observation: `src/gui/app.py` is now exactly at the 500-line cap (zero headroom) and a future change will require a helper split. Recommendation: MERGE.

## Summary

The cycle-1 diff is narrow and surgical. The composition root in `src/gui/app.py` gains a single keyword-only `exporter_registry` parameter and a one-line conditional resolution. The presenter in `src/gui/presenters/pipeline_presenter.py` loses a single test-only mutator method, with no other production-code impact. Tests are migrated to standard paths; one new positive test asserts the injection seam works without affecting the default path. The architecture remains MVP with pure-Python presenters and a thin Qt widget layer. Type annotations are full under Pyright strict; docstrings are Google-style with `Args:`, `Returns:`, and `Side effects:` sections.

The single cycle-0 Blocking item (R-1) is closed via a clear, well-typed in-memory capture seam. The cycle-0 non-blocking #1 (production-source test seam) is closed by deletion. The remaining non-blocking observations from cycle 0 (silent default in `default_export_runner`, docstring accuracy on the CSV behavioral test, file-size headroom on `app.py` and `pipeline_presenter.py`) are partially or fully addressed by cycle 1: the docstring is rewritten; the presenter dropped to 486 lines; the silent default deferral is documented in the plan; and `app.py` is now exactly at the cap (no headroom but no overage).

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | src/gui/app.py | whole file, 500 lines (exactly at cap) | The composition-root file is at the 500-line ceiling after the `exporter_registry` parameter and docstring update. Zero headroom for the next addition. | Plan a second split (e.g., move `MainWindowPipelineView` into `src/gui/_main_window_view.py`) before the next composition change. The cycle-0 code review already flagged this; the cycle-1 change pushed it from 492 to 500. | `.claude/rules/general-code-change.md` 500-line cap; safety margin is now zero. | `wc -l src/gui/app.py` = 500. |
| Minor | src/gui/_wiring.py | `default_export_runner`, line 79-95 | Carried over from the cycle-0 entry review. The fall-through on an unrecognized filter defaults silently to `"Excel"`. The cycle-1 plan explicitly deferred this to a future v2.1 ticket (Phase 4 out-of-scope list). | Add a `logger.warning` when the filter string is neither `*.xlsx` nor `*.csv` in a follow-up ticket. | `.claude/rules/general-code-change.md` "Fail fast and explicitly". | Read `src/gui/_wiring.py:78-96`. |
| Minor | src/gui/runners.py | `SynchronousRunner.run`, broad `except Exception` | Carried over from the cycle-0 entry review. The broad catch is documented as a deliberate boundary at module level; the `try`/`except` body lacks an inline pointer to the boundary contract. | Add a one-line inline comment: "Broad catch: protocol contract requires re-routing any task exception to on_error." | `.claude/rules/general-code-change.md` and `python.md` permit broad handlers at well-defined boundaries but require the rationale at the site. | Read `src/gui/runners.py` around the catch. |
| Minor | docs/features/.../v2/evidence/qa-gates/ | phase10-qa, phase11-qa absent | Carried over from the cycle-0 entry review. The plan's Phase 10/11 acceptance is split across `tier-classification`, `dod-traceability`, `coverage-delta`, and the four `final-*` files. The required schema fields are present in each individual artifact; the per-phase aggregation expected by the plan is absent. Cycle 1 did not introduce or modify these artifacts. | Document this re-grouping in `dod-traceability` OR add stub phase10/11 artifacts that point at the split files. | The plan's structure assumes a per-phase QA artifact; verifiers may search for it and find nothing. | `ls v2/evidence/qa-gates/` contains phase1-qa through phase9-qa but no phase10/11 entries. |
| Informational | tests/gui/integration/test_behavioral_dialogs.py | new `_CapturingStringIO` class | The in-memory capture subclass overrides `close()` to snapshot the buffer into `captured_writes` before super-closing. The pattern is necessary because the production exporter consumes the sink inside a `with` block, which would otherwise close the buffer before the test can read its contents. The subclass is local to the test and well-typed. | None — accepted pattern. | Local in-memory capture seam; no policy violation. | Read `test_behavioral_dialogs.py:183-194`. |
| Informational | src/gui/app.py | new `exporter_registry` parameter | Keyword-only, optional, defaults to `None`. The body resolves to `_build_registry()` when `None`, preserving production wiring. No call site outside the new test passes the parameter. | None — accepted seam. | The minimal extension follows the established v2 injection pattern (runner, choosers, pipeline_service, workbook_reader). | Read `build_application` body. |
| Informational | tests/gui/test_app_wiring.py | new test (+1) | `test_build_application_uses_injected_exporter_registry` asserts the injected registry is used and that the default path still constructs the production registry with `["Excel", "CSV"]`. Brings the file to 492 lines (under cap). | None. | Coverage of the new branch; satisfies the cycle-1 plan's P1-T2 acceptance criteria. | Read the new test. |

## Resolved cycle-0 findings (re-verified)

| Cycle-0 Severity | Item | Status in cycle 1 | Evidence |
|---|---|---|---|
| Blocking | tests/gui/integration/test_behavioral_dialogs.py R-1 (CSV disk-leak) | RESOLVED | The test uses an in-memory `_CapturingStringIO` capture seam injected through `build_application(exporter_registry=...)`; `git status` after the post-remediation pytest run shows no untracked `results_*.csv` files. |
| Major (non-blocking #1) | src/gui/presenters/pipeline_presenter.py `set_imported_tables_for_test` | RESOLVED | Working-tree grep of `set_imported_tables_for_test` across `src/` and `tests/` returns zero matches. All callers migrated to `on_import_all(_import_spec())` against `FakePipelineService(import_result=_fake_imports())`. |
| Minor | docstring on `test_export_csv_routes_destination_to_csv_exporter` claimed "name-mangling end-to-end" | RESOLVED | Rewritten docstring describes the actual assertion: per-table key set via injected `open_writer`, with name-mangling unit contract covered by `tests/gui/test_csv_exporter.py`. |
| Minor | src/gui/presenters/pipeline_presenter.py at 496/500 | IMPROVED | Now at 486/500 after `set_imported_tables_for_test` removal. |

## Design Principles Review

- **Simplicity first:** The cycle-1 diff is the minimum change to close R-1. The `exporter_registry` parameter is additive and optional. The in-memory capture is a small, local subclass.
- **Reusability:** The injected registry seam mirrors the runner/choosers/service injection pattern already established in v2.
- **Extensibility:** The seam supports any future exporter test that needs to inject a recording fake without bleeding test concerns into production.
- **Separation of concerns:** Removal of `set_imported_tables_for_test` is a strict improvement; the production presenter no longer carries a test-only mutator.

## API and Compatibility

- `build_application` adds one keyword-only optional parameter (`exporter_registry`). All existing callers continue to work; the production `main()` path is unchanged.
- `PipelinePresenter.set_imported_tables_for_test` is removed. Working-tree grep confirms no production caller; only test code referenced it.
- `WiredApplication.registry`: the `Attributes:` docstring note can be updated to reference the injection seam; not a blocker.

## Dependencies

No new dependency added in cycle 1.

## Determinism

- Behavioral tests continue to use `SynchronousRunner` injection and `button.click()` plus direct attribute/state assertions.
- Zero polling primitives (`qtbot.waitUntil`, `QTest.qWait`, `time.sleep`, `QThread.sleep`) in `tests/gui/integration/`.
- `qtbot.waitSignal` remains confined to non-`integration/` files.

## Testing Quality

- Arrange-Act-Assert structure preserved across modified tests.
- Property test for `on_file_path_changed` (Hypothesis) preserved.
- Coverage 99/99 with 417 tests confirms the surface is exercised.
- New positive test for the registry-injection seam is well-named and AAA-structured.

## Documentation

- Docstrings on the cycle-1 modified classes/functions are Google-style with the required sections.
- The `build_application` docstring `Args:` block documents the new `exporter_registry` parameter, including the rationale (test seam for in-memory CSV capture; defaults to production registry).
- The CSV behavioral test docstring is rewritten to match the assertions.

## Overall Assessment

The cycle-1 code change is narrow, well-scoped, and resolves the cycle-0 Blocking finding without introducing new policy violations. The one non-blocking observation (`app.py` at exactly 500 lines) is a future-proofing concern, not a current violation. Recommendation: MERGE.
