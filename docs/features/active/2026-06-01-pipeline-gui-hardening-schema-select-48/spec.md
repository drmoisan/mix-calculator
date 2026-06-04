# Pipeline GUI Hardening and Schema Selection — Spec (Issue #48)

- Issue: #48
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/48
- Owner: drmoisan
- Work Mode: full-feature
- Last Updated: 2026-06-01
- Status: Draft
- Research basis: `artifacts/research/pipeline-gui-robustness-diagnosis.md`

## Overview

A `poetry run mix-pipeline-gui` session against a real partial-year ("8+4")
workbook exposed five defects and one missing capability in the GUI pipeline
path. The defects share a single theme: failure handling and user interaction
were routed through paths designed for a console (stdin prompts, status-bar-only
errors, an unguarded Run action) rather than through Qt dialogs, and a latent
validation defect rejected valid partial-year data. This feature delivers six
workstreams (WS1a, WS1b, WS2, WS3, WS4, WS5) together so the GUI handles the
partial-year workbook end to end without console interaction or false validation
failures.

## Goals

- Eliminate every stdin interaction from a GUI session; route the KEY-mismatch
  decision through a Qt modal that defaults to "Keep existing" (trust).
- Launch packaged builds with no console window; allow a developer console for
  logs only, never for interaction.
- Gate the Run action on the presence of all three required import keys so a
  partial import cannot cause a cascading `KeyError`.
- Surface every import and run error through a modal dialog and a status-bar
  summary.
- Correct the `validate_aop` YTD identity so partial-year ("8+4") sheets validate
  correctly while genuine identity violations and full-year sheets are unaffected.
- Add a per-source-tab import-schema dropdown with auto-select, a
  `<Choose Schema>` placeholder, and a "Build new schema" button, reusing the
  existing matching, discovery, and builder machinery.

## Non-Goals

- Do NOT relax or remove AOP validation. WS5 corrects the identity that is
  checked; genuine identity violations must still fail validation.
- Do NOT change the known-file loader defaults. Schema selection (WS2) is
  additive; `import_le`, `import_aop`, and `import_skulu` remain the default
  import path.
- Do NOT alter the financial transform math (`mix_transforms.py` and the AOP/LE
  derivation logic). Only the validation identity in `validate_aop` changes.
- Do NOT change required-check configuration, branch protection, or the
  benchmark baseline provenance rules.
- No new third-party dependencies. Qt (PySide/Qt) and the existing schema
  subsystem are already present.
- Confidential workbook figures must never appear in any committed artifact
  (spec, tests, fixtures, evidence).

## Functional Requirements by Workstream

### WS1a — Route KEY-mismatch resolution through a Qt dialog

The KEY-mismatch decision must never reach the stdin `input()` path in a GUI
session.

- The `etl_key.resolve_key` seam (`src/etl_key.py:193`) already exposes
  injectable `is_tty: Callable[[], bool]` and `prompt: Callable[[str], str]`
  collaborators. The loaders `load_aop.load_aop` (`src/load_aop.py:122`) and
  `normalize_le.load_source` forward these with defaults that bind the built-in
  `input` and `sys.stdin.isatty`.
- The GUI's `PipelineService` (`src/gui/pipeline_service.py`) currently calls the
  loaders without supplying these seams (for example `import_aop` at
  `pipeline_service.py:276`), so a diverging KEY under the default `prompt`
  policy reaches stdin.
- `PipelineService` must be wired so a GUI session never reaches the stdin
  `input()` path. When a KEY mismatch is detected, resolution is presented as a
  Qt modal with two options: "Keep existing" (trust — keep the source KEY) and
  "Rebuild" (overwrite — rebuild the KEY from components). The default selection
  is "Keep existing".
- The dialog decision maps to the loader policy: "Keep existing" -> trust;
  "Rebuild" -> overwrite. The dialog is injected through the existing
  `prompt`/`is_tty` seam (or an equivalent service-layer parameter) so the
  service does not depend on a live terminal and remains unit-testable without
  real stdin.
- `normalize_le.load_source` shares the same exposure as the AOP loader and must
  receive the same treatment so the LE import path also never reaches stdin.

### WS1b — Console-less packaged launch

