# gui-render-import-ux — Atomic Implementation Plan

- **Issue:** #27
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-28T23-30
- **Status:** Draft
- **Version:** 1.0
- **Work Mode:** full-feature

## Required References

All work must comply with these policies; their content is not duplicated here.

- `CLAUDE.md` (standing instructions)
- `.claude/rules/general-code-change.md`
- `.claude/rules/general-unit-test.md`
- `.claude/rules/python.md`
- `.claude/rules/python-suppressions.md`
- `.claude/rules/quality-tiers.md`
- `.claude/rules/self-explanatory-code-commenting.md`
- `.claude/rules/tonality.md`

## Authoritative Inputs

- Spec: `docs/features/active/2026-05-28-gui-render-import-ux-27/spec.md`
- Acceptance criteria (AC1–AC14): `docs/features/active/2026-05-28-gui-render-import-ux-27/issue.md`
- User stories: `docs/features/active/2026-05-28-gui-render-import-ux-27/user-story.md`
- Research: `artifacts/research/gui-render-import-ux-27.md`

## Settled Design Decisions (do not re-litigate)

1. Mutual exclusion and preview-clear wiring via the `src/gui/_render_exclusivity.py`
   helper module (public entry point `wire_render_checkboxes`, which reuses the
   retained public `wire_render_exclusivity`), called once from `app.py`
   `build_application`, with `blockSignals` re-entrancy guards (not
   `QButtonGroup`). Displaced boxes are unchecked with signals blocked so their
   clear-preview callbacks do not fire. Zero-checked state stays reachable. The
   wiring lives in the helper rather than inline in `app.py` to keep `app.py`
   under the 500-line cap.
2. Off-thread imports via new presenter methods `make_import_one_task` /
   `make_import_all_task` and slots `on_import_one_success` /
   `on_import_one_error` / `on_import_all_success` / `on_import_all_error`,
   mirroring `make_run_task` / `on_run_success` / `on_run_error`.
   `_handle_import_one` / `_handle_import_all` dispatch through the injected
   `RunnerProtocol`. `PipelineWorker` reused unchanged. `SynchronousRunner`
   remains the deterministic test seam.
3. Completion feedback: `show_result("Imported {name}.")` (import-one) and
   `show_result("Imported all 3 sources.")` (import-all) in success callbacks.
4. Layout: `SourceInputWidget` gains optional `import_label: str | None = None`
   ctor param and an `import_btn` property; `MainWindow` re-exposes
   `import_le_btn` / `import_aop_btn` / `import_skulu_btn` as property forwarders
   to the widgets' `import_btn`, removing the three per-input buttons from the
   control row (keeping Import All). `set_import_button_enabled` is unchanged.

## Execution Constraints

- **Per-batch budget:** at most 3 production files + 3 test files per executable
  batch. Phases below are sequenced to stay within budget.
- **Toolchain loop (run in order, restart on any change/failure):**
  1. `env -u VIRTUAL_ENV poetry run black .`
  2. `env -u VIRTUAL_ENV poetry run ruff check .`
  3. `env -u VIRTUAL_ENV poetry run pyright`
  4. `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Prefix every Poetry invocation with `env -u VIRTUAL_ENV` (Poetry env quirk:
    `VIRTUAL_ENV` points at the global interpreter; without the prefix Poetry can
    install/run against the wrong environment).
  - Set `QT_QPA_PLATFORM=offscreen` for all pytest runs (pytest-qt headless).
- **File-size cap (500 lines).** Current sizes to watch:
  - `src/gui/app.py` — was exactly 500 lines at baseline and is currently 504
    lines on disk after the inline exclusivity wiring landed (P1-T2 first attempt),
    which exceeds the hard cap. The revised P1-T2 removes the inline
    `_make_preview_clear` factory, its three `toggled` connects, and the inline
    exclusivity call, replacing them with a single `wire_render_checkboxes(...)`
    call so `app.py` drops back below 500. P3 routes import dispatch through small
    helpers to avoid growth.
  - `src/gui/presenters/pipeline_presenter.py` ≈ 487 lines — adding six methods
    will exceed 500. P2-T1 extracts the import task/callback logic into a
    dedicated collaborator module so the presenter file stays under the cap.
  - `src/gui/widgets/source_input_widget.py` ≈ 304 lines — has headroom for the
    optional import button.
- **Coverage:** line ≥ 85%, branch ≥ 75%, no regression on changed lines. Every
  production change is paired with test coverage in the same phase.
- **Evidence:** all evidence artifacts go under
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/<kind>/`.
  Non-canonical `artifacts/...` evidence paths are forbidden.

