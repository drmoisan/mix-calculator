# Pipeline GUI Hardening and Schema Selection — Plan (Issue #48)

- **Issue:** #48
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/48
- **Owner:** drmoisan
- **Work Mode:** full-feature
- **Last Updated:** 2026-06-01T11-54
- **Status:** Draft
- **Version:** 1.0
- **Spec (AC source, AC-1..AC-15):** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/spec.md`
- **Issue:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/issue.md`
- **Research:** `artifacts/research/pipeline-gui-robustness-diagnosis.md`

## Compliance References

All work complies with the repository policies (loaded automatically via `.claude/rules/`):
`CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`,
`.claude/rules/python.md`, `.claude/rules/python-suppressions.md`,
`.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`,
`.claude/rules/tonality.md`. Do not duplicate their content here.

## Evidence Location Invariant

All evidence artifacts MUST be written under the canonical scheme
`docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/<kind>/`
per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing evidence to
`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical
path is a policy violation. In this plan `<FEATURE>` abbreviates
`docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`.

## Per-Task Toolchain Contract

Unless a task states otherwise, each code/test task runs the full four-stage Python loop
in order, restarting from stage 1 on any failure or autofix (prefix Poetry with
`env -u VIRTUAL_ENV` per the known virtual-env quirk):

1. `env -u VIRTUAL_ENV poetry run black .`
2. `env -u VIRTUAL_ENV poetry run ruff check .`
3. `env -u VIRTUAL_ENV poetry run pyright`
4. `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`

Zero-regression gate: format clean, lint zero, type zero, line coverage >= 85%,
branch coverage >= 75%, no coverage regression on changed lines. T2 modules also require
>= 1 property test per pure function and no untyped (`Any`/`# type: ignore`) escape hatches.

---

### Phase 0 — Baseline Capture and Policy Reading

> Headroom note: Phase 0 is read-only and produces no source changes. It establishes the
> pre-change coverage headline used by the Phase 9 delta verification.

- [x] [P0-T1] Read the policy files in required order and record a Phase 0 read-evidence artifact.
  - Files to read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`.
  - Acceptance: `<FEATURE>/evidence/baseline/phase0-instructions-read.md` exists with `Timestamp:`, `Policy Order:`, and the explicit list of files read.

- [x] [P0-T2] Capture the baseline format/lint/type state.
  - Commands: `env -u VIRTUAL_ENV poetry run black --check .`; `env -u VIRTUAL_ENV poetry run ruff check .`; `env -u VIRTUAL_ENV poetry run pyright`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-static.md` exists with `Timestamp:`, `Command:` (each command), `EXIT_CODE:` (each), and an `Output Summary:` capturing pass/fail and error counts.

- [x] [P0-T3] Capture the baseline test + coverage state.
  - Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-tests.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` recording numeric baseline line-coverage % and branch-coverage % plus passed/failed counts.

- [x] [P0-T4] Record the current line counts of the near-cap and to-be-touched files as the headroom baseline.
  - Files to measure: `src/gui/app.py`, `src/gui/presenters/pipeline_presenter.py`, `src/gui/widgets/source_input_widget.py`, `src/gui/protocols.py`, `src/gui/pipeline_service.py`, `src/gui/_main_window_view.py`, `src/_load_aop_helpers.py`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-file-sizes.md` exists with `Timestamp:`, the per-file line counts, and an `Output Summary:` flagging `app.py` (499/500) and `pipeline_presenter.py` (490/500) as requiring extraction before additions.

---

### Phase 1 — Extraction for Cap Headroom

> Headroom note: `src/gui/app.py` is 499/500 and `src/gui/presenters/pipeline_presenter.py`
> is 490/500. No code may be added to either until logic is extracted into sibling `_*.py`
> wiring modules (the established `_wiring.py` / `_import_dispatch_wiring.py` / `_schema_wiring.py`
> pattern). This phase is behavior-preserving: no functional change, only relocation.