- Packaged builds must open no console window. The Nuitka build invocation
  (`src/build_exe.py`) must pass `--windows-console-mode=disable`, and/or the
  entry point must be a `gui`-style (non-console) launch. The current entry point
  `mix-pipeline-gui = "src.gui.app:main"` (`pyproject.toml:39`) generates a
  `console_scripts` entry that allocates a console on Windows.
- Developer `poetry run` launches MAY retain a console, but it is for logs only.
  No user interaction may use stdin in any launch mode; all interaction goes
  through Qt dialogs (see WS1a).
- The Velopack `NotInstalled` message (`src/gui/_velopack_bootstrap.py`) is
  benign when run unmanaged and is out of scope; no change is required there.

### WS2 — Per-source-tab import-schema dropdown

Each source tab gains an import-schema selector. This wires previously-unused
machinery and is additive to the known-file loaders.

- Add a schema dropdown (`QComboBox`) and a "Build new schema" button to
  `SourceInputWidget` (`src/gui/widgets/source_input_widget.py`, 355/500 lines).
  Add a `schema_selected` signal and view methods to populate and set the combo
  (for example `set_schema_list`, `set_selected_schema`). The `<Choose Schema>`
  placeholder is the combo's first item.
- On tab activation, auto-select a matching schema. The
  `SourceSelectionPresenter`
  (`src/gui/presenters/source_selection_presenter.py`, 198/500 lines) gains a
  schema-discovery handler that reads a header preview and calls the existing
  `schema_matching.find_best_match` via
  `SchemaServiceProtocol.find_best_match` (`src/gui/services/schema_service.py`)
  and the decision logic in `_schema_wiring.discover_schema`
  (`src/gui/_schema_wiring.py:63`).
- When `discover_schema` returns `action="proceed"`, set the matching schema name
  as the combo's current selection. When it returns `action="resolve"` (no
  suitable match), leave the combo at the `<Choose Schema>` placeholder.
- The "Build new schema" button opens the existing schema builder dialog
  (`src/gui/widgets/schema_builder_dialog.py`), reusing the `_open_schema_builder`
  closure already wired for the `Tools > Schema Builder...` menu action
  (`_schema_wiring.py:97`), passing the current source headers as context where
  available.
- `PipelineViewProtocol`/`SourceSelectionViewProtocol` (`src/gui/protocols.py`,
  298/500 lines) are extended with the schema-selection view methods as needed.
- Known-file loaders remain the default import path. Schema selection is additive
  and does not change `import_le`/`import_aop`/`import_skulu` default behavior.

### WS3 — Gate the Run action on all three import keys

- `pipeline_presenter.can_run()` (`src/gui/presenters/pipeline_presenter.py:298`)
  currently returns `bool(self.working_tables) and not self._is_running`. Because
  `working_tables` is non-empty when any single table imported, a partial import
  (for example LE succeeded, AOP failed) satisfies the guard.
- `make_run_task()` (`pipeline_presenter.py:310`) captures
  `dict(self._imported_tables)`, which lacks `"aop"` after a failed AOP import;
  `run_pipeline` then reads `tables[_AOP_KEY]` (`pipeline_service.py:373`) and
  raises `KeyError: 'aop'`.
- Strengthen `can_run()` so Run is permitted only when all three required import
  keys (`LE`, `aop`, `sku_lu`) are present in `_imported_tables` (or a non-empty
  `_derived_tables` set exists from a prior successful run, preserving re-run
  behavior) and no job is running. A partial import must leave Run disabled, so
  no cascading `KeyError` can occur.
- This is a guard-only change. No change to the worker, service, or error
  callback is required for the cascade fix.

### WS4 — Modal plus status-bar error surfacing

- The single bridge from the presenter error contract to the Qt surface is
  `MainWindowPipelineView.show_error` (`src/gui/_main_window_view.py:67`), which
  currently only writes to the status bar via `MainWindow.set_status`.
- All import and run errors must be surfaced via a `QMessageBox.critical` modal
  AND a status-bar summary. The modal carries the full diagnostic message; the
  status bar carries a concise summary.