---

### Phase 0 — Baseline Capture and Policy Read

- [x] [P0-T1] Read the policy files in the required order
  (`CLAUDE.md` → `.claude/rules/general-code-change.md` →
  `.claude/rules/general-unit-test.md` → `.claude/rules/python.md` →
  `.claude/rules/python-suppressions.md` → `.claude/rules/quality-tiers.md` →
  `.claude/rules/self-explanatory-code-commenting.md` →
  `.claude/rules/tonality.md`). Record a Phase 0 read-evidence artifact at
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/baseline/phase0-instructions-read.md`
  containing `Timestamp:`, `Policy Order:`, and the explicit list of files read.
  Acceptance: artifact exists with all three fields populated.
- [x] [P0-T2] Capture the baseline format state. Run
  `env -u VIRTUAL_ENV poetry run black --check .` and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/baseline/black-check.<ts>.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
  Acceptance: artifact records the exit code and a one-line pass/fail summary.
- [x] [P0-T3] Capture the baseline lint state. Run
  `env -u VIRTUAL_ENV poetry run ruff check .` and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/baseline/ruff-check.<ts>.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count).
  Acceptance: artifact records exit code and error count.
- [x] [P0-T4] Capture the baseline type-check state. Run
  `env -u VIRTUAL_ENV poetry run pyright` and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/baseline/pyright.<ts>.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning
  counts). Acceptance: artifact records exit code and counts.
- [x] [P0-T5] Capture the baseline test + coverage state. Run
  `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
  and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/baseline/pytest-coverage.<ts>.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including the
  numeric baseline **line coverage %** and **branch coverage %** and the
  pass/fail count. Acceptance: artifact records numeric line and branch coverage
  headline values (not placeholders).

---

### Phase 1 — Change 1: Mutually-Exclusive Render-Tab Checkboxes (AC1–AC3)

Batch: 2 production files (`src/gui/_render_exclusivity.py` — already created in
P1-T1, public entry point `wire_render_checkboxes` plus retained
`wire_render_exclusivity`; `src/gui/app.py`) + 1 test file
(`tests/gui/test_app_wiring.py`).

- [x] [P1-T1] Create `src/gui/_render_exclusivity.py` exposing two public wiring
  helpers (the "only public symbol" clause is relaxed to allow a small, named
  public surface). Define the single composition-root entry point
  `wire_render_checkboxes(checkboxes: Sequence[QCheckBox],
  clear_callbacks: Sequence[Callable[[], None]]) -> None` (module + function
  docstrings per `self-explanatory-code-commenting.md`), which folds in the
  preview-clear wiring formerly inlined in `app.py`:
  - For each `(checkbox, clear_callback)` pair (positionally aligned), connect the
    checkbox's `toggled` signal to a closure that invokes `clear_callback()` only
    on a `toggled(False)` transition — preserving the existing
    `_make_preview_clear` "if not checked: clear" semantics.
  - Apply mutual exclusion across the same checkboxes via `blockSignals(True)` /
    `blockSignals(False)` re-entrancy guards (the existing
    `wire_render_exclusivity` logic): on a check-to-`True` transition, the other
    boxes are `setChecked(False)` with their signals blocked across exactly each
    `setChecked` call, so the displaced unchecks do NOT fire their clear-preview
    callbacks and the newly-checked widget's preview survives.
  Decision (stated explicitly): retain the existing `wire_render_exclusivity`
  helper as a public symbol so the pure exclusivity logic stays independently
  testable, and have `wire_render_checkboxes` reuse it internally (wire
  preview-clear closures first, then call `wire_render_exclusivity` on the same
  box list). `__all__` lists both helpers. Keep the file well under 500 lines.
  Acceptance: module imports cleanly; public surface is exactly
  `wire_render_checkboxes` and `wire_render_exclusivity`; no Qt logic beyond
  signal wiring; preview-clear closures fire only on `toggled(False)`.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC1, AC2 (suppression mechanism), AC3 (zero-checked preserved).
