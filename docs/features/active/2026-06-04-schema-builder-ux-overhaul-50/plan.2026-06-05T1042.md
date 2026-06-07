# schema-builder-ux-overhaul — Plan

- **Issue:** #50
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-05T13-58
- **Status:** Complete — all phases (0–15) done; 922 tests pass; toolchain green
- **Version:** 1.0
- **Work Mode:** full-feature
- **Tier:** T3 (adapters & UI), Python (PySide6)

## Required References

- Cross-language code change policy: `.claude/rules/general-code-change.md`
- Cross-language unit test policy: `.claude/rules/general-unit-test.md`
- Python toolchain & standards: `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
- Quality tiers / coverage gates: `.claude/rules/quality-tiers.md` (line >= 85%, branch >= 75%, no regression on changed lines)
- Commenting/docstrings: `.claude/rules/self-explanatory-code-commenting.md`
- CI workflow authoring: `.claude/rules/ci-workflows.md`; benchmark provenance: `.claude/rules/benchmark-baselines.md`
- Authoritative spec: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` (v1.0, Resolved Design Decisions are binding)
- Research facts: `artifacts/research/schema-builder-ux-overhaul-50.md`

**All work must comply with these policies; do not duplicate their content here.**

## Evidence Location Invariant

All evidence artifacts produced by this plan MUST be written under
`docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/`
using canonical sub-paths (`baseline/`, `qa-gates/`, `regression-testing/`,
`other/`, `issue-updates/`). Writing to `artifacts/baselines/`, `artifacts/qa/`,
`artifacts/coverage/`, or any other non-canonical location is a policy violation.
Timestamps use ISO-8601 `yyyy-MM-ddTHH-mm`.

Shorthand used below: `<FEATURE>` = `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50`.

---

## Acceptance-Criterion → Task Map

| Spec AC | Covered by |
|---|---|
| Import button disabled until schema selected; re-disables on placeholder | P6-T1..T5 |
| Activating source tab auto-selects best match; placeholder when none | P6-T6..T10 |
| Edit-schema action loads existing schema and re-saves | P5-T1..T4, P8-T6 |
| New-from-template seeds from closest existing | P5-T5..T8, P8-T7 |
| Builder accepts required/optional specs, default key pattern, masked preview slice | P4-T1..T7 |
| Columns tab renders draggable source-column buttons | P7-T1..T4 |
| Required/optional rows pre-populate via fuzzy match; matched col consumed | P7-T5..T9 |
| Matched source→canonical mapping persists as aliases; reload re-matches | P3-T1..T4, P7-T6 |
| Activation-time matching runs first against persisted alias columns; partial → new-from-template | P6-T8..T10, P5-T5..T8 |
| Matched columns show green check / red X with failing example | P7-T10..T13 |
| Key tab drag-drop parts + repeatable Generic Text token; default pattern parsed | P2-T1..T6, P9-T1..T8 |
| Dedup defaults to aggregate with Key discriminator; dropdown-only | P1-T1..T6, P10-T1..T5 |
| Derived precedes Columns; dialog creates derived rows; derived appear on Columns | P8-T1..T8, P11-T1 |
| `expected_dtype` added; version bumped; forward migration; defaults migrated to aggregate | P1-T7..T9, P3-T1..T6, P12-T1..T4 |
| No real workbook values or proprietary column names committed (masking scan) | P0-T7, P7-T11..T13, P13-T1..T3 |

---

### Phase 0 — Baseline Capture and Policy Read

- [x] [P0-T1] Read repo policies in required order (`.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`) and record a Phase 0 evidence artifact.
  - Acceptance: `<FEATURE>/evidence/baseline/phase0-instructions-read.md` exists with `Timestamp:`, `Policy Order:`, and the explicit list of files read.