- Add a view method to `PipelineViewProtocol` (`src/gui/protocols.py`) if a
  separate dialog-error contract is needed (for example
  `show_dialog_error(title, message)`), and implement it on
  `MainWindowPipelineView`. The presenter error callbacks (`on_import_one_error`,
  `on_import_all_error`, `on_run_error`) route through this surface.

### WS5 — Correct the `validate_aop` YTD identity

- `validate_aop` (`src/_load_aop_helpers.py:181`) builds `per_row_checks` with
  `"YTD": MONTHS` (full Jan..Dec) unconditionally (line 220), then adds
  `"YTG": YTG_MONTHS` only when a `YTG` column is present (line 224). The module
  defines `YTG_MONTHS = MONTHS[4:]` (May..Dec) at line 40, so YTD logically
  covers the complementary months Jan..Apr when YTG is present.
- This is a confirmed logic defect. Verified with openpyxl against the real
  workbook (AOP1 sheet, header at Excel row 3, 1522 data rows):
  `YTD == sum(Jan..Apr)` holds for 1522/1522 rows; `YTG == sum(May..Dec)` holds
  for 1522/1522; `YTD + YTG == sum(Jan..Dec)` holds for 1522/1522. The current
  check `YTD == sum(Jan..Dec)` passes only 648/1522 rows (those where YTG == 0).
- Correct the identity:
  - When a `YTG` column is present: assert `YTD == sum(months not in YTG_MONTHS)`
    (the complementary set, Jan..Apr) AND `YTG == sum(YTG_MONTHS)` (May..Dec).
  - When `YTG` is absent: assert `YTD == sum(MONTHS)` (full-year sheet,
    unchanged behavior).
- The quarter identity checks (`Q1..Q4 == sum(its 3 months)`) and the
  duplicate-KEY warning are unchanged.
- Validation is CORRECTED, not relaxed or removed: a genuine identity violation
  (a row where the corrected identity does not hold within `TIEOUT_TOL`) must
  still raise `ValueError`. Confidential workbook figures must not appear in any
  committed artifact; tests use synthetic values that exercise the identity.

## Design and Constraints

### Hard 500-line file cap

The 500-line file cap (`.claude/rules/general-code-change.md`) is enforced hard.
Two files near the cap require extraction BEFORE any additions:

- `src/gui/app.py` — 499/500 lines. No code may be added directly. Any change
  (notably the WS2 build-new-schema wiring) requires extracting existing logic
  into a sibling module first, following the established `_wiring.py` /
  `_import_dispatch_wiring.py` / `_schema_wiring.py` pattern.
- `src/gui/presenters/pipeline_presenter.py` — 490/500 lines. The WS3
  `can_run()` change is small (3–5 lines) but lands near the cap; extract first
  if WS2-related presenter changes are co-located, or relocate the gate logic to
  `import_dispatch.py` (386/500 lines).

Files with sufficient headroom for their planned changes:
`pipeline_service.py` (437/500), `import_dispatch.py` (386/500),
`source_input_widget.py` (355/500), `source_selection_presenter.py` (198/500),
`schema_service.py` (245/500), `_main_window_view.py` (108/500),
`main_window.py` (200/500), `protocols.py` (298/500). The full size-headroom
table is in the research doc.

### Module quality tiers

Per `quality-tiers.yml` and the research doc:

- T2 (Core): `pipeline_service.py`, `pipeline_presenter.py`,
  `source_selection_presenter.py`, `schema_service.py`, `protocols.py`
  (and `import_dispatch.py` by sibling classification).
- T3 (Adapters & UI): `source_input_widget.py`, `main_window.py`,
  `workers/pipeline_worker.py`.
- T4 (Scaffolding): `app.py`, `_schema_wiring.py`, `_main_window_view.py`, and
  the other wiring modules.

T2 modules require line coverage >= 85%, branch coverage >= 75%, no untyped
escape hatches, and at least one property test per pure function. Coverage and
branch thresholds are uniform across all tiers (`.claude/rules/quality-tiers.md`).

### Other constraints

- All Python changes pass the four-stage toolchain (Black, Ruff, Pyright,
  Pytest) per `.claude/rules/python.md`.
- Error handling fails fast and explicitly; no broad catch-all that swallows
  errors. The WS4 surface is the GUI boundary that displays the failure.