- [x] [P1-T2] In `src/gui/app.py` `build_application`, remove the inline
  `_make_preview_clear` factory, its three `le_box.toggled.connect(...)` /
  `aop_box.toggled.connect(...)` / `skulu_box.toggled.connect(...)` connections,
  and the inline `wire_render_exclusivity([...])` call (currently lines ~340–358).
  Replace them with a single call to `wire_render_checkboxes`, passing the three
  render checkboxes and the three clear-preview callbacks
  (`le_presenter.on_clear_preview`, `aop_presenter.on_clear_preview`,
  `skulu_presenter.on_clear_preview`) positionally aligned. Update the import to
  pull `wire_render_checkboxes` from `src/gui/_render_exclusivity.py`; drop the
  unused `wire_render_exclusivity` import and the now-unused `Callable` import if
  `_make_preview_clear` was its only consumer. Net effect: `app.py` drops ~10
  lines, well below the cap. Acceptance: `app.py` ≤ 500 lines; clear-preview
  behavior unchanged on user uncheck; exclusivity active; no spurious
  clear-preview fires on displaced unchecks.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC1, AC2, AC3.
- [x] [P1-T3] In `tests/gui/test_app_wiring.py` add behavioral tests using the
  fully-wired application (`build_application` with `SynchronousRunner`), so they
  exercise the public surface `wire_render_checkboxes` wires through `app.py`:
  (a) checking AOP after LE is checked leaves AOP checked and LE+SKU_LU
  unchecked; (b) checking each box in turn leaves exactly that box checked;
  (c) checking one box does not invoke `on_clear_preview` on the displaced
  presenters (assert via a recording fake / spy on the preview sink so no
  spurious `show_preview([])` fires for the newly-checked widget); (d) unchecking
  the active box leaves all three unchecked and clears the shared preview
  (zero-checked reachable). Optionally add one direct unit test importing
  `wire_render_exclusivity` to assert the pure exclusivity guard in isolation.
  Arrange–Act–Assert; deterministic; no timing APIs. Acceptance: all four
  behavioral tests pass; existing
  `test_build_application_unchecking_render_clears_preview` still passes.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC1, AC2, AC3.

---

### Phase 2 — Change 2/3: Off-Thread Import Tasks + Completion Messages in the Presenter (AC4–AC10 presenter surface)

Batch: 2 production files (`src/gui/presenters/import_dispatch.py` [new],
`src/gui/presenters/pipeline_presenter.py`) + 2 test files
(`tests/gui/test_pipeline_presenter.py`, `tests/gui/test_pipeline_presenter_v2.py`).

- [x] [P2-T1] Create `src/gui/presenters/import_dispatch.py` to hold the import
  task/callback success-and-error logic extracted from the current synchronous
  `on_import_one` / `on_import_all` (so `pipeline_presenter.py` stays ≤ 500
  lines). Provide module-level helper functions that operate on presenter state
  passed in explicitly (no new class with hidden state), or a thin
  `ImportDispatch` collaborator constructed from the presenter's view and
  service references. Each function/method carries a full docstring. Acceptance:
  module imports cleanly; no Qt import; public surface limited to the helpers the
  presenter delegates to.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC4–AC10 (logic relocation enabling off-thread dispatch).
- [x] [P2-T2] In `src/gui/presenters/pipeline_presenter.py` add the six public
  methods, delegating their bodies to the P2-T1 helpers:
  - `make_import_one_task(name, spec) -> Callable[[], dict[str, pd.DataFrame]]`
    returning a zero-arg callable that calls `_import_one_frame(name, spec)` and
    returns `{name: frame}` (loader `ValueError` propagates out of the callable).
  - `on_import_one_success(result)` — records the frame, updates
    `_last_imported_path`, sets `_derived_tables = {}`, disables the keyed import
    button via `set_import_button_enabled(name, False)`, pushes
    `set_run_button_enabled(self.can_run())` and `_push_action_enabled_states()`,
    clears busy via `_set_running(False)`, and emits
    `view.show_result(f"Imported {name}.")`.
  - `on_import_one_error(message)` — calls `view.show_error(message)`, clears busy
    via `_set_running(False)`; leaves the keyed import button enabled.
  - `make_import_all_task(spec) -> Callable[[], dict[str, pd.DataFrame]]`
    returning a callable that calls `service.import_sources(spec)` and returns the
    three-entry dict.
  - `on_import_all_success(result)` — records all frames, updates per-key paths,
    sets `_derived_tables = {}`, disables the three keyed buttons, pushes Run/
    Save/Export states, clears busy, and emits
    `view.show_result("Imported all 3 sources.")`.
  - `on_import_all_error(message)` — calls `view.show_error(message)`, clears busy.
  Retain the existing synchronous `on_import_one` / `on_import_all` as internal
  helpers (or have them call the new callbacks) so the public surface grows
  without breaking. Confirm `pipeline_presenter.py` ≤ 500 lines (logic lives in
  P2-T1). Acceptance: all six methods present, typed, documented; file ≤ 500
  lines; existing presenter tests still pass.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC4, AC5, AC6, AC7, AC8, AC9, AC10.
