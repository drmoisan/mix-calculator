# schema-builder-ux-overhaul - Plan

- **Issue:** #72
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-16T14-25
- **Status:** Draft
- **Version:** 1.0
- **Work Mode:** full-feature

## Required References

- General Coding Standards: `.claude/rules/general-code-change.md`
- General Unit Test Policy: `.claude/rules/general-unit-test.md`
- Python Standards: `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
- Quality Tiers: `.claude/rules/quality-tiers.md`
- Commenting Policy: `.claude/rules/self-explanatory-code-commenting.md`

**All work must comply with these policies; do not duplicate their content here.**

## Authoritative Inputs

- Spec (resolved D-1/D-2/D-3, AC-1..AC-11): `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/spec.md`
- Issue: `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/issue.md`
- Research: `artifacts/research/schema-builder-ux-overhaul-72.md`

## Evidence Location (Canonical, Non-Overridable)

All evidence artifacts resolve to `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/evidence/<kind>/`:
- Phase 0 policy read + baselines: `.../evidence/baseline/`
- Regression / fail-before: `.../evidence/regression-testing/`
- Final QA gates: `.../evidence/qa-gates/`
- Other: `.../evidence/other/`

Writing to any `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or other non-canonical path is a policy violation.

## Per-Task Python Toolchain (applies to every code/test task)

Run in order and restart from step 1 on any failure or auto-fix:
1. `poetry run black .`
2. `poetry run ruff check .`
3. `poetry run pyright`
4. `poetry run pytest --cov --cov-branch --cov-report=term-missing`

GUI tests run under `QT_QPA_PLATFORM=offscreen` with the PySide6 CI system libraries.

## File-Cap Watch List (hard 500-line cap, prod AND test)

- `src/gui/widgets/_columns_tab_drag.py` — 498 lines, **at cap**. Item 5 MUST extract a helper module; no net additions in place.
- `src/gui/widgets/schema_builder_dialog.py` — 500 lines, **at cap**. Items 2/3/7 MUST be replacements or extracted helpers, not net additions.

---

## Implementation Plan (Atomic Tasks)

### Phase 0 — Compliance & Baseline Capture