- [x] [P1-T1] Extract the `_handle_run` closure and its Run-signal wiring from `src/gui/app.py` (around line 182) into a new sibling module `src/gui/_run_wiring.py` exposing a `wire_run(...)` function, and call it from `app.py`.
  - Tests: extend `tests/gui/test_app_wiring_dispatch.py` (or add `tests/gui/test_run_wiring.py`) to assert `wire_run` connects `run_requested` to the run dispatch and that behavior is unchanged.
  - Toolchain: full four-stage loop.
  - Acceptance: `src/gui/_run_wiring.py` <= 500 lines; `src/gui/app.py` line count strictly decreases and stays <= 500; all existing GUI tests pass; behavior unchanged.

- [x] [P1-T2] Extract the `_open_schema_builder` / `schema_builder_requested` wiring referenced by `app.py` into `src/gui/_schema_wiring.py` (137/500, ample headroom) as a reusable `wire_schema_builder`-adjacent helper callable with source-header context, and update `app.py` to call it.
  - Tests: extend `tests/gui/test_app_wiring_schema.py` to assert the builder wiring still connects the menu action to the builder dialog.
  - Toolchain: full four-stage loop.
  - Acceptance: `src/gui/app.py` line count decreases further and stays <= 500; `src/gui/_schema_wiring.py` <= 500 lines; schema-builder menu behavior unchanged.

- [x] [P1-T3] Relocate the Run-gate logic surface for `can_run()` so the WS3 strengthening (Phase 2) lands with headroom: move the pure gate predicate from `pipeline_presenter.py` (490/500) into `src/gui/presenters/import_dispatch.py` (386/500) as a pure function `required_keys_present(imported, derived, is_running)`, and have `can_run()` delegate to it.
  - Tests: extend `tests/gui/test_pipeline_presenter.py` to assert `can_run()` delegates and current behavior is preserved (this task does not yet change the gate semantics).
  - Toolchain: full four-stage loop.
  - Acceptance: `src/gui/presenters/pipeline_presenter.py` line count decreases and stays <= 500; `import_dispatch.py` <= 500 lines; `can_run()` behavior byte-for-byte equivalent to baseline.

- [x] [P1-T4] Record the post-extraction line counts and confirm headroom for all later phases.
  - Acceptance: `<FEATURE>/evidence/other/post-extraction-file-sizes.md` exists with `Timestamp:` and per-file line counts showing `app.py`, `pipeline_presenter.py`, `import_dispatch.py`, and any new sibling modules all <= 500 lines.

---

### Phase 2 — WS5: Correct the `validate_aop` YTD Identity

> Headroom note: `src/_load_aop_helpers.py` is well under cap. Extract the per-row identity
> selection into a small pure helper so it is property-testable (T2) and to avoid growing
> `validate_aop` itself. AC-15: all test values are synthetic; no workbook figures.

- [x] [P2-T1] Add a pure helper `build_per_row_checks(columns: Sequence[str]) -> dict[str, list[str]]` in `src/_load_aop_helpers.py` that returns `{"YTD": [m for m in MONTHS if m not in YTG_MONTHS], "YTG": YTG_MONTHS, **QUARTER_TO_MONTHS}` when `"YTG"` is in `columns`, and `{"YTD": MONTHS, **QUARTER_TO_MONTHS}` when it is absent.
  - Tests: add `tests/test_load_aop_helpers.py` cases asserting the YTG-present mapping uses Jan..Apr for YTD and May..Dec for YTG, and the YTG-absent mapping uses full MONTHS for YTD.
  - Toolchain: full four-stage loop.
  - Acceptance: helper returns the corrected mappings for both branches; satisfies the construction half of AC-8 and AC-9.

- [x] [P2-T2] Replace the inline `per_row_checks` construction in `validate_aop` (`src/_load_aop_helpers.py:219-224`) with a call to `build_per_row_checks(frame.columns)`, and update the function docstring to state the corrected identity (YTD = sum of non-YTG months when YTG present; YTD = sum(MONTHS) when absent). Do not change the quarter checks, the duplicate-KEY warning, the empty-frame guard, or `TIEOUT_TOL`.
  - Tests: in `tests/test_load_aop_helpers.py`, add (a) a YTG-present synthetic frame where `YTD == sum(Jan..Apr)` and `YTG == sum(May..Dec)` passes; (b) a full-year synthetic frame (no YTG) where `YTD == sum(Jan..Dec)` passes.
  - Toolchain: full four-stage loop.
  - Acceptance: both synthetic frames validate without raising; `validate_aop` is corrected, not relaxed. Satisfies AC-8 and AC-9.