- [x] [P2-T3] In `tests/gui/test_pipeline_presenter.py` add unit tests against a
  fake view (no `QApplication`): `make_import_one_task` returns a callable
  producing `{name: frame}` per key; the callable raises `ValueError` when the
  loader fails; `on_import_one_success` records the frame, sets last-imported
  path, invalidates `_derived_tables`, disables the keyed button, recomputes
  Run/Save/Export, clears busy, and emits `"Imported {name}."` via the fake
  view's `show_result`; `on_import_one_error` routes the message to `show_error`,
  clears busy, and leaves the button enabled. Acceptance: tests pass; changed
  presenter lines covered.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC4, AC6, AC7, AC8, AC9.
- [x] [P2-T4] In `tests/gui/test_pipeline_presenter_v2.py` add unit tests for the
  import-all trio: `make_import_all_task` returns a callable producing the
  three-entry dict; `on_import_all_success` records all frames, updates per-key
  paths, invalidates derived tables, disables the three keyed buttons, recomputes
  Run/Save/Export, clears busy, and emits `"Imported all 3 sources."` via
  `show_result`; `on_import_all_error` routes to `show_error` and clears busy.
  Add a busy-state assertion (`set_running(True)` reflected during dispatch and
  `False` after completion) consistent with the Run path. Acceptance: tests pass;
  changed presenter lines covered.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC5, AC6, AC7, AC8, AC10.

---

### Phase 3 — Change 2: Composition-Root Off-Thread Import Dispatch (AC4, AC5, AC8)

Batch: 1 production file (`src/gui/app.py`) + 2 test files
(`tests/gui/test_app_wiring.py`, `tests/gui/integration/test_behavioral_import_buttons.py`).

- [x] [P3-T1] In `src/gui/app.py` `wire_control_signals`, rewrite
  `_handle_import_one(name)` to build the task with
  `pipeline_presenter.make_import_one_task(name, _current_import_spec(window))`,
  disable the keyed button before dispatch (route through the view adapter:
  `pipeline_presenter` view's `set_import_button_enabled(name, False)` at dispatch
  time to prevent double-dispatch), then call
  `runner.run(task, pipeline_presenter.on_import_one_success,
  pipeline_presenter.on_import_one_error)`. Rewrite `_handle_import_all()`
  analogously with `make_import_all_task`, disabling Import All (and the three
  keyed buttons) at dispatch time, dispatching through `runner.run` with the
  import-all success/error callbacks. Keep both handlers small; if `app.py`
  approaches 500 lines, factor the busy/disable-before-dispatch step into a small
  module-private helper in `app.py` or in a new `src/gui/_import_dispatch_wiring.py`
  (prefer the existing file only if it stays ≤ 500 lines; otherwise extract).
  Acceptance: both handlers dispatch through `runner`, not directly on the
  presenter; `app.py` ≤ 500 lines.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC4, AC5, AC8.
- [x] [P3-T2] In `tests/gui/test_app_wiring.py` update/extend the import-routing
  tests to assert dispatch goes through the injected runner: confirm
  `test_import_one_signal_routes_to_presenter_with_live_spec` and
  `test_import_all_signal_routes_to_presenter` still pass with `SynchronousRunner`
  (tables populated synchronously before assertion), and add a test that injects a
  recording fake runner verifying `_handle_import_one` / `_handle_import_all`
  call `runner.run` (not the presenter's synchronous `on_import_one` /
  `on_import_all` directly). Acceptance: routing tests pass; recording-runner test
  proves the dispatch seam is used.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC4, AC5.