- [x] [P0-T1] Read policy files in required order and record the read evidence
  - Read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`
  - Acceptance: `.../evidence/baseline/phase0-instructions-read.md` exists with `Timestamp:`, `Policy Order:`, and the explicit list of files read.

- [x] [P0-T2] Capture Black baseline
  - Command: `poetry run black --check .`
  - Acceptance: `.../evidence/baseline/baseline-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T3] Capture Ruff baseline
  - Command: `poetry run ruff check .`
  - Acceptance: `.../evidence/baseline/baseline-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T4] Capture Pyright baseline
  - Command: `poetry run pyright`
  - Acceptance: `.../evidence/baseline/baseline-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T5] Capture Pytest + coverage baseline
  - Command: `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `.../evidence/baseline/baseline-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` containing the numeric baseline line-coverage % and branch-coverage % headline plus pass/fail count.

- [x] [P0-T6] Record current line counts of the file-cap watch list as a baseline reference
  - Files: `_columns_tab_drag.py`, `schema_builder_dialog.py`, `_schema_builder_tabs.py`, `schema_builder_presenter.py`, `_columns_tab_presenter.py`, `_derived_formula_dialog.py`, `_dtype_check_widget.py`, `_schema_builder_window_setup.py`, `_schema_builder_state.py`
  - Acceptance: `.../evidence/baseline/baseline-line-counts.md` with `Timestamp:` and a per-file line-count table.

### Phase 1 — Low-Risk Mechanical UI (Window, Identity, Derived `=` separator, Double-click insert)

Covers AC-1, AC-2, AC-3, AC-5. Cohesive change surface: window setup, identity widget, derived display separator, derived dialog. No model/loader changes.

- [x] [P1-T1] Fix the vertical-resize blocker in window flags (AC-1)
  - File: `src/gui/widgets/_schema_builder_window_setup.py` (replace the flag combination per research §1: set `Qt.WindowType.Window` and add `dialog.setMinimumSize(400, 400)` so the window reports a resizable minimum below the 900x700 default).
  - Acceptance: `apply_schema_builder_window_flags` produces a resizable top-level window retaining min/max/close controls and a minimum size below default; no `setFixedSize`/`setMaximumSize` introduced.

- [x] [P1-T2] Update the window-flags test to assert the new flag set and minimum size (AC-1)
  - File: `tests/gui/test_schema_builder_dialog.py` (replace the `WindowMaximizeButtonHint` assertion at the existing window-flag test; assert resizable flags and `minimumSize` below default).
  - Acceptance: test asserts the post-change flag combination and that `minimumSize().height() < 700`; passes under offscreen. Run full per-task toolchain.

- [x] [P1-T3] Replace the Identity description control with a wrapping multi-line widget (AC-2)
  - File: `src/gui/widgets/_schema_builder_tabs.py` (`build_identity_tab`: `QLineEdit` -> `QPlainTextEdit` with word-wrap and `Expanding` vertical size policy; update `IdentityTabControls.description` annotation to `QPlainTextEdit`; keep `name`/`version` in the form layout).
  - Acceptance: Identity tab `description` is a `QPlainTextEdit` that wraps and expands vertically; no signature change to tab dataclass beyond the `description` type.

- [x] [P1-T4] Update Identity accessors to the multi-line API (AC-2)
  - File: `src/gui/widgets/schema_builder_dialog.py` (`set_identity` `.setText` -> `.setPlainText`; `get_identity` `.text()` -> `.toPlainText()`; replacements only, no net new lines — preserve `tuple[str, str, str]` / three-`str` contract).
  - Acceptance: `get_identity`/`set_identity` signatures unchanged; round-trip uses plain-text API. File remains <= 500 lines.

- [x] [P1-T5] Add a unit test for multi-line identity round-trip (AC-2)
  - File: `tests/gui/test_schema_builder_dialog.py` (set then get a description containing embedded newlines; assert the multi-line value survives and the widget wraps).
  - Acceptance: test drives `set_identity`/`get_identity` with multi-line text and asserts exact round-trip. Run full per-task toolchain.

- [x] [P1-T6] Change the Derived render/parse separator from `name|expression` to `name = expression` (AC-3)
  - Files: `src/gui/widgets/schema_builder_dialog.py` (`set_derived`: `f"{name} = {expression}"`; `get_derived`: `line.partition(" = ")` splitting on first occurrence). Replacements only.
  - Acceptance: `set_derived`/`get_derived` produce and parse `name = expression`; no `name|expression` string is produced anywhere.

- [x] [P1-T7] Update the Derived tab label text to describe the `=` format (AC-3)
  - File: `src/gui/widgets/_schema_builder_tabs.py` (label `"One derived column per line: name|expression"` -> `"... name = expression"`).
  - Acceptance: derived tab label text reflects the `=` separator.

- [x] [P1-T8] Update derived-format tests for the `=` separator (AC-3)
  - File: `tests/gui/test_schema_builder_dialog.py` (replace any `name|expression` construction/assertion with `name = expression`; add a negative test asserting `|` is no longer produced).
  - Acceptance: tests assert `=` round-trip and absence of `|` separator. Run full per-task toolchain.

- [x] [P1-T9] Wire double-click column insert in the New-derived dialog (AC-5)
  - File: `src/gui/widgets/_derived_formula_dialog.py` (connect `self._names_list.itemDoubleClicked` to a new `_on_column_double_clicked` slot that inserts the bracketed name `[Name]` at the cursor via `QLineEdit.insert`).
  - Acceptance: double-clicking an available column inserts `[Name]` at the cursor position; file remains <= 500 lines (currently 232).

- [x] [P1-T10] Add a unit test for double-click bracketed insert (AC-5)
  - File: `tests/gui/test_derived_formula_dialog.py` (emit `itemDoubleClicked` for a known column; assert the bracketed name is inserted at the cursor in the expression input).
  - Acceptance: test drives the double-click path and asserts the inserted text and cursor behavior. Run full per-task toolchain.

### Phase 2 — Derived Bracket Format Helper (D-1, display-only, formula grammar unchanged)

Covers AC-4. Isolated to a new display/format helper; `src/schema_formula.py` and `FormulaEvaluator` are NOT modified (D-1).

- [x] [P2-T1] Create the bracket strip/add helper module (AC-4, D-1)
  - File (new): `src/gui/widgets/_schema_builder_derived_format.py` with two pure functions: `strip_brackets(expr: str) -> str` converting `[Name]` -> `col("Name")` (handles names with spaces/special chars via the quoted `col()` form), and `add_brackets(expr: str, known_names: Iterable[str]) -> str` re-wrapping known column references as `[Name]` with comma separators outside the brackets.
  - Acceptance: module exposes both pure functions with full type hints and docstrings; no import of or change to `src/schema_formula.py`.

- [x] [P2-T2] Add unit tests for the bracket helper, including names with spaces (AC-4, D-1)
  - File (new): `tests/gui/test_schema_builder_derived_format.py` covering: bracket -> `col("...")` strip, `col("...")` -> bracket re-add, names containing spaces, comma-separated multi-reference expressions, and an idempotence/round-trip property.
  - Acceptance: tests assert `[col a], [col b]` <-> `col("col a"), col("col b")` round-trip and that stripped output is valid input to the existing `FormulaEvaluator` (asserted by calling `FormulaEvaluator.validate` on stripped output). Run full per-task toolchain.

- [x] [P2-T3] Apply bracket strip-on-store and bracket-on-display in derived accessors (AC-4, D-1)
  - File: `src/gui/widgets/schema_builder_dialog.py` (`get_derived` strips brackets via `strip_brackets` before storing; `set_derived` calls `add_brackets` with the declared column names before display). Replacements / delegation to the new helper only — no net line growth that breaches 500.
  - Acceptance: stored/validated expressions use `col("Name")`; displayed expressions show `[Name]`; `schema_builder_dialog.py` remains <= 500 lines (extract a thin private method to the new helper module if needed to stay under cap).

- [x] [P2-T4] Add a round-trip test proving stored form is bare `col()` and displayed form is bracketed, with grammar unchanged (AC-4, D-1)
  - File: `tests/gui/test_schema_builder_dialog.py` (set a derived expression with brackets, read it back, assert the persisted `DerivedColumnSpec.expression` uses `col("...")`; assert the rendered display uses `[...]`; assert `FormulaEvaluator` grammar is exercised unchanged on the stored form).
  - Acceptance: test asserts display/storage divergence and that no bracket syntax ever reaches `FormulaEvaluator`. Run full per-task toolchain.

### Phase 3 — Columns Tab Row Chooser and Masked Value Display

Covers AC-6. Medium risk; `_columns_tab_drag.py` is at cap — extraction is mandatory.

- [x] [P3-T1] Extract a helper module from `_columns_tab_drag.py` to create headroom (file-cap)
  - Files: new `src/gui/widgets/_columns_tab_row_chooser.py` (or similarly named helper); move a cohesive block out of `_columns_tab_drag.py` so it drops below cap before any additions.
  - Acceptance: `_columns_tab_drag.py` is < 500 lines after extraction; extracted module is < 500 lines; behavior unchanged (existing columns-tab tests still pass).

- [x] [P3-T2] Add the row-number chooser control to the Columns tab (AC-6)
  - Files: `src/gui/widgets/_columns_tab_drag.py` (add a `QSpinBox` chooser at `ColumnsTabWidget` level bounded `0..len(preview_slice.rows)-1`, wired to notify the presenter on change) using the extracted helper from P3-T1.
  - Acceptance: the chooser appears once at tab level with correct bounds; emits the chosen row index to the presenter; file remains <= 500 lines.

- [x] [P3-T3] Extend the dtype widget to show a value string instead of the dtype glyph (AC-6)
  - File: `src/gui/widgets/_dtype_check_widget.py` (add a `set_value_display(value: str)` path so the widget renders the assigned masked cell value to the right of the blue object, switchable with the existing dtype-glyph mode).
  - Acceptance: widget can render either the dtype glyph or a value string; file remains <= 500 lines (currently 95).

- [x] [P3-T4] Render the chosen row's masked assigned value in the presenter (AC-6)
  - File: `src/gui/presenters/_columns_tab_presenter.py` (`_render_assignments_and_dtypes` accepts an optional `row_index: int | None`; when set, push `preview_slice.rows[row_index][header.index(assigned_source)]` to each row's value display; values come only from already-masked `PreviewSlice.rows`).
  - Acceptance: when a row index is set the presenter pushes masked cell values; when `None`, the dtype-glyph path is preserved; no new I/O introduced.

- [x] [P3-T5] Add the protocol method for the row chooser if the presenter drives it (AC-6)
  - File: `src/gui/_columns_tab_protocol.py` (add `set_row_chooser_value`/value-display method to `ColumnsTabViewProtocol` only if P3-T2/P3-T4 require it).
  - Acceptance: protocol matches the view/presenter contract; Pyright clean.

- [x] [P3-T6] Add unit tests for row chooser and masked value display using a masked `PreviewSlice` fixture (AC-6)
  - File: `tests/gui/test_columns_tab.py` (or the existing columns-tab test module) with a `PreviewSlice` fixture of >= 2 masked rows; assert changing the chooser updates each row's displayed value to the chosen row's masked value, and that only masked values appear (no real-workbook values in the committed fixture).
  - Acceptance: tests cover row 0 and a non-zero row, an unassigned row, and assert masking is preserved. Run full per-task toolchain.

### Phase 4 — Key Tab Simplification (D-2, Option C; model + loader unchanged)

Covers AC-7. Replaces the drag-and-drop / Generic-Text-token UI with a multi-select of declared columns producing ordered `column-ref` `KeySpec` parts.

- [x] [P4-T1] Replace the Key tab UI with a multi-select of declared canonical columns (AC-7, D-2)
  - File: `src/gui/widgets/_schema_builder_tabs.py` (build a multi-select list/checkbox control of declared canonical columns; retain the SKU-coercion checkbox; remove the drag pool / `GenericTextToken` UI from the key tab build path).
  - Acceptance: Key tab presents a multi-select of declared columns plus the SKU-coercion checkbox; no drag-and-drop key UI remains.

- [x] [P4-T2] Map the multi-select to ordered `column-ref` KeySpec parts in the key get/set accessors (AC-7, D-2)
  - File: `src/gui/widgets/schema_builder_dialog.py` (key get/set: selected columns become ordered `column-ref` parts joined by a default literal-text separator; `KeySpec`/`KeyPart` model and the loader's `resolve_key` are unchanged). Replacements only.
  - Acceptance: selecting columns composes an ordered `KeySpec`; round-trips through `KeySpec` with no model/serialization/loader change; file remains <= 500 lines.

- [x] [P4-T3] Track key multi-select state in the schema-builder state (AC-7, D-2)
  - File: `src/gui/presenters/_schema_builder_state.py` (represent the ordered selected key columns; presenter sync in `src/gui/presenters/schema_builder_presenter.py` as needed).
  - Acceptance: state holds the ordered key-column selection and round-trips to `KeySpec`; both files remain <= 500 lines.

- [x] [P4-T4] Add unit tests for the Key multi-select round-trip through `KeySpec` (AC-7, D-2)
  - File: `tests/gui/test_schema_builder_dialog.py` (select an ordered subset of declared columns; assert the assembled `KeySpec` parts are ordered `column-ref` entries matching the selection joined by the default separator; assert SKU-coercion checkbox is honored; assert no model/loader change is required by loading the result through the existing key resolution).
  - Acceptance: test asserts ordered `column-ref` parts and unchanged `KeySpec` semantics. Run full per-task toolchain.

### Phase 5 — Dedup `auto` Mode (D-3, Option B; LE explicit path preserved)

Covers AC-8. Highest model/loader risk; isolated with explicit LE-regression evidence.

- [x] [P5-T1] Add the `auto` mode to the dedup policy model and relax the invariant for `auto` only (AC-8, D-3)
  - Files: `src/schema_model.py` and/or `src/_schema_model_specs.py` (`DedupPolicy`): add `auto` to the allowed modes; relax the discriminator-required invariant in `__post_init__` ONLY when `mode == "auto"`; `none`/`collapse`/`aggregate`/`select_from` invariants stay byte-for-byte unchanged.
  - Acceptance: `DedupPolicy(mode="auto")` constructs without a discriminator; `aggregate`/`collapse` still require their discriminator exactly as before; file(s) remain <= 500 lines.

- [x] [P5-T2] Add the `auto` groupby code path in the loader/dedup helper (AC-8, D-3)
  - Files: `src/_schema_loader_helpers.py` (and `src/etl_key.py` only if the key path is implicated): when `mode == "auto"`, group by all `dimension`-role columns and sum all `measure`-role columns with no explicit discriminator; the existing `collapse`/`aggregate`/`select_from` branches are untouched.
  - Acceptance: `auto` mode produces a `dimension`-grouped, `measure`-summed result; existing branches unchanged; file remains <= 500 lines.

- [x] [P5-T3] Add a regression test asserting the existing LE explicit dedup behavior is unchanged (AC-8, D-3)
  - File: `tests/test_schema_loader_dedup.py` (or the existing dedup loader test module): exercise the LE `select_from`/explicit-discriminator path against a masked fixture and assert the existing aggregated output is byte-for-byte unchanged from baseline behavior.
  - Acceptance: LE explicit-path test passes against current behavior; documents the preserved invariant. Run full per-task toolchain.

- [x] [P5-T4] Add unit + loader tests for `auto` mode groupby/sum with no discriminator (AC-8, D-3)
  - File: `tests/test_schema_loader_dedup.py` (construct an `auto`-mode schema with `dimension` and `measure` roles and no discriminator; assert groupby is the `dimension` set and `measure` columns are summed; assert `DedupPolicy(mode="auto")` requires no discriminator).
  - Acceptance: tests cover the positive `auto` path, the no-discriminator construction, and an empty/edge groupby case. Run full per-task toolchain.

- [x] [P5-T5] Wire the `auto` mode into the Dedup tab control and state (AC-8, D-3)
  - Files: `src/gui/widgets/_schema_builder_tabs.py` (mode control offers `auto`, `aggregate`, `collapse`, `none`; discriminator control not required when `auto` is selected), `src/gui/presenters/_schema_builder_state.py` and `src/gui/presenters/schema_builder_presenter.py` (dedup auto-mode state + sync).
  - Acceptance: selecting `auto` in the tab assembles a no-discriminator `DedupPolicy(mode="auto")`; other modes still require their discriminator; files remain <= 500 lines.

- [x] [P5-T6] Add a GUI test asserting `auto` mode assembles without a discriminator from the dialog (AC-8, D-3)
  - File: `tests/gui/test_schema_builder_dialog.py` (select `auto` in the dedup tab; assert `assemble_schema` succeeds with no discriminator and yields `DedupPolicy(mode="auto")`; select `aggregate` with no discriminator and assert the existing `SchemaValidationError` is still raised).
  - Acceptance: test proves the relaxed invariant applies only to `auto`. Run full per-task toolchain.

### Phase 6 — Preview Tab Rendering and Production Wiring

Covers AC-9, AC-10. Item 7: `update_preview` currently has NO production call site (verified: single definition at `schema_builder_presenter.py:406`, no caller in `src/`). Must wire the trigger and prove the wired path with an integration test, not only a unit test of the method (memory: audit-verify-production-call-site; integration-test standard).

- [x] [P6-T1] Replace the preview `QLabel` with a tabular widget in the preview tab controls (AC-9)
  - File: `src/gui/widgets/_schema_builder_tabs.py` (`PreviewTabControls`: replace `rows_label: QLabel` with a `QTableWidget`/`QTableView` following the `src/gui/widgets/preview_widget.py` pattern; keep a separate error/message area).
  - Acceptance: preview tab hosts a tabular widget with column headers; file remains <= 500 lines.

- [x] [P6-T2] Add a slice->rows helper to convert masked `PreviewSlice` rows to row mappings (AC-9)
  - File: `src/gui/presenters/_schema_builder_state.py` (e.g., `preview_rows_from_slice` converting `PreviewSlice.rows` + `PreviewSlice.header` into `list[Mapping[str, object]]`; returns empty/None signal when `preview_slice is None`).
  - Acceptance: helper maps masked rows by header keys; handles `None`/empty slice; file remains <= 500 lines.

- [x] [P6-T3] Populate the preview table from `show_preview` and show a specific message on failure (AC-9, AC-10)
  - File: `src/gui/widgets/schema_builder_dialog.py` (`show_preview` populates the table widget instead of the label; the missing-input / assembly-failure message from `SchemaValidationError`/loader errors is shown in the message area). Replacements only; extract a thin method to `_schema_open_helpers.py` if needed to stay under cap.
  - Acceptance: success path fills the table; failure path shows the specific `SchemaValidationError`/loader message (not blank); `schema_builder_dialog.py` remains <= 500 lines.

- [x] [P6-T4] Wire the tab-change trigger to call `update_preview` at dialog open time (AC-9)
  - Files: `src/gui/_schema_wiring.py` or `src/gui/widgets/_schema_open_helpers.py` (connect `QTabWidget.currentChanged` so navigating to the Preview tab calls `presenter.update_preview` with slice-derived rows; if `preview_slice is None`, display "No source data available to preview").
  - Acceptance: a production (non-test) call site for `update_preview` exists, reachable from the opened dialog; grep for `update_preview` in `src/` returns a non-test caller.

- [x] [P6-T5] Add an integration test proving the wired production path renders the table (AC-9)
  - File: `tests/gui/test_schema_builder_dialog.py` (instantiate the production `SchemaBuilderDialog` reached by the user with a masked `PreviewSlice` fixture; drive the real tab-change to the Preview tab; assert the `QTableWidget` is populated from the masked slice — do NOT call `update_preview` directly, and do NOT use a synthetic-only alias path).
  - Acceptance: test drives the production dialog and tab-change seam, asserts table population from masked values, and fails if the code falls back to the old label path. Paired with the P6-T4 production grep. Run full per-task toolchain.

- [x] [P6-T6] Add tests for the missing-input / assembly-failure message path (AC-10)
  - File: `tests/gui/test_schema_builder_dialog.py` (drive the wired path with a schema missing a required input — e.g., empty name, undeclared key reference — and assert the specific `SchemaValidationError` message text is shown; drive a `None` preview slice and assert the "No source data available to preview" message).
  - Acceptance: tests assert the specific missing-input messages render rather than nothing. Run full per-task toolchain.

### Phase 7 — Final QA Loop, Coverage Delta, and File-Cap Scan

Covers AC-11. Full toolchain in order; restart from step 1 on any failure/auto-fix. One artifact per command step.

- [x] [P7-T1] Scan all changed production and test files for the 500-line cap (AC-11)
  - Acceptance: `.../evidence/qa-gates/file-size-scan.md` with `Timestamp:` and a per-changed-file line count; every changed prod AND test file is <= 500 lines; explicitly confirms `_columns_tab_drag.py`, `schema_builder_dialog.py`, and any newly extracted modules are under cap. Any file > 500 lines blocks completion.

- [x] [P7-T2] Run final Black and record evidence (AC-11)
  - Command: `poetry run black .`
  - Acceptance: `.../evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (no files reformatted on the clean pass).