- [x] [P2-T3] Add negative-path tests proving genuine identity violations still raise `ValueError` under the corrected logic.
  - Tests: in `tests/test_load_aop_helpers.py`, add (a) a YTG-present synthetic frame with a row where `YTD != sum(Jan..Apr)` beyond `TIEOUT_TOL` raises `ValueError`; (b) a YTG-present frame where `YTG != sum(May..Dec)` raises `ValueError`; (c) a full-year frame where `YTD != sum(Jan..Dec)` raises `ValueError`.
  - Toolchain: full four-stage loop.
  - Acceptance: each violation raises `ValueError`; validation is corrected, not relaxed. Satisfies AC-10.

- [x] [P2-T4] Add at least one Hypothesis property test for the pure identity helper `build_per_row_checks` (T2 module requires >= 1 property test per pure function), using synthetic column lists only.
  - Tests: add a `tests/test_load_aop_helpers.py` property test asserting that for any input column set, YTD-months and YTG-months are disjoint when YTG is present and their union equals MONTHS, and YTD == MONTHS when YTG is absent.
  - Toolchain: full four-stage loop.
  - Acceptance: property test passes; no confidential figures used. Satisfies AC-15 (synthetic-only) and the T2 property-test obligation for WS5.

- [x] [P2-T5] Capture a WS5 regression-evidence artifact for the corrected identity.
  - Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_load_aop_helpers.py --cov=src._load_aop_helpers --cov-branch`.
  - Acceptance: `<FEATURE>/evidence/regression-testing/ws5-validate-aop.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording pass counts and module coverage %; confirms synthetic-only values (AC-15).

---

### Phase 3 — WS3: Gate the Run Action on All Three Import Keys

> Headroom note: the gate predicate now lives in `import_dispatch.py` (Phase 1, ample
> headroom); the `pipeline_presenter.py` change is delegation only.

- [x] [P3-T1] Strengthen `required_keys_present(...)` in `src/gui/presenters/import_dispatch.py` so it returns `True` only when all three required keys (`"LE"`, `"aop"`, `"sku_lu"`) are present in `_imported_tables`, OR a non-empty `_derived_tables` set exists (preserving re-run after a prior successful run), AND no job is running.
  - Tests: in `tests/gui/test_pipeline_presenter.py`, add parametrized cases: each single-key and two-key partial import returns `False`; all-three-keys present and not running returns `True`; non-empty derived set returns `True`; running state returns `False`.
  - Toolchain: full four-stage loop.
  - Acceptance: `can_run()` (delegating to the predicate) returns `True` only for the all-keys / derived-set cases. Satisfies AC-5.

- [x] [P3-T2] Add a partial-import-failure test proving no cascading `KeyError` can be produced by `run_pipeline`.
  - Tests: in `tests/gui/test_pipeline_presenter.py` (or `tests/gui/integration/test_behavioral_pipeline_run.py`), simulate LE + sku_lu imported but AOP failed, assert `can_run()` is `False` and that the run path is not dispatched, so `run_pipeline` is never reached with a missing `"aop"` key.
  - Toolchain: full four-stage loop.
  - Acceptance: partial import leaves Run disabled; no `KeyError: 'aop'` path is reachable. Satisfies AC-6.

---

### Phase 4 — WS4: Modal plus Status-Bar Error Surface

> Headroom note: `src/gui/_main_window_view.py` is 108/500 and `src/gui/protocols.py` is
> 298/500; both have ample headroom.

- [x] [P4-T1] Add a `show_dialog_error(title: str, message: str) -> None` method to `PipelineViewProtocol` in `src/gui/protocols.py` with a contract docstring (modal carries the full diagnostic; the status bar carries a summary).
  - Tests: extend `tests/gui/fakes/fake_views.py` `FakePipelineView` to record `show_dialog_error` calls; assert the protocol method is part of the view surface.
  - Toolchain: full four-stage loop.
  - Acceptance: `protocols.py` <= 500 lines; the fake records dialog-error calls.