- [x] [P3-T3] In `tests/gui/integration/test_behavioral_import_buttons.py`
  confirm all existing tests pass unchanged with `SynchronousRunner` (assertions
  fire after the synchronous callback). Add a test asserting that on a loader
  `ValueError` the keyed button remains enabled and the message routes to the
  status bar (`show_error` path), and a test asserting the busy state is cleared
  after completion. Add a test asserting the success completion message appears
  in the status bar for import-one and import-all. Acceptance: existing ten tests
  pass; new error/busy/message tests pass.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC4, AC5, AC6, AC8, AC9, AC10.

---

### Phase 4 — Change 4: Layout Relocation of Per-Input Import Buttons (AC11–AC13)

Batch: 2 production files (`src/gui/widgets/source_input_widget.py`,
`src/gui/main_window.py`) + 2 test files
(`tests/gui/test_source_input_widget.py`, `tests/gui/test_main_window.py`).

- [x] [P4-T1] In `src/gui/widgets/source_input_widget.py` add an optional
  constructor parameter `import_label: str | None = None`. When supplied (or
  defaulted to `f"Import {input_label}"` when the caller opts in), construct an
  import `QPushButton` and add it to the widget's `QVBoxLayout` beside the
  Render-tab checkbox; when `None`, construct no button. Expose a read-only
  `import_btn` property returning the button (raising or documenting behavior when
  no button was constructed). Update the class docstring to record the new
  passive UI child and the `import_btn` attribute. Confirm file ≤ 500 lines
  (currently ≈ 304). Acceptance: widget constructs with and without the import
  button; `import_btn` resolves when constructed.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC11.
- [x] [P4-T2] In `src/gui/main_window.py` `__init__`: construct each
  `SourceInputWidget` with its import label (`"LE"`/`"AOP"`/`"SKU_LU"` →
  `import_label="Import LE"` etc.); remove the three standalone
  `self.import_le_btn` / `import_aop_btn` / `import_skulu_btn` `QPushButton`
  constructions and their `controls_row.addWidget(...)` calls (Import All, Run,
  Save, Open, Export remain in the row); add read-only properties
  `import_le_btn`, `import_aop_btn`, `import_skulu_btn` delegating to
  `self.le_widget.import_btn` / `aop_widget.import_btn` / `skulu_widget.import_btn`;
  wire each widget button's `clicked` signal to emit `import_one_requested` with
  the matching key (`"LE"`, `"aop"`, `"sku_lu"`), reading the button through the
  widget. Update the class docstring. Confirm file ≤ 500 lines. Acceptance:
  three per-input buttons absent from `controls_row`; Import All present;
  `import_le_btn`/`import_aop_btn`/`import_skulu_btn` resolve through the widgets;
  `import_one_requested` still emits the correct key.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC11, AC12, AC13.
- [x] [P4-T3] In `tests/gui/test_source_input_widget.py` add tests: a widget
  constructed with `import_label` exposes `import_btn` with the expected label
  text and the button lives inside the widget; a widget constructed without
  `import_label` constructs no import button (documented behavior verified).
  Acceptance: tests pass.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC11.
- [x] [P4-T4] In `tests/gui/test_main_window.py` confirm the existing
  `test_main_window_exposes_import_le_btn_publicly` /
  `_aop_` / `_skulu_` tests still pass (now resolving through the new properties).
  Add a test asserting the three per-input import buttons are NOT direct children
  of the `controls_row` layout but ARE children of their source widgets, and that
  Import All remains in the control row. Acceptance: existing eight attribute
  tests pass; new layout-location test passes.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC11, AC12, AC13.

---

### Phase 5 — Cross-Cutting Test Reconciliation (AC13 contract, regression safety)

Batch: 0 production files + 2 test files
(`tests/gui/integration/test_behavioral_composition.py`,
`tests/gui/test_app_wiring.py` adapter section).

- [x] [P5-T1] In `tests/gui/integration/test_behavioral_composition.py` confirm
  `test_composition_smoke_all_control_buttons_addressable` still passes (the loop
  over the eight attribute names now resolves the three import buttons through
  `MainWindow` properties). Acceptance: composition smoke test passes unchanged.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC13.
- [x] [P5-T2] In `tests/gui/test_app_wiring.py` confirm the
  `set_import_button_enabled` adapter tests (asserting on
  `window.import_le_btn.isEnabled()` etc.) still pass through the re-export
  properties; if any adapter test exercised the old direct-attribute button it
  must resolve unchanged. Acceptance: all `set_import_button_enabled` adapter
  tests pass; no test rewrite required beyond confirmation.
  Toolchain: black → ruff → pyright → pytest.
  Satisfies: AC13.