- [x] [P7-T3] Run final Ruff and record evidence (AC-11)
  - Command: `poetry run ruff check .`
  - Acceptance: `.../evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (0 errors; any suppression pre-authorized per `python-suppressions.md`).

- [x] [P7-T4] Run final Pyright and record evidence (AC-11)
  - Command: `poetry run pyright`
  - Acceptance: `.../evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (0 errors).

- [x] [P7-T5] Run final Pytest with coverage and record evidence (AC-11)
  - Command: `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `.../evidence/qa-gates/final-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` containing post-change numeric line-coverage % and branch-coverage % plus pass count.

- [x] [P7-T6] Verify coverage thresholds and no-regression on changed lines (AC-11)
  - Acceptance: `.../evidence/qa-gates/coverage-delta.md` reporting baseline coverage (from P0-T5), post-change coverage (from P7-T5), and changed/new-code coverage; confirms line >= 85%, branch >= 75%, and no regression on changed lines. If any threshold is unmet the outcome is remediation-required, not PASS.

- [x] [P7-T7] Verify AC-1..AC-11 are each mapped to a passing test and record the mapping (AC-11)
  - Acceptance: `.../evidence/qa-gates/ac-traceability.md` mapping each AC to the test(s) that prove it, including the AC-9 production-wiring integration test and the AC-8 LE-regression test.

## Test Plan

- Unit: window flags + minimum size; identity multi-line round-trip; derived `=` parse/render; bracket strip/add helper (incl. names with spaces); double-click insert; columns row chooser + masked value display; key multi-select -> `KeySpec`; dedup `auto` model invariant; loader `auto` groupby/sum; preview slice->rows helper; preview missing-input messages.
- Integration: opened production `SchemaBuilderDialog` with a masked `PreviewSlice` fixture, real tab-change trigger renders the preview `QTableWidget` (AC-9 wired path); LE explicit dedup path unchanged (AC-8 regression).
- Manual/CLI: not applicable (GUI feature); all GUI tests run under `QT_QPA_PLATFORM=offscreen`.
- Coverage evidence: baseline at `.../evidence/baseline/baseline-pytest.md`; post-change at `.../evidence/qa-gates/final-pytest.md`; delta at `.../evidence/qa-gates/coverage-delta.md`.

## Open Questions / Notes

- D-1/D-2/D-3 are resolved in the spec; no design questions remain. `src/schema_formula.py` is NOT touched (D-1). `KeySpec`/`KeyPart` model and key loader are NOT changed (D-2). `DedupPolicy` invariant is relaxed only for `auto` (D-3); the LE explicit `select_from`/discriminator path is preserved and regression-tested.
- File-cap risk concentrated in `_columns_tab_drag.py` (498) and `schema_builder_dialog.py` (500); Phase 3 mandates extraction before additions, and dialog edits across Phases 1/2/4/6 must be replacements or helper extractions.
- AC-9 wiring is the highest audit risk: `update_preview` has no production caller today; P6-T4 adds the call site and P6-T5 proves it through the opened dialog, not an isolated method unit test.