- Evidence artifacts (baselines, QA gates, coverage) are written only to
  `<FEATURE>/evidence/<kind>/` per the evidence-location invariant.

## Testing Strategy

All GUI tests run under `QT_QPA_PLATFORM=offscreen` (set in
`tests/gui/conftest.py`); `pytest-qt` (`qtbot`) is available for signal-wait
tests. Tests must be deterministic, isolated, and must not use real stdin,
temporary files, or external services.

- WS1a: Unit-test the `PipelineService` KEY-mismatch path with the dialog
  injected as a fake callable; assert the stdin `input()` path is never reached
  and that "Keep existing" maps to trust and "Rebuild" maps to overwrite. The
  default selection is "Keep existing". Cover both AOP and LE loader paths.
- WS1b: Verify the build invocation includes the console-disable flag and/or the
  non-console entry point. Packaging is verified by inspecting the build
  configuration; no runtime console-window assertion is required in unit tests.
- WS2: Offscreen widget tests for the schema combo (placeholder present, list
  population, `schema_selected` signal). Presenter tests for the discovery
  handler: `action="proceed"` selects the matched schema; `action="resolve"`
  leaves the `<Choose Schema>` placeholder. Integration test for the
  build-new-schema button opening the builder dialog.
- WS3: `can_run()` returns `False` when any required key is missing and `True`
  only when all three keys are present and not running; a partial import leaves
  Run disabled and produces no `KeyError`.
- WS4: `show_error` (and any new dialog-error method) drives both a modal and a
  status-bar summary; the existing `FakePipelineView` records the calls.
  Integration test: an import-failure path shows the modal and disables Run.
- WS5: Unit tests for the corrected identity — a YTG-present sheet
  (YTD = Jan..Apr, YTG = May..Dec) passes; a full-year sheet (no YTG,
  YTD = Jan..Dec) passes; a row with a genuine identity violation still raises
  `ValueError`. At least one property test for the pure identity helper (T2). All
  test values are synthetic.

## Acceptance Criteria

- [x] AC-1: In any GUI session, no stdin prompt occurs. The KEY-mismatch
      decision is resolved through a Qt modal; the `PipelineService` import path
      never reaches the `etl_key`/loader stdin `input()` path. (WS1a)
- [x] AC-2: The KEY-mismatch Qt modal presents "Keep existing" (trust) and
      "Rebuild" (overwrite) options and defaults to "Keep existing"; the selected
      option maps to the corresponding loader policy. (WS1a)
- [x] AC-3: The LE import path receives the same dialog-based KEY-mismatch
      handling as the AOP path and never reaches stdin. (WS1a)
- [x] AC-4: Packaged builds open no console window (Nuitka
      `--windows-console-mode=disable` and/or a `gui`-style entry point);
      developer `poetry run` launches may retain a console for logs only, with no
      stdin interaction in any launch mode. (WS1b)
- [x] AC-5: `pipeline_presenter.can_run()` returns `True` only when all three
      required import keys (`LE`, `aop`, `sku_lu`) are present (or a derived-table
      set from a prior successful run exists) and no job is running. (WS3)
- [x] AC-6: After a partial import failure (one or two of the three sources
      failed), Run is disabled and no cascading `KeyError` (for example
      `KeyError: 'aop'`) can be produced by `run_pipeline`. (WS3)
- [x] AC-7: Every import and run error is surfaced through a
      `QMessageBox.critical` modal AND a status-bar summary, routed through the
      `MainWindowPipelineView` error surface. (WS4)
- [x] AC-8: `validate_aop` accepts the partial-year ("8+4") sheet: when a `YTG`
      column is present, it asserts `YTD == sum(months not in YTG_MONTHS)`
      (Jan..Apr) AND `YTG == sum(YTG_MONTHS)` (May..Dec). (WS5)
- [x] AC-9: `validate_aop` leaves full-year sheets unaffected: when no `YTG`
      column is present, it asserts `YTD == sum(MONTHS)` (Jan..Dec). (WS5)
- [x] AC-10: `validate_aop` still rejects genuine identity violations: a row
      where the corrected identity does not hold within `TIEOUT_TOL` raises
      `ValueError`. Validation is corrected, not relaxed. (WS5)