- [x] [P4-T2] Implement `show_dialog_error` on `MainWindowPipelineView` (`src/gui/_main_window_view.py`) using `QMessageBox.critical(self._window, title, message)`, and update `show_error` to drive BOTH a `QMessageBox.critical` modal AND a concise status-bar summary via `MainWindow.set_status`.
  - Tests: add `tests/gui/test_main_window_view.py` offscreen test (`QT_QPA_PLATFORM=offscreen`, `qtbot`) asserting `show_error` invokes a modal (patch `QMessageBox.critical` at its import location in `_main_window_view`) and sets a status-bar summary.
  - Toolchain: full four-stage loop.
  - Acceptance: `_main_window_view.py` <= 500 lines; an error drives both a modal and a status summary. Satisfies AC-7.

- [x] [P4-T3] Route the presenter error callbacks `on_import_one_error`, `on_import_all_error`, and `on_run_error` through the modal-plus-status surface, and add an integration test that an import-failure path shows the modal and leaves Run disabled.
  - Files: `src/gui/presenters/import_dispatch.py` / `pipeline_presenter.py` error paths (verify they call `view.show_error` / `show_dialog_error`).
  - Tests: extend `tests/gui/integration/test_behavioral_import_buttons.py` or `test_behavioral_pipeline_run.py` to assert the modal is shown on import failure and Run stays disabled.
  - Toolchain: full four-stage loop.
  - Acceptance: import/run errors surface a modal plus status summary through `MainWindowPipelineView`. Satisfies AC-7 (combined with P4-T2).

---

### Phase 5 — WS1a: Qt KEY-Mismatch Dialog Seam

> Headroom note: `src/gui/pipeline_service.py` is 437/500 (63 lines). Inject the existing
> `etl_key` `prompt`/`is_tty` seam; do not modify `etl_key.py`, `load_aop.py`, or
> `normalize_le.py` defaults.

- [x] [P5-T1] Add a constructor-injectable KEY-mismatch resolver seam to `PipelineService` (`src/gui/pipeline_service.py`): accept a `key_mismatch_resolver: Callable[[], str] = lambda: "trust"` (or equivalent `prompt`/`is_tty` pair) defaulting so the service never reaches the stdin `input()` path, and document it.
  - Tests: in `tests/gui/test_pipeline_service.py`, assert the default resolver yields `"trust"` and that no real stdin is consulted.
  - Toolchain: full four-stage loop.
  - Acceptance: `pipeline_service.py` <= 500 lines; the default seam never reaches stdin.

- [x] [P5-T2] Wire `import_aop` (`pipeline_service.py:276`) to forward the injected seam to `load_aop.load_aop(...)` via its `key_mismatch`/`is_tty`/`prompt` parameters so the AOP path resolves through the injected resolver instead of the built-in `input`.
  - Tests: in `tests/gui/test_pipeline_service.py`, inject a fake resolver and assert: "Keep existing" maps to trust, "Rebuild" maps to overwrite, and the stdin `input()` path is never invoked for the AOP loader.
  - Toolchain: full four-stage loop.
  - Acceptance: the AOP import never reaches stdin; the dialog decision maps to loader policy. Satisfies AC-1 and AC-2 (AOP half).

- [x] [P5-T3] Wire `import_le` (the LE path via `normalize_le.load_source`, `pipeline_service.py:256`) to forward the same injected seam so the LE path also never reaches stdin.
  - Tests: in `tests/gui/test_pipeline_service.py`, repeat the trust/overwrite/no-stdin assertions for the LE loader path.
  - Toolchain: full four-stage loop.
  - Acceptance: the LE import never reaches stdin and uses the same dialog-based handling as AOP. Satisfies AC-3.

- [x] [P5-T4] Implement the Qt KEY-mismatch modal as the injected resolver at the composition root, offering "Keep existing" (trust, default) and "Rebuild" (overwrite), and inject it into `PipelineService` via the GUI wiring (`app.py` / a sibling wiring module from Phase 1).
  - Tests: add an offscreen test (`tests/gui/test_run_wiring.py` or `tests/gui/test_app_wiring_dispatch.py`) asserting the resolver is injected and that the default selection is "Keep existing" -> trust (patch `QMessageBox` at its import location; no real dialog).
  - Toolchain: full four-stage loop.
  - Acceptance: the composition root injects a Qt modal defaulting to "Keep existing"; mapped to loader policy. Completes AC-2; reinforces AC-1 and AC-3.