- [x] [P0-T2] Capture baseline Black formatting state by running `poetry run black --check .`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T3] Capture baseline Ruff lint state by running `poetry run ruff check .`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T4] Capture baseline Pyright type-check state by running `poetry run pyright`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count).
- [x] [P0-T5] Capture baseline test + coverage state by running `poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric baseline line% and branch% headline values and pass/fail counts.
- [x] [P0-T6] Record current line counts of cap-sensitive files (`src/schema_model.py`, `src/gui/app.py`, `src/gui/widgets/source_input_widget.py`) to verify the decomposition preconditions.
  - Acceptance: `<FEATURE>/evidence/baseline/baseline-file-sizes.md` lists each path with its current line count and the 500-line cap.
- [x] [P0-T7] Create the masking-scan helper script that scans changed/added files for forbidden patterns (real workbook numeric values and known proprietary source column names) and confirm it runs clean on the current tree.
  - Acceptance: a committed scan script (for example `scripts/checks/scan_masked_fixtures.py`, <= 500 lines) exists; `<FEATURE>/evidence/baseline/baseline-masking-scan.md` records `Command:`, `EXIT_CODE: 0`, `Output Summary:` for a clean baseline run.

---

### Phase 1 — Schema Model Split and New Model Fields

- [x] [P1-T1] Extract the spec dataclasses (`ColumnSpec`, `KeySpec`, `DedupPolicy`, `DerivedColumnSpec`, `FillRule`) from `src/schema_model.py` into new module `src/_schema_model_specs.py` and re-export them from `src/schema_model.py`.
  - Acceptance: `src/_schema_model_specs.py` <= 500 lines; `src/schema_model.py` <= 500 lines; all existing imports of these names from `src.schema_model` still resolve.
- [x] [P1-T2] Run `poetry run pytest tests/test_schema_model.py tests/test_schema_serialization.py` and confirm the split is behavior-preserving (no model change yet).
  - Acceptance: both files pass; no test edits required for the pure move.
- [x] [P1-T3] Add `expected_dtype: str | None = None` to `ColumnSpec` in `src/_schema_model_specs.py` with vocabulary validation `{string, integer, float, date, bool}` enforced in `__post_init__`.
  - Acceptance: constructing `ColumnSpec(..., expected_dtype="float")` succeeds; an invalid value raises `SchemaValidationError`.
- [x] [P1-T4] Define a `DTYPE_VOCAB` constant and a `numeric=True → "float"` derivation helper so legacy `numeric` columns map deterministically to an expected dtype.
  - Acceptance: a unit test asserts `numeric=True` with `expected_dtype=None` resolves to `"float"`.
- [x] [P1-T5] Add unit tests for `expected_dtype` to `tests/test_schema_model.py`: valid vocabulary, invalid value rejection, and the `numeric→float` derivation.
  - Acceptance: new tests pass; cover positive, negative, and the derivation edge case.
- [x] [P1-T6] Introduce the structured key-part model in `src/_schema_model_specs.py`: a `KeyPart` representation distinguishing `column-ref` parts from `literal-text` ("Generic Text") parts, ordered, with non-empty validation per Decision 2.
  - Acceptance: a column-ref part requires a non-empty canonical name; a literal-text part carries an arbitrary string value; ordering is preserved.
- [x] [P1-T7] Change `KeySpec` to hold an ordered tuple of `KeyPart` (replacing the flat `columns: tuple[str, ...]`) per Decision 2 (no string overloading), retaining `sku_coercion`.
  - Acceptance: `KeySpec` exposes ordered parts; constructing with a mix of column-ref and literal parts validates; an all-literal key with no column-ref raises `SchemaValidationError`.
- [x] [P1-T8] Add `"aggregate"` to `DEDUP_MODES` in `src/schema_model.py` per Decision 1 (no removal of existing modes).
  - Acceptance: `DedupPolicy(mode="aggregate", ...)` validates; `DEDUP_MODES == {"none", "collapse", "aggregate"}`.
- [x] [P1-T9] Define a module-level current-format version constant (for example `SCHEMA_FORMAT_VERSION`) in `src/schema_model.py` set to the new bumped version string (`"2.0"`), and document it in the `SchemaDefinition` docstring as the current write format. (`SchemaDefinition.version` remains a required, per-instance/per-JSON field with no dataclass default.)
  - Acceptance: `SCHEMA_FORMAT_VERSION` exists with the bumped value (`"2.0"`); the `SchemaDefinition` docstring references it as the current format version; `tests/test_schema_model.py` asserts the constant's value. Do not assert a dataclass default on `SchemaDefinition.version` (the field has none).
- [x] [P1-T10] Add unit tests to `tests/test_schema_model.py` for the structured `KeySpec` parts and the `aggregate` dedup mode (positive, negative, ordering).
  - Acceptance: new tests pass and assert ordering preservation and rejection of an all-literal key.
- [x] [P1-T11] Run `poetry run pytest tests/test_schema_model.py` and confirm all model tests pass.
  - Acceptance: model test module exits 0.

---

### Phase 2 — Serialization and Key-Part Round-Trip

- [x] [P2-T1] Update `_column_to_object`/`_object_to_*` in `src/schema_serialization.py` to serialize and parse `expected_dtype` on `ColumnSpec`.
  - Acceptance: round-trip of a `ColumnSpec` with `expected_dtype="date"` preserves the value.
- [x] [P2-T2] Update `_key_to_object` and the key parser in `src/schema_serialization.py` to serialize and parse the structured `KeyPart` list (typed entries for column-ref vs literal-text).
  - Acceptance: round-trip of a `KeySpec` with mixed parts preserves order and part types.
- [x] [P2-T3] Update the dedup serialization path to accept and emit `"aggregate"` mode.
  - Acceptance: round-trip of a `DedupPolicy(mode="aggregate")` preserves the mode.
- [x] [P2-T4] Update `schema_to_json` version emission so the serialized format reflects `SCHEMA_FORMAT_VERSION` (the bumped current write version).
  - Acceptance: serialized JSON written through the current path contains `SCHEMA_FORMAT_VERSION`.
- [x] [P2-T5] Add serialization round-trip tests to `tests/test_schema_serialization.py` covering `expected_dtype`, structured key parts (column-ref + repeated literal-text), and `aggregate` dedup mode.
  - Acceptance: new round-trip tests pass; assert order and types of key parts survive serialization.
- [x] [P2-T6] Run `poetry run pytest tests/test_schema_serialization.py` and confirm all serialization tests pass.
  - Acceptance: serialization test module exits 0.

---

### Phase 3 — Forward Migration and Alias Persistence

- [x] [P3-T1] Implement a forward-only migration in `schema_from_json` (`src/schema_serialization.py`) that detects pre-bump version JSON and upgrades it: flat `key.columns` → structured column-ref `KeyPart` list per Decision 3.
  - Acceptance: parsing a pre-bump JSON with `"key": {"columns": [...]}` produces a `KeySpec` of column-ref parts in the same order; pre-bump detection is defined by comparing the parsed version against `SCHEMA_FORMAT_VERSION` (any value not equal to the current constant, or a JSON shape using flat `key.columns`, is treated as pre-bump).
- [x] [P3-T2] Extend the migration to backfill `expected_dtype` from legacy `numeric` (numeric→float, otherwise None) during parse of pre-bump JSON.
  - Acceptance: a legacy column with `numeric:true` parses with `expected_dtype="float"`.
- [x] [P3-T3] Ensure the migration sets the bumped version on the resulting `SchemaDefinition` so a re-serialize emits the new format (forward-only; no dual representation retained).
  - Acceptance: the migration sets `SchemaDefinition.version` to `SCHEMA_FORMAT_VERSION`; parse-then-serialize of legacy JSON yields current-format JSON carrying `SCHEMA_FORMAT_VERSION`.
- [x] [P3-T4] Confirm `ColumnSpec.aliases` is the persisted store for matched source→canonical mappings (no new field); document that activation-time matching consults alias columns first per Decision 6.
  - Acceptance: a docstring/comment in `src/_schema_model_specs.py` states aliases hold persisted source-column matches; a unit test asserts aliases round-trip through serialization unchanged.
- [x] [P3-T5] Add migration unit tests to `tests/test_schema_serialization.py`: legacy-key migration, numeric→expected_dtype backfill, version-bump on re-serialize, and an idempotency test (current-format JSON parses unchanged).
  - Acceptance: new migration tests pass including the idempotency case.
- [x] [P3-T6] Run `poetry run pytest tests/test_schema_serialization.py tests/test_schema_model.py` and confirm model + serialization + migration pass together.
  - Acceptance: both modules exit 0.

---

### Phase 4 — Caller Contract (Specs, Default Key Pattern, Masked Preview Slice)

- [x] [P4-T1] Extend `SchemaBuilderState` (`src/gui/presenters/_schema_builder_state.py`) with fields for the source-column pool, per-row consumed-column tracking, structured key-part state, and a masked preview slice reference.
  - Acceptance: new fields default to empty/None; `_schema_builder_state.py` <= 500 lines; existing `known_column_names(state)` still resolves declared + derived names.
- [x] [P4-T2] Add required/optional `ColumnSpec` sequence parameters, an optional `default_key_pattern`, and a masked preview-slice parameter to `open_schema_builder(...)` in `src/gui/_schema_wiring.py` with defaults that preserve the blank menu-action path (Decision 7).
  - Acceptance: calling `open_schema_builder` without the new args opens a blank builder (menu path); calling with them seeds the presenter state.
- [x] [P4-T3] Thread the new parameters through `wire_build_schema_buttons(...)` so each per-tab button supplies required/optional specs, default key pattern, and masked preview slice for its active source per Decision 7.
  - Acceptance: each of the three source widgets' `build_schema_requested` handlers passes its source-specific specs.
- [x] [P4-T4] If `src/gui/_schema_wiring.py` approaches the 500-line cap after threading, extract the per-tab spec assembly into a helper module (for example `src/gui/_schema_build_specs.py`).
  - Acceptance: `_schema_wiring.py` <= 500 lines and any new helper <= 500 lines; behavior unchanged.
- [x] [P4-T5] Implement the presenter seeding path: when caller specs are supplied, populate `SchemaBuilderState` required/optional rows and parse the `default_key_pattern` into structured `KeyPart` state.
  - Acceptance: a presenter test with caller specs shows required/optional rows pre-listed and the default key parsed into ordered parts.
- [x] [P4-T6] Define the masked-preview-slice contract type (header row + up to ~200 masked rows) and assert in the presenter that no I/O is performed inside the builder (Decision 5).
  - Acceptance: a presenter test passes a fixture preview slice and verifies the presenter reads it without invoking any reader/file API.
- [x] [P4-T7] Update `tests/gui/test_schema_builder_presenter.py` and `tests/gui/test_app_wiring_schema.py` for the new caller-contract parameters (specs supplied path and blank menu path).
  - Acceptance: both updated test modules pass and cover both paths.

---

### Phase 5 — Edit-Existing and New-From-Template Presenter Flows

- [x] [P5-T1] Verify `SchemaBuilderPresenter.load_existing(name)` populates the new state fields (structured key parts, expected_dtype rows, aggregate dedup) after the model changes.
  - Acceptance: a presenter test loads a schema containing structured key parts and aggregate dedup and renders them into state.
- [x] [P5-T2] Update `_render_state()` (or its view-protocol setters) so loaded structured key parts and per-row dtype/expected-type are pushed to the view.
  - Acceptance: the fake view receives ordered key parts and expected-dtype per row on load.
- [x] [P5-T3] Add an "Edit schema" entry that resolves the selected schema name to `load_existing` and re-save through the existing `save_schema` path.
  - Acceptance: a presenter test performs load → modify → save and asserts the saved schema reflects the modification (round-trip).
- [x] [P5-T4] Add edit-load tests to `tests/gui/test_schema_builder_presenter.py` covering load → edit → save with structured key parts and aggregate mode.
  - Acceptance: new tests pass.
- [x] [P5-T5] Implement a "New from template" seeding method on the presenter that, given a closest-existing schema, copies its specs/aliases/key/dedup into fresh state under a new (blank) name per Decision 6.
  - Acceptance: a presenter test seeds from a template schema; the new state mirrors the template but with a cleared name awaiting save-as.
- [x] [P5-T6] Implement the closest-existing selection by reusing `find_best_match` / `_closest_candidates` against persisted alias columns to choose the template when a partial match is detected.
  - Acceptance: a unit test with a partially-matching registry selects the highest-scoring existing schema as the template.
- [x] [P5-T7] Ensure save-as for a new-from-template schema writes a new `<name>.schema.json` via `save_schema` without overwriting the template.
  - Acceptance: a presenter test asserts the template file name and the new file name differ and both are valid.
- [x] [P5-T8] Add new-from-template tests to `tests/gui/test_schema_builder_presenter.py` (seed, adjust, save-as, no-overwrite).
  - Acceptance: new tests pass.

---

### Phase 6 — Import Gating and on_schema_discovery Wiring

- [x] [P6-T1] Extract schema-combo/import-button wiring from `src/gui/widgets/source_input_widget.py` into a helper (for example `src/gui/widgets/_source_input_button_wiring.py`) so the widget stays under the 500-line cap before adding gating logic.
  - Acceptance: `source_input_widget.py` <= 500 lines; new helper <= 500 lines; existing `tests/gui` widget tests still pass.
- [x] [P6-T2] Set the Import button to start disabled for each source tab per Decision 8.
  - Acceptance: a Qt offscreen test asserts the Import button `isEnabled()` is False on construction before any schema selection.
- [x] [P6-T3] Wire `SourceInputWidget.schema_selected` so selecting a non-placeholder schema calls `set_import_button_enabled(key, True)`.
  - Acceptance: a presenter/wiring test asserts selecting a schema enables Import for that key.
- [x] [P6-T4] Re-disable the Import button when the selection returns to the `<Choose Schema>` placeholder.
  - Acceptance: a test asserts returning to the placeholder sets Import disabled.
- [x] [P6-T5] Update `tests/gui/test_app_wiring_schema.py` (or a focused wiring test) to assert the `schema_selected` → import-gate connection exists in the composition root.
  - Acceptance: the wiring test verifies the connection is established in `app.py`/wiring.
- [x] [P6-T6] Decompose `src/gui/app.py` (currently at the 500-line cap) by extracting the schema-discovery/import-gating wiring into a new module (for example `src/gui/_schema_discovery_wiring.py`) before adding new wiring.
  - Acceptance: `src/gui/app.py` <= 500 lines; new wiring module <= 500 lines; existing app-wiring tests pass.
- [x] [P6-T7] Wire `SourceSelectionPresenter.on_schema_discovery(path, sheet)` to `_tab_combo.currentTextChanged` per Decision 9 (completing #48 follow-up F2), retaining existing empty-header and reader-error guards.
  - Acceptance: a test asserts `currentTextChanged` triggers `on_schema_discovery`; empty-header and reader-error guard tests still pass.
- [x] [P6-T8] Implement activation-time matching that runs first against persisted alias columns of existing schemas (Decision 6), then falls back to header-based `find_best_match`.
  - Acceptance: a presenter test where a schema's alias columns match the active sheet selects that schema before generic header matching.
- [x] [P6-T9] On a no-match, set the schema selection to the `<Choose Schema>` placeholder (which keeps Import disabled).
  - Acceptance: a test asserts no-match leaves the placeholder selected and Import disabled.
- [x] [P6-T10] On a partial match (many alias columns match but not all), surface the new-from-template path entry point.
  - Acceptance: a test asserts a partial match exposes new-from-template seeding for the closest existing schema.
- [x] [P6-T11] Update `tests/gui/test_source_selection_presenter.py` and `tests/gui/integration/test_behavioral_schema_import.py` for the wired discovery, alias-first matching, no-match placeholder, and partial-match paths.
  - Acceptance: both modules pass with the new behavior covered.

---

### Phase 7 — Columns Tab Redesign (Drag-Drop + Fuzzy Pre-Population + Dtype Check)

- [x] [P7-T1] Define a Columns-tab view-protocol seam exposing `assign_column(source_column, target_canonical)` and pool/row setters so presenter tests never simulate drag events (research G).
  - Acceptance: the protocol is declared with assignment + setter methods; a fake view implements it for presenter tests.
- [x] [P7-T2] Create `src/gui/widgets/_columns_tab_drag.py` implementing the draggable source-column token pool and required/optional row widgets, calling `assign_column(...)` on drop.
  - Acceptance: file <= 500 lines; a Qt offscreen test asserts a drop gesture invokes `assign_column` exactly once with the dropped source/target.
- [x] [P7-T3] Render draggable buttons for each source-sheet column from the masked preview slice header row.
  - Acceptance: a Qt offscreen test asserts one draggable token per header column.
- [x] [P7-T4] Render required/optional rows showing canonical name, description, and expected data type from caller specs.
  - Acceptance: a Qt offscreen test asserts each row displays name, description, and expected dtype.
- [x] [P7-T5] Create `src/gui/presenters/_columns_tab_presenter.py` implementing fuzzy pre-population using `_closest_candidates` / `normalize_name` against the source-column pool.
  - Acceptance: file <= 500 lines; a presenter test pre-populates rows with the best fuzzy source match per canonical column.
- [x] [P7-T6] Persist each matched source column onto the corresponding `ColumnSpec.aliases` so the mapping survives save/reload (Decision 6).
  - Acceptance: a presenter test asserts a matched source column is added to that column's aliases in saved state.
- [x] [P7-T7] Implement consumed-column tracking: a matched source column is removed from the pool and cannot match a second row.
  - Acceptance: a presenter test asserts a consumed source column is absent from the pool and unavailable to other rows.
- [x] [P7-T8] Implement manual re-assignment via the `assign_column` seam, returning a previously-consumed column to the pool when a row is cleared/reassigned.
  - Acceptance: a presenter test asserts clearing a row returns its source column to the pool.
- [x] [P7-T9] Add presenter tests to `tests/gui/test_columns_tab_presenter.py` for pre-population, alias persistence, consumed exclusion, re-match guard, and manual reassignment.
  - Acceptance: new test module passes covering positive, negative, and edge cases.
- [x] [P7-T10] Create pure dtype-coercion logic (for example `src/dtype_check.py`) that, given sampled values and an expected dtype, returns coercible/not-coercible plus the first failing example value; reuse `pd.to_numeric` for numeric/integer/float and explicit parsing for date/bool/string.
  - Acceptance: file <= 500 lines; pure-function unit tests cover identical, coercible, and non-coercible (with a returned failing example) for each dtype in the vocabulary.
- [x] [P7-T11] Create `src/gui/widgets/_dtype_check_widget.py` as a passive indicator (green check / red X + failing example) driven by presenter-supplied state, with all displayed example values masked.
  - Acceptance: file <= 500 lines; a Qt offscreen test asserts the widget shows green for coercible state and red + masked example for non-coercible state.
- [x] [P7-T12] Orchestrate the dtype check in `_columns_tab_presenter.py`: run the pure check on the masked preview slice for each matched column and push pass/fail + masked example to the widget.
  - Acceptance: a presenter test asserts a non-coercible matched column yields a red state with a masked failing example.
- [x] [P7-T13] Add `tests/test_dtype_check.py` for the pure coercion logic and confirm every fixture value used is synthetic/masked (no real workbook values).
  - Acceptance: new test module passes; fixtures contain only synthetic values; masking-scan helper (P0-T7) reports clean for the new test file.

---

### Phase 8 — Derived Tab Dialog and Reorder

- [x] [P8-T1] Create `src/gui/widgets/_derived_formula_dialog.py` as a sub-dialog for authoring one derived column: available-name list (declared + prior-derived), expression input, live validation.
  - Acceptance: file <= 500 lines; a Qt offscreen test asserts the dialog lists available names and accepts an expression.
- [x] [P8-T2] Populate the dialog's available names from `known_column_names(state)` (declared columns + derived rows above the current one).
  - Acceptance: a test asserts the dialog offers a prior-derived column name to a later derived row.
- [x] [P8-T3] Wire live validation to `FormulaEvaluator.validate(expression, known_columns)` and surface `FormulaError` inline (reuse existing engine; no new engine).
  - Acceptance: a test asserts an invalid expression surfaces a `FormulaError` message and a valid one clears it.
- [x] [P8-T4] Add a Derived-tab button that opens the dialog and, on accept, appends the new `DerivedColumnSpec` to state in order.
  - Acceptance: a presenter test asserts accepting the dialog appends a derived row to state.
- [x] [P8-T5] Ensure newly-added derived columns become selectable on the Columns tab (feed derived names into the columns-tab available set).
  - Acceptance: a presenter test asserts a derived column appears as a selectable column on the Columns tab.
- [x] [P8-T6] Update `SchemaBuilderDialog.__init__` tab construction to the order `Identity → Derived → Columns → Key → Dedup → Preview` (Decision 10), importing the new drag-drop/dialog tab modules.
  - Acceptance: a Qt offscreen test asserts tab text/order matches the specified sequence.
- [x] [P8-T7] If `src/gui/widgets/schema_builder_dialog.py` or `_schema_builder_tabs.py` approaches the cap after wiring the new tabs, extract construction helpers so each file stays <= 500 lines.
  - Acceptance: both files <= 500 lines; existing dialog round-trip tests pass.
- [x] [P8-T8] Add derived-dialog tests to `tests/gui/test_schema_builder_dialog.py` (and a focused `tests/gui/test_derived_formula_dialog.py`) covering available-name population, validation parity, ordering, and surfacing on Columns.
  - Acceptance: new/updated tests pass.

---

### Phase 9 — Key Tab Redesign (Drag-Drop + Structured Parts + Generic Text)

- [x] [P9-T1] Define a Key-tab view-protocol seam exposing `add_key_part(part)` / `reorder_parts(order)` / `set_parts(parts)` so presenter tests drive key composition without drag events.
  - Acceptance: the protocol is declared; a fake view implements it for presenter tests.
- [x] [P9-T2] Create `src/gui/widgets/_key_tab_drag.py` with draggable column-name tokens, a repeatable Generic Text token, a per-literal value input, and ordered key-part rows.
  - Acceptance: file <= 500 lines; a Qt offscreen test asserts a column drop and a Generic Text drop each invoke `add_key_part` with the correct part type.
- [x] [P9-T3] Enforce that Generic Text is the only token placeable multiple times (column tokens are single-use, consistent with the Columns pool semantics where applicable).
  - Acceptance: a test asserts multiple Generic Text parts are allowed and each carries its own literal value.
- [x] [P9-T4] Create `src/gui/presenters/_key_tab_presenter.py` managing ordered key-part state (column-ref vs literal-text) and reorder operations.
  - Acceptance: file <= 500 lines; a presenter test asserts parts maintain insertion/reorder order.
- [x] [P9-T5] Implement default-key-pattern parsing in the key-tab presenter: parse a caller-supplied pattern into structured `KeyPart` rows and render them via the seam.
  - Acceptance: a presenter test parses a default pattern containing column refs and a literal segment into ordered parts.
- [x] [P9-T6] Implement key-part → `KeySpec` assembly so saving produces the structured model and round-trips through serialization.
  - Acceptance: a presenter test composes parts, saves, reloads, and asserts the key parts are identical in order and type.
- [x] [P9-T7] Reject saving a key that contains no column-ref part (consistent with the model invariant from P1-T7).
  - Acceptance: a presenter test asserts an all-literal key surfaces a validation error and is not saved.
- [x] [P9-T8] Add key-tab tests to `tests/gui/test_key_tab_presenter.py` and a Qt round-trip in `tests/gui/test_schema_builder_dialog.py` covering column parts, repeated Generic Text, default-pattern parse/round-trip, and the no-column-ref guard.
  - Acceptance: new/updated tests pass.

---

### Phase 10 — Dedup Tab Defaults

- [x] [P10-T1] Set the Dedup tab default mode to `aggregate` per Decision 1.
  - Acceptance: a Qt offscreen test asserts a freshly-opened Dedup tab shows `aggregate` selected.
- [x] [P10-T2] Set the default discriminator to the Key per Decision 6/spec point 6.
  - Acceptance: a test asserts the default discriminator resolves to the schema Key.
- [x] [P10-T3] Replace any free-text discriminator entry with a dropdown populated from existing canonical + derived column names only (invariant: discriminator must reference an existing column).
  - Acceptance: a Qt offscreen test asserts the discriminator control is a dropdown and contains only existing column names.
- [x] [P10-T4] Ensure a non-existent column cannot be selected as discriminator (no free-text path remains).
  - Acceptance: a presenter test asserts attempting to set an unknown discriminator is rejected.
- [x] [P10-T5] Add dedup-defaults tests to `tests/gui/test_schema_builder_dialog.py` / presenter tests covering aggregate default, Key discriminator default, and dropdown-only constraint.
  - Acceptance: new/updated tests pass.

---

### Phase 11 — Integration Wiring

- [x] [P11-T1] Wire the full builder open path end-to-end through `open_schema_builder` / `wire_build_schema_buttons`: caller specs → presenter seeding → new tabs (Derived/Columns/Key/Dedup) → save, confirming the menu-action blank path still works.
  - Acceptance: `tests/gui/integration/test_behavioral_schema_import.py` (or a new integration test) exercises per-tab open with specs and menu open without specs.
- [x] [P11-T2] Verify the activation flow end-to-end: tab activation → `on_schema_discovery` → alias-first match → schema selection → import-gate enable; and no-match → placeholder → import disabled.
  - Acceptance: an integration test asserts the full enable/disable transition across activation and selection.
- [x] [P11-T3] Run `poetry run pytest tests/gui` and confirm the GUI suite passes under `QT_QPA_PLATFORM=offscreen`.
  - Acceptance: GUI test directory exits 0; evidence noted in `<FEATURE>/evidence/regression-testing/gui-suite.md` with `Command:`, `EXIT_CODE:`, `Output Summary:`.

---

### Phase 12 — Migrate Bundled Default Schemas Forward

- [x] [P12-T1] Migrate `src/schemas/default_le.schema.json` forward: bump version, convert `key.columns` to structured column-ref parts, add `expected_dtype` per column (numeric→float), and set dedup `mode` to `aggregate`.
  - Acceptance: the file parses via `schema_from_json` without error and serializes back to current format.
- [x] [P12-T2] Migrate `src/schemas/default_aop.schema.json` forward with the same transforms (version, structured key, expected_dtype, aggregate mode).
  - Acceptance: the file parses and serializes without error.
- [x] [P12-T3] Confirm the migrated bundled defaults preserve existing loader behavior (no measure/derived/parity regressions) by running the default-schema and loader-parity tests.
  - Acceptance: `tests/test_default_schemas.py`, `tests/test_schema_loader_*` pass.
- [x] [P12-T4] Update `tests/test_default_schemas.py` to assert the bundled defaults are at the bumped version, use structured key parts, and use `aggregate` dedup mode.
  - Acceptance: updated assertions pass.

---

### Phase 13 — Confidentiality Masking Enforcement

- [x] [P13-T1] Audit every new/changed test fixture and artifact for real workbook values and proprietary source column names; replace any with synthetic masked equivalents.
  - Acceptance: a manual review note in `<FEATURE>/evidence/other/masking-audit.md` lists each fixture file reviewed and confirms synthetic-only content.
- [x] [P13-T2] Run the masking-scan helper (P0-T7) across all files changed by this feature.
  - Acceptance: `<FEATURE>/evidence/qa-gates/masking-scan.md` with `Command:`, `EXIT_CODE: 0`, `Output Summary:` confirming no leaked values/names.
- [x] [P13-T3] Add the masking scan as a pre-commit-style gate task (documented command + clean run) so future fixture additions are checked.
  - Acceptance: the scan command is documented in the feature docs and the clean run is recorded in `<FEATURE>/evidence/qa-gates/masking-scan.md`.

---

### Phase 14 — CI Workflow Adjustment (Conditional)

- [x] [P14-T1] Determine whether the existing CI workflow already installs the PySide6 Ubuntu system libs (`libegl1`, `libgl1`, `libxkbcommon0`, `libdbus-1-3`, `libfontconfig1`) and sets `QT_QPA_PLATFORM=offscreen` for the pytest job.
  - Acceptance: `<FEATURE>/evidence/other/ci-pyside6-check.md` records the workflow file/lines inspected and whether the libs + env var are present.
- [x] [P14-T2] If and only if the libs/env are absent, add them to the workflow as an isolated change (single workflow edit) and note that this triggers the `modified-workflow-needs-green-run` rule (a green run against branch head is required before merge).
  - Acceptance: the workflow change (if needed) is isolated to the CI job; the `modified-workflow-needs-green-run` requirement is recorded in `<FEATURE>/evidence/other/ci-pyside6-check.md`. If P14-T1 shows the libs/env already present, this task records `EXIT_CODE: SKIPPED — already present` per the explicit skip branch authorized in this task text.

---

### Phase 15 — Final QA Loop and Coverage Comparison

- [x] [P15-T1] Run `poetry run black .` and re-run until no files change.
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:`.
- [x] [P15-T2] Run `poetry run ruff check .` and resolve all findings (no unauthorized suppressions).
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:`.
- [x] [P15-T3] Run `poetry run pyright` and resolve all type errors (no strictness reduction).
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` (0 errors).
- [x] [P15-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` under `QT_QPA_PLATFORM=offscreen` and confirm all tests pass.
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` including numeric post-change line% and branch%.
- [x] [P15-T5] Restart the loop from P15-T1 if any QA step failed or changed files, until one clean full pass completes.
  - Acceptance: a single clean pass of black → ruff → pyright → pytest is recorded across the P15 artifacts.
- [x] [P15-T6] Compare coverage against baseline (P0-T5) and verify line >= 85%, branch >= 75%, and no regression on changed lines.
  - Acceptance: `<FEATURE>/evidence/qa-gates/coverage-comparison.md` reports baseline line%/branch%, post-change line%/branch%, and changed-lines coverage; verdict PASS only if thresholds and no-regression hold.
- [x] [P15-T7] Verify all cap-sensitive and new files are <= 500 lines.
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-file-sizes.md` lists every new/modified `.py` file with its line count; all <= 500.
- [x] [P15-T8] Map each spec Acceptance Criterion to a passing test or demo and record the mapping.
  - Acceptance: `<FEATURE>/evidence/other/ac-traceability.md` links each AC to at least one passing test name.

## Test Plan

- Unit (pure logic): `tests/test_schema_model.py`, `tests/test_schema_serialization.py`, `tests/test_dtype_check.py` — model fields, structured key, aggregate mode, serialization round-trip, forward migration, dtype coercion.
- Presenter (no QApplication): `tests/gui/test_schema_builder_presenter.py`, `tests/gui/test_columns_tab_presenter.py`, `tests/gui/test_key_tab_presenter.py`, `tests/gui/test_source_selection_presenter.py` — caller contract, edit/new-from-template, fuzzy pre-population, alias persistence, consumed exclusion, dtype orchestration, key composition, alias-first activation matching.
- Qt offscreen (pytest-qt): `tests/gui/test_schema_builder_dialog.py`, `tests/gui/test_derived_formula_dialog.py`, source-input/import-gate widget tests — drag→assign seam invocation, tab order, dropdown-only dedup, import-gate enable/disable.
- Integration: `tests/gui/integration/test_behavioral_schema_import.py` — end-to-end open paths and activation→gate flow.
- Default schemas: `tests/test_default_schemas.py`, `tests/test_schema_loader_*` — migrated bundled defaults and loader parity.
- Coverage evidence: baseline `<FEATURE>/evidence/baseline/baseline-pytest.md`; post-change `<FEATURE>/evidence/qa-gates/final-pytest.md`; comparison `<FEATURE>/evidence/qa-gates/coverage-comparison.md`.

## Open Questions / Notes

- All ten spec Resolved Design Decisions are treated as authoritative and are not reopened here.
- The version-bump contract uses a named module-level `SCHEMA_FORMAT_VERSION` constant (value `"2.0"`) in `src/schema_model.py` as the single source of truth for the current write format. `SchemaDefinition.version` remains a required, per-instance/per-JSON field with no dataclass default; there is no "default version" to bump. Serialization (P2-T4), forward migration (P3-T1, P3-T3), and bundled-default migration (Phase 12) all bind "bumped version" to `SCHEMA_FORMAT_VERSION`, and pre-bump detection compares the parsed version against that constant (or detects the flat `key.columns` legacy shape).
- `schema_from_json` lives in `src/schema_serialization.py` (not `src/schema_model.py`); migration tasks (Phase 3) target that module accordingly. This refines research section A's API-location note.
- Phase 14 is conditional: if the CI workflow already provisions PySide6 libs and `QT_QPA_PLATFORM=offscreen`, no workflow edit is made and the `modified-workflow-needs-green-run` rule is not triggered.