---

### Phase 6 — Final QA Loop and Acceptance Check-Off (AC14)

Run the full toolchain loop in order; restart from step 1 on any failure or
file change. Persist one final-QC artifact per command step.

- [x] [P6-T1] Run `env -u VIRTUAL_ENV poetry run black .` and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/qa-gates/black.<ts>.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance:
  exit code 0 and no files reformatted on the final pass.
  Satisfies: AC14.
- [x] [P6-T2] Run `env -u VIRTUAL_ENV poetry run ruff check .` and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/qa-gates/ruff.<ts>.md`
  with the four schema fields. Acceptance: exit code 0, zero lint errors.
  Satisfies: AC14.
- [x] [P6-T3] Run `env -u VIRTUAL_ENV poetry run pyright` and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/qa-gates/pyright.<ts>.md`
  with the four schema fields. Acceptance: exit code 0, zero type errors.
  Satisfies: AC14.
- [x] [P6-T4] Run
  `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
  and write
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/qa-gates/pytest-coverage.<ts>.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including the
  numeric **post-change line coverage %** and **branch coverage %** and the
  pass/fail count. Acceptance: all tests pass; line ≥ 85%, branch ≥ 75%.
  Satisfies: AC14.
- [x] [P6-T5] Write a coverage-delta verification artifact at
  `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/qa-gates/coverage-delta.<ts>.md`
  reporting baseline line/branch coverage (from P0-T5), post-change line/branch
  coverage (from P6-T4), and changed-line coverage for the four touched
  production files plus the two new modules. Acceptance: no regression on changed
  lines; thresholds met. If any required coverage value is unavailable, mark the
  outcome remediation-required (not PASS).
  Satisfies: AC14.
- [x] [P6-T6] Check off AC1–AC14 against the evidence and update the AC checklist
  in `docs/features/active/2026-05-28-gui-render-import-ux-27/issue.md`. Acceptance:
  every AC is marked complete with a pointer to the satisfying task(s)/evidence;
  any unmet AC is recorded as remediation-required.
  Satisfies: AC14.

---

## Traceability Matrix (AC → Tasks)

| AC | Description | Tasks |
|---|---|---|
| AC1 | Checking one Render-tab box unchecks the other two | P1-T1, P1-T2, P1-T3 |
| AC2 | Displaced unchecks do not invoke `on_clear_preview` / clear the new preview | P1-T1, P1-T2, P1-T3 |
| AC3 | Zero-checked state reachable (uncheck active box clears preview) | P1-T1, P1-T2, P1-T3 |
| AC4 | Import-one dispatched through `RunnerProtocol` | P2-T1, P2-T2, P2-T3, P3-T1, P3-T2, P3-T3 |
| AC5 | Import-all dispatched through `RunnerProtocol` | P2-T1, P2-T2, P2-T4, P3-T1, P3-T2, P3-T3 |
| AC6 | Success disables keyed button; `ValueError` leaves it enabled, routes to `show_error` | P2-T2, P2-T3, P2-T4, P3-T3 |
| AC7 | Successful import invalidates derived-table set | P2-T2, P2-T3, P2-T4 |
| AC8 | Busy state during import, idle on completion | P2-T2, P2-T4, P3-T1, P3-T3 |
| AC9 | Import-one completion message via `show_result` | P2-T2, P2-T3, P3-T3 |
| AC10 | Import-all completion message via `show_result` | P2-T2, P2-T4, P3-T3 |
| AC11 | Per-input Import button inside `SourceInputWidget`; `import_btn` exposed | P4-T1, P4-T2, P4-T3, P4-T4 |
| AC12 | Import All in control row; per-input buttons absent from control row | P4-T2, P4-T4 |
| AC13 | `MainWindow.import_*_btn` resolve to widget-owned buttons; adapter/tests unchanged | P4-T2, P4-T4, P5-T1, P5-T2 |
| AC14 | Toolchain passes; line ≥ 85%, branch ≥ 75%, no regression on changed lines | P0-T2..T5, P6-T1..T6 |

## Follow-Up (out of scope for #27)

- `SourceSelectionPresenter.on_file_selected` and `on_render_tab` still read the
  workbook synchronously on the UI thread. Moving these off-thread is a recorded
  follow-up work item, not delivered by issue #27.