---

### Phase 6 — WS1b: Console-less Packaged Build

> Headroom note: `src/build_exe.py` and `pyproject.toml` are configuration; no near-cap risk.

- [x] [P6-T1] Add `--windows-console-mode=disable` to the Nuitka invocation in `src/build_exe.py` so packaged builds open no console window.
  - Tests: add `tests/test_build_exe.py` asserting the assembled Nuitka argument list contains `--windows-console-mode=disable` (inspect the build configuration; no runtime console assertion).
  - Toolchain: full four-stage loop.
  - Acceptance: the build invocation includes the console-disable flag. Satisfies AC-4 (build half).

- [x] [P6-T2] Provide a `gui`-style (non-console) packaged launch path so no launch mode performs stdin interaction: confirm the packaged entry resolves to `src.gui.app:main` without a `console_scripts` console allocation in the packaged artifact (configure the build/entry, not the dev `poetry run` console), and document that developer `poetry run` retains a logs-only console with no stdin interaction.
  - Tests: extend `tests/test_build_exe.py` (or add a config assertion test) verifying the packaged entry is the GUI main and that no stdin-interactive path is configured for any launch mode.
  - Toolchain: full four-stage loop.
  - Acceptance: packaged launch is console-less; dev console is logs-only with no stdin interaction (the WS1a seam guarantees no stdin). Satisfies AC-4.

---

### Phase 7 — WS2: Per-Tab Schema Dropdown

> Headroom note: `src/gui/widgets/source_input_widget.py` is 355/500 (~50-70 lines added,
> landing ~420), `source_selection_presenter.py` is 198/500, `protocols.py` is 298/500,
> `schema_service.py` is 245/500 — all have headroom. The `app.py` schema-builder wiring was
> already extracted in Phase 1 (P1-T2). Known-file loaders remain the default path (AC-14).

- [x] [P7-T1] Add a schema `QComboBox` (with `<Choose Schema>` as the first/placeholder item) and a "Build new schema" `QPushButton` to `SourceInputWidget` (`src/gui/widgets/source_input_widget.py`), plus a `schema_selected: Signal = Signal(str)` signal, a `build_schema_requested` signal, and view methods `set_schema_list(names: list[str]) -> None` and `set_selected_schema(name: str) -> None`.
  - Tests: extend `tests/gui/test_source_input_widget.py` (offscreen) asserting the placeholder is present, `set_schema_list` populates the combo, `set_selected_schema` selects a name, and changing the combo emits `schema_selected`.
  - Toolchain: full four-stage loop.
  - Acceptance: `source_input_widget.py` <= 500 lines; combo, button, signals, and view methods present and tested. Supports AC-11, AC-12, AC-13.

- [x] [P7-T2] Extend `SourceSelectionViewProtocol` in `src/gui/protocols.py` with `set_schema_list` and `set_selected_schema`, and update `tests/gui/fakes` view fakes to record those calls.
  - Tests: update the relevant fake in `tests/gui/fakes/` and assert the protocol methods are recorded.
  - Toolchain: full four-stage loop.
  - Acceptance: `protocols.py` <= 500 lines; the protocol declares the two schema-view methods.

- [x] [P7-T3] Add an `on_schema_discovery(path: str, sheet: str) -> None` handler to `SourceSelectionPresenter` (`src/gui/presenters/source_selection_presenter.py`) that reads a header preview, calls `SchemaServiceProtocol.find_best_match(headers)`, applies `_schema_wiring.discover_schema`, and on `action="proceed"` calls `view.set_selected_schema(match_name)`; the `SchemaServiceProtocol` is injected via the composition root.
  - Tests: extend `tests/gui/test_source_selection_presenter.py` asserting `action="proceed"` selects the matched schema name.
  - Toolchain: full four-stage loop.
  - Acceptance: a matching schema auto-selects on tab activation. Satisfies AC-11.