- [x] AC-11: Each source tab shows an import-schema dropdown that auto-selects a
      matching schema on tab activation when `discover_schema` returns
      `action="proceed"`. (WS2)
- [x] AC-12: When no schema matches (`discover_schema` returns
      `action="resolve"`), the dropdown shows the `<Choose Schema>` placeholder
      and does not auto-select a schema. (WS2)
- [x] AC-13: Each source tab has a working "Build new schema" button that opens
      the existing schema builder dialog. (WS2)
- [x] AC-14: Schema selection is additive: the known-file loaders
      (`import_le`/`import_aop`/`import_skulu`) remain the default import path and
      their default behavior is unchanged. (WS2)
- [x] AC-15: No confidential workbook figures appear in any committed artifact
      (spec, tests, fixtures, or evidence); WS5 tests use synthetic values. (WS5)

### Remediation Acceptance Criteria (cycle 2026-06-01T23-31, Issue #48 / PR #49)

- [x] R-AC-1: On a profile with an empty user registry directory and no
      `MIX_CALCULATOR_SCHEMA_DIR` override, the set of selectable schema names
      exposed to the GUI includes both `default_aop` and `default_le`.
      (Evidence: P4-T1 `tests/gui/test_schema_service.py::test_service_lists_and_loads_bundled_defaults_when_user_dir_empty`.)
- [x] R-AC-2: A user-saved schema whose name collides with a bundled default name
      takes precedence over the bundled default of the same name (user override
      wins; no duplicate name appears in the list). (Evidence: P1-T4
      `tests/test_schema_registry.py::test_list_schemas_user_override_appears_once_and_resolves_to_user`.)
- [x] R-AC-3: Each source tab's schema dropdown is populated at application startup
      (and/or on tab activation) with the available schema names from the schema
      service; `set_schema_list` has at least one production caller and the
      populated names include the bundled defaults per R-AC-1. (Evidence: P3-T4/P3-T5
      `tests/gui/test_app_wiring_schema_list.py`.)
- [x] R-AC-4: `discover_schema` / `find_best_match` consider the bundled defaults as
      candidates, so a source whose headers match a bundled default yields
      `action="proceed"` and auto-selects that schema (restores AC-11 for the
      shipped defaults). (Evidence: P2-T1
      `tests/test_schema_matching_registry.py::test_find_best_match_and_discover_see_bundled_defaults`.)
- [x] R-AC-5: Loading a selected schema by name (`SchemaService.load_schema` / the
      import-with-schema path) succeeds for a bundled-default name even when no
      user-saved file of that name exists. (Evidence: P4-T1
      `tests/gui/test_schema_service.py::test_service_lists_and_loads_bundled_defaults_when_user_dir_empty`.)
- [x] R-AC-6: The change is additive: the existing known-file loaders
      (`import_le`/`import_aop`/`import_skulu`) and the existing user-registry
      persistence behavior are unchanged. Existing AC-1..AC-15 remain PASS.
      (Evidence: P4-T2
      `tests/test_schema_registry.py::test_additivity_bundled_default_and_user_round_trip_unchanged`
      and the full suite at P5-T4: 811 passed, 0 failed.)
- [x] R-AC-7 — `ThreadedRunner` performs no cross-thread `QObject` destruction:
      the worker is wired to `deleteLater` on `thread.finished`; a second dispatch
      does not drop a still-running prior thread; application-shutdown teardown
      quits and waits all active worker threads; and the existing queued-connection
      success/error delivery on the GUI thread is preserved. (Cycle 2 / issue #48
      Finding F1. Evidence:
      `tests/gui/test_runners_threaded_lifecycle.py::test_worker_deletelater_wired_to_thread_finished` (a),
      `::test_second_dispatch_does_not_drop_running_prior_thread` (b),
      `::test_await_active_quits_and_waits_then_no_running_thread` and
      `tests/gui/test_shutdown_wiring.py::test_about_to_quit_calls_await_active` /
      `::test_wire_shutdown_cleanup_noop_for_runner_without_await_active` (c),
      `::test_queued_outcome_still_delivers_on_gui_thread` (d); full suite at P4-T4:
      818 passed, 0 failed; runners.py 100% line/branch.)