- [x] [P7-T4] Handle the no-match path in `on_schema_discovery`: when `discover_schema` returns `action="resolve"`, leave the combo at the `<Choose Schema>` placeholder (do not auto-select).
  - Tests: extend `tests/gui/test_source_selection_presenter.py` asserting `action="resolve"` leaves the placeholder selected and does not call `set_selected_schema` with a real schema name.
  - Toolchain: full four-stage loop.
  - Acceptance: no-match leaves the `<Choose Schema>` placeholder. Satisfies AC-12.

- [x] [P7-T5] Wire the "Build new schema" button's `build_schema_requested` signal to the extracted schema-builder helper (from P1-T2) at the composition root, passing the current source headers as context.
  - Tests: add/extend `tests/gui/integration/test_behavioral_schema_import.py` (offscreen) asserting the button opens the existing schema builder dialog (patch the dialog at its import location).
  - Toolchain: full four-stage loop.
  - Acceptance: the per-tab "Build new schema" button opens the existing schema builder dialog. Satisfies AC-13.

- [x] [P7-T6] Add a test confirming schema selection is additive: the known-file loaders (`import_le`/`import_aop`/`import_skulu`) remain the default import path and their default behavior is unchanged by the schema dropdown.
  - Tests: extend `tests/gui/test_pipeline_service.py` or an integration test asserting that with no non-default schema selected, the default loaders are used and produce unchanged output.
  - Toolchain: full four-stage loop.
  - Acceptance: default import path unchanged; schema selection is additive. Satisfies AC-14.

---

### Phase 8 — End-to-End Integration

> Headroom note: integration tests live under `tests/gui/integration/`; no production files
> near cap are touched.

- [x] [P8-T1] Add an offscreen end-to-end test exercising a partial-import-failure run: AOP import fails, the modal surfaces the error, Run stays disabled, and no `KeyError` occurs.
  - Tests: add to `tests/gui/integration/test_behavioral_pipeline_run.py` (offscreen, `qtbot`).
  - Toolchain: full four-stage loop.
  - Acceptance: end-to-end partial-failure path shows the modal, disables Run, and produces no cascade. Cross-checks AC-6 and AC-7.

- [x] [P8-T2] Add an offscreen end-to-end test for the schema-selection flow on a source tab: a matching header preview auto-selects a schema; a non-matching preview shows `<Choose Schema>`; the build button opens the builder.
  - Tests: add to `tests/gui/integration/test_behavioral_schema_import.py` (offscreen).
  - Toolchain: full four-stage loop.
  - Acceptance: end-to-end schema flow exercises auto-select, placeholder, and build-new. Cross-checks AC-11, AC-12, AC-13.

- [x] [P8-T3] Add an end-to-end test (or assertion in an existing integration test) confirming no GUI path reaches stdin during import (AOP and LE), using injected resolvers.
  - Tests: extend `tests/gui/integration/test_behavioral_composition.py`.
  - Toolchain: full four-stage loop.
  - Acceptance: no stdin interaction occurs in the composed GUI import path. Cross-checks AC-1, AC-3.

---

### Phase 9 — Final QA Loop and AC Checkoff

> Headroom note: re-measure every touched file; any file at or over 500 lines is a blocking
> finding requiring extraction before sign-off.

- [x] [P9-T1] Run the final formatting check and record evidence.
  - Command: `env -u VIRTUAL_ENV poetry run black --check .`
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-format.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:` (0), `Output Summary:`. Restart the loop from formatting if any file changes.

- [x] [P9-T2] Run the final lint check and record evidence.
  - Command: `env -u VIRTUAL_ENV poetry run ruff check .`
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-lint.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:` (0), `Output Summary:` recording zero lint errors.

- [x] [P9-T3] Run the final type check and record evidence.
  - Command: `env -u VIRTUAL_ENV poetry run pyright`
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-type.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:` (0), `Output Summary:` recording zero type errors and no new `Any`/`# type: ignore` in T2 modules.

- [x] [P9-T4] Run the final coverage-enabled test suite and record evidence.
  - Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-tests.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:` (0), and `Output Summary:` recording numeric post-change line-coverage % and branch-coverage % plus passed/failed counts.

- [x] [P9-T5] Verify the coverage delta and thresholds against the Phase 0 baseline.
  - Acceptance: `<FEATURE>/evidence/qa-gates/coverage-delta.md` exists with `Timestamp:` and reports baseline line/branch coverage (from P0-T3), post-change line/branch coverage (from P9-T4), and changed-code coverage; confirms line >= 85%, branch >= 75%, and no regression on changed lines. If any threshold is unmet, outcome is remediation-required (not PASS).

- [x] [P9-T6] Verify the 500-line cap holds for every touched file and new module.
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-file-sizes.md` exists with `Timestamp:` and per-file line counts; every production, test, and reusable-script file touched or added is <= 500 lines.

- [x] [P9-T7] Complete the AC-1..AC-15 traceability checkoff against the recorded evidence.
  - Acceptance: `<FEATURE>/evidence/qa-gates/ac-checkoff.md` exists with `Timestamp:` and each AC (AC-1..AC-15) marked satisfied with a pointer to the satisfying task(s) and evidence artifact; AC-15 confirms no confidential workbook figures appear in any committed artifact.

---

## AC Traceability (AC-1..AC-15 → Tasks)

| AC | Workstream | Satisfying task(s) |
|---|---|---|
| AC-1 (no stdin; KEY-mismatch via Qt modal) | WS1a | P5-T1, P5-T2, P5-T4, P8-T3 |
| AC-2 (modal Keep existing/Rebuild, default Keep existing, maps to policy) | WS1a | P5-T2, P5-T4 |
| AC-3 (LE path same dialog handling, no stdin) | WS1a | P5-T3, P8-T3 |
| AC-4 (packaged build no console; dev console logs-only) | WS1b | P6-T1, P6-T2 |
| AC-5 (`can_run()` true only with all three keys or derived set) | WS3 | P3-T1 |
| AC-6 (partial import disables Run; no cascading `KeyError`) | WS3 | P3-T2, P8-T1 |
| AC-7 (modal + status-bar error surface) | WS4 | P4-T1, P4-T2, P4-T3, P8-T1 |
| AC-8 (YTG present: YTD=Jan..Apr, YTG=May..Dec) | WS5 | P2-T1, P2-T2 |
| AC-9 (YTG absent: YTD=sum(MONTHS)) | WS5 | P2-T1, P2-T2 |
| AC-10 (genuine violations still raise `ValueError`) | WS5 | P2-T3 |
| AC-11 (auto-select matching schema on `proceed`) | WS2 | P7-T1, P7-T3, P8-T2 |
| AC-12 (`<Choose Schema>` placeholder on `resolve`) | WS2 | P7-T1, P7-T4, P8-T2 |
| AC-13 ("Build new schema" opens builder dialog) | WS2 | P7-T1, P7-T5, P8-T2 |
| AC-14 (known-file loaders remain default; additive) | WS2 | P7-T6 |
| AC-15 (no confidential figures; synthetic test values) | WS5 | P2-T4, P2-T5, P9-T7 |

## Evidence Artifact Index (canonical paths)

- `<FEATURE>/evidence/baseline/phase0-instructions-read.md` (P0-T1)
- `<FEATURE>/evidence/baseline/baseline-static.md` (P0-T2)
- `<FEATURE>/evidence/baseline/baseline-tests.md` (P0-T3)
- `<FEATURE>/evidence/baseline/baseline-file-sizes.md` (P0-T4)
- `<FEATURE>/evidence/other/post-extraction-file-sizes.md` (P1-T4)
- `<FEATURE>/evidence/regression-testing/ws5-validate-aop.md` (P2-T5)
- `<FEATURE>/evidence/qa-gates/final-format.md` (P9-T1)
- `<FEATURE>/evidence/qa-gates/final-lint.md` (P9-T2)
- `<FEATURE>/evidence/qa-gates/final-type.md` (P9-T3)
- `<FEATURE>/evidence/qa-gates/final-tests.md` (P9-T4)
- `<FEATURE>/evidence/qa-gates/coverage-delta.md` (P9-T5)
- `<FEATURE>/evidence/qa-gates/final-file-sizes.md` (P9-T6)
- `<FEATURE>/evidence/qa-gates/ac-checkoff.md` (P9-T7)
