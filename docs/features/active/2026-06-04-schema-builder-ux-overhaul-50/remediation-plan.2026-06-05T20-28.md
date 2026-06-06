# schema-builder-ux-overhaul — Remediation Plan (Cycle 1)

- **Issue:** #50
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-05T20-28
- **Status:** Draft (preflight pending)
- **Version:** 1.0
- **Work Mode:** full-feature
- **Tier:** T3 (adapters & UI), Python (PySide6)
- **Cycle entry inputs:** `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/remediation-inputs.2026-06-05T20-28.md`

## Required References

- Cross-language code change policy: `.claude/rules/general-code-change.md`
- Cross-language unit test policy: `.claude/rules/general-unit-test.md`
- Python toolchain & standards: `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
- Quality tiers / coverage gates: `.claude/rules/quality-tiers.md` (line >= 85%, branch >= 75%, no regression on changed lines)
- Commenting/docstrings: `.claude/rules/self-explanatory-code-commenting.md`
- Authoritative spec (AC source): `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` (v1.0; Resolved Design Decisions are binding)
- Cycle-entry findings (sole remediation scope): the `remediation-inputs` artifact named above (R1–R6 blocking, N1–N3 non-blocking)

**All work must comply with these policies; do not duplicate their content here.**

## Remediation Scope and Root Cause

The drag-drop Columns tab (`_columns_tab_drag.py` / `_columns_tab_presenter.py`),
drag-drop Key tab (`_key_tab_drag.py` / `_key_tab_presenter.py`), PowerQuery-style
derived-formula dialog (`_derived_formula_dialog.py`), dtype-check widget
(`_dtype_check_widget.py`), `BuildSpecProvider` (`_schema_build_specs.py`),
`SchemaBuilderPresenter.new_from_template`, and the `on_partial_match` seam on
`SourceSelectionPresenter` were all implemented and unit-tested in isolation but
never wired into the live `SchemaBuilderDialog`, `_schema_builder_tabs.py`, or the
composition root (`app.py`, `_schema_discovery_wiring.py`). This cycle performs
INTEGRATION wiring; it reuses the existing modules and does not author new feature
logic. The defect class that produced the FAIL is isolated unit coverage that
masked missing production wiring, so every wired seam in this plan is proven by an
INTEGRATED test that drives the production object (the opened `SchemaBuilderDialog`
or `build_application`), not an isolated widget/presenter unit test.

## Evidence Location Invariant

All evidence artifacts produced by this plan MUST be written under
`docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/`
using canonical sub-paths (`remediation-baseline/`, `qa-gates/`,
`regression-testing/`, `other/`, `issue-updates/`). Writing to
`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other
non-canonical location is a policy violation. Timestamps use ISO-8601
`yyyy-MM-ddTHH-mm`.

Shorthand used below: `<FEATURE>` = `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50`.

## Toolchain Invariant

Python commands run through Poetry with the `env -u VIRTUAL_ENV` prefix (the
project's Poetry virtual-env points at the global Python otherwise). pytest-qt
collection requires `QT_QPA_PLATFORM=offscreen`. Canonical commands:

- Format: `env -u VIRTUAL_ENV poetry run black .`
- Lint: `env -u VIRTUAL_ENV poetry run ruff check .`
- Type-check: `env -u VIRTUAL_ENV poetry run pyright`
- Test+coverage: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`

---

## Finding → Task Map

| Finding | Spec AC | Closed by |
|---|---|---|
| R1 — drag-drop Columns tab wired into live dialog | AC 6; UI half of 7, 10 | P1-T1..T6 |
| R2 — drag-drop Key tab wired into live dialog | AC 11 (UI) | P2-T1..T5 |
| R3 — derived-formula dialog wired into Derived tab | AC 13 (dialog) | P3-T1..T4 |
| R4 — `BuildSpecProvider` constructed + injected at composition root | AC 5 | P4-T1..T5 |
| R5 — production caller for `new_from_template` | AC 4 | P5-T1..T3 |
| R6 — `on_partial_match` injected into source presenters | AC 9 | P5-T4..T6 |
| N1 — split `tests/test_schema_serialization.py` (669 > 500) | n/a (file-size policy) | P6-T1 |
| N2 — remove dead `# noqa: N802` directives | n/a (suppression policy) | P6-T2 |
| N3 — reconcile spec Decision 1 / AC 14 dedup-migration wording | n/a (doc) | P6-T3 |

---

### Phase 0 — Baseline Capture and Policy Read

- [x] [P0-T1] Read repo policies in required order (`CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`) and record a Phase 0 evidence artifact.
  - Acceptance: `<FEATURE>/evidence/remediation-baseline/phase0-instructions-read.md` exists with `Timestamp:`, `Policy Order:`, and the explicit list of files read.
- [x] [P0-T2] Capture baseline Black formatting state by running `env -u VIRTUAL_ENV poetry run black --check .`.
  - Acceptance: `<FEATURE>/evidence/remediation-baseline/baseline-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T3] Capture baseline Ruff lint state by running `env -u VIRTUAL_ENV poetry run ruff check .`.
  - Acceptance: `<FEATURE>/evidence/remediation-baseline/baseline-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T4] Capture baseline Pyright type-check state by running `env -u VIRTUAL_ENV poetry run pyright`.
  - Acceptance: `<FEATURE>/evidence/remediation-baseline/baseline-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count).
- [x] [P0-T5] Capture baseline test + coverage state by running `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  - Acceptance: `<FEATURE>/evidence/remediation-baseline/baseline-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric baseline line% and branch% headline values and pass/fail counts.
- [x] [P0-T6] Record current line counts of cap-sensitive files that this remediation will modify (`src/gui/widgets/schema_builder_dialog.py`, `src/gui/widgets/_schema_builder_tabs.py`, `src/gui/app.py`, `src/gui/_schema_discovery_wiring.py`, `src/gui/_schema_wiring.py`) against the 500-line cap.
  - Acceptance: `<FEATURE>/evidence/remediation-baseline/baseline-file-sizes.md` lists each path with its current line count and the 500-line cap, flagging any file within 60 lines of the cap as extraction-at-risk.
- [x] [P0-T7] Capture a fail-before signal proving the integration gap: run the existing GUI suite filtered to confirm no current test asserts the live `SchemaBuilderDialog` contains drag widgets and that `build_application` injects a `BuildSpecProvider`/`on_partial_match`.
  - Acceptance: `<FEATURE>/evidence/regression-testing/fail-before-integration.2026-06-05T20-28.md` records `SearchScope:` (production grep targets), `SearchPatterns:` (`ColumnsTabWidget`, `KeyTabWidget`, `DerivedFormulaDialog`, `BuildSpecProvider`, `on_partial_match` as production call sites), and `SearchResult:` showing zero production callers at cycle entry, satisfying the fail-before requirement for the new integrated tests added in Phases 1–5.

---

### Phase 1 — Wire the Drag-Drop Columns Tab into the Live Dialog (R1)

Closes R1. Satisfies spec AC 6 and the UI half of AC 7 and AC 10. The integrated
test that proves the wiring lives in this phase (P1-T6).

- [x] [P1-T1] If `src/gui/widgets/_schema_builder_tabs.py` or `src/gui/widgets/schema_builder_dialog.py` would exceed the 500-line cap after Phases 1–3 additions (per the P0-T6 risk flags), extract the new drag-tab construction into a dedicated helper module (for example `src/gui/widgets/_schema_builder_drag_tabs.py`) BEFORE wiring; otherwise record that no extraction is required.
  - Acceptance: either a new helper module <= 500 lines exists and is imported by the dialog, or `<FEATURE>/evidence/other/cap-precheck-phase1.md` records the projected post-change line counts for both files as <= 500 with the decision "no extraction required".
- [x] [P1-T2] Replace the plain-text Columns editor in `build_columns_tab` (`src/gui/widgets/_schema_builder_tabs.py` L160-172) with a bundle that constructs `ColumnsTabWidget` (`src/gui/widgets/_columns_tab_drag.py`), removing the `QPlainTextEdit` "One column per line" control.
  - Acceptance: `build_columns_tab` returns a controls bundle exposing the `ColumnsTabWidget`; `grep` confirms `src/gui/widgets/_columns_tab_drag.py` is imported by `_schema_builder_tabs.py`; the old `QPlainTextEdit` columns editor is removed from that builder.
- [x] [P1-T3] In `src/gui/widgets/schema_builder_dialog.py`, construct a `ColumnsTabPresenter` (`src/gui/presenters/_columns_tab_presenter.py`) over the new `ColumnsTabWidget` and route `set_columns`/`set_column_dtypes`/source-pool population through the widget's `set_source_pool` / `set_rows` / `set_dtype_indicator` seam instead of the removed text editor.
  - Acceptance: the dialog holds a `ColumnsTabPresenter` instance; `set_columns` populates `ColumnsTabWidget.row_canonicals()`; `set_column_dtypes` drives `set_dtype_indicator` rather than the no-op `del dtypes` path.
- [x] [P1-T4] Render draggable source-column tokens on the Columns tab from the masked preview-slice header so the pool reflects the opened sheet, and render each required/optional row's canonical name, description, and expected dtype.
  - Acceptance: after the dialog is seeded with a preview slice, `ColumnsTabWidget.token_names()` returns one token per header column and each row's `row_label_text(canonical)` includes the expected dtype.
- [x] [P1-T5] Render the dtype-check pass/fail indicator per matched column via `DtypeCheckWidget` / the row indicator, with every displayed example value masked (Decision 5).
  - Acceptance: a coercible matched column shows the green/coercible indicator and a non-coercible one shows the red indicator with a masked failing example (no real workbook value).
- [x] [P1-T6] Add an INTEGRATED test in `tests/gui/test_schema_builder_dialog.py` that opens a real `SchemaBuilderDialog` under `QT_QPA_PLATFORM=offscreen`, seeds it via the production open path, and asserts the live Columns tab contains draggable source-column tokens and dtype indicators (not an isolated `ColumnsTabWidget` unit test).
  - Acceptance: the test instantiates `SchemaBuilderDialog` (the production object the user opens) and asserts (a) `ColumnsTabWidget` is present in the Columns tab widget tree, (b) `token_names()` is non-empty from the seeded preview slice, and (c) at least one dtype indicator is rendered; the test fails if the dialog falls back to the plain-text editor. Test passes under `QT_QPA_PLATFORM=offscreen`.

---

### Phase 2 — Wire the Drag-Drop Key Tab into the Live Dialog (R2)

Closes R2. Satisfies spec AC 11 (UI; the structured-part model is already wired).
The integrated test that proves the wiring lives in this phase (P2-T5).

- [x] [P2-T1] Replace the `QLineEdit` comma-separated Key editor in `build_key_tab` (`src/gui/widgets/_schema_builder_tabs.py` L175-187) with a bundle that constructs `KeyTabWidget` (`src/gui/widgets/_key_tab_drag.py`), retaining the SKU-coercion checkbox.
  - Acceptance: `build_key_tab` returns a bundle exposing the `KeyTabWidget`; `grep` confirms `_key_tab_drag.py` is imported by `_schema_builder_tabs.py`; the comma-separated `QLineEdit` key editor is removed.
- [x] [P2-T2] In `src/gui/widgets/schema_builder_dialog.py`, construct a `KeyTabPresenter` (`src/gui/presenters/_key_tab_presenter.py`) over the `KeyTabWidget` and route `set_key`/`set_key_parts` through the widget's `set_parts` / `add_key_part` seam (replacing the column-ref-only `setText` rendering).
  - Acceptance: the dialog holds a `KeyTabPresenter`; `set_key_parts` populates `KeyTabWidget.parts_text()` with both column-ref and literal-text parts in order (not the previous column-only flattening).
- [x] [P2-T3] Expose the repeatable Generic Text token on the live Key tab and render the caller-supplied default key pattern onto the tab as structured parts.
  - Acceptance: the Generic Text token is reachable in the live tab and a seeded `default_key_pattern` is rendered into ordered `KeyTabWidget` parts including any literal segment.
- [x] [P2-T4] Drive the column-token pool of the live Key tab from the same preview-slice header columns used by the Columns tab so key parts are composed from real source columns.
  - Acceptance: `KeyTabWidget.column_token_names()` reflects the seeded header columns after the dialog is seeded.
- [x] [P2-T5] Add an INTEGRATED test in `tests/gui/test_schema_builder_dialog.py` that opens a real `SchemaBuilderDialog`, seeds a default key pattern via the production open path, and asserts the live Key tab is a `KeyTabWidget` with the rendered structured parts and a placeable Generic Text token (not an isolated `KeyTabWidget` unit test).
  - Acceptance: the test instantiates `SchemaBuilderDialog` and asserts (a) the Key tab contains `KeyTabWidget`, (b) `parts_text()` reflects the seeded default pattern, and (c) the Generic Text affordance is present; the test fails if the dialog falls back to the `QLineEdit` editor. Test passes under `QT_QPA_PLATFORM=offscreen`.

---

### Phase 3 — Wire the Derived-Formula Dialog into the Derived Tab (R3)

Closes R3. Satisfies spec AC 13 (dialog; tab order is already correct). The
integrated test that proves the wiring lives in this phase (P3-T4).

- [x] [P3-T1] Add a button to the Derived tab in `build_derived_tab` (`src/gui/widgets/_schema_builder_tabs.py` L213-227) that, when clicked, opens `DerivedFormulaDialog` (`src/gui/widgets/_derived_formula_dialog.py`).
  - Acceptance: `build_derived_tab` exposes a "New derived column" button in its controls bundle; `grep` confirms `_derived_formula_dialog.py` is imported by the dialog or tabs module.
- [x] [P3-T2] In `src/gui/widgets/schema_builder_dialog.py`, wire the Derived-tab button click to construct and open `DerivedFormulaDialog`, populating its available-name list from the declared columns plus previously-derived columns and reusing the existing `FormulaEvaluator` for validation.
  - Acceptance: opening the dialog offers named + previously-derived columns; an invalid expression surfaces a `FormulaError`-derived message through the existing `FormulaEvaluator` (no new engine introduced).
- [x] [P3-T3] On dialog accept, append the created `DerivedColumnSpec` to the builder state in order and make the derived column appear as a selectable column on the Columns tab.
  - Acceptance: accepting the derived dialog adds the row to the Derived tab in order and the new derived name appears among `ColumnsTabWidget.row_canonicals()` (or the columns-tab selectable set).
- [x] [P3-T4] Add an INTEGRATED test in `tests/gui/test_schema_builder_dialog.py` that opens a real `SchemaBuilderDialog`, triggers the Derived-tab button to open `DerivedFormulaDialog`, accepts a valid derived column, and asserts it appears on the live Columns tab (driven through the dialog, not an isolated `DerivedFormulaDialog` unit test).
  - Acceptance: the test instantiates `SchemaBuilderDialog`, invokes the Derived button handler to produce a `DerivedFormulaDialog`, asserts the available-name list includes a prior-derived name, and asserts the accepted derived column surfaces on the Columns tab. Test passes under `QT_QPA_PLATFORM=offscreen`.

---

### Phase 4 — Construct and Inject a BuildSpecProvider at the Composition Root (R4)

Closes R4. Satisfies spec AC 5. The integrated test that proves the wiring lives
in this phase (P4-T5), exercising the injected provider through
`build_application`.

- [x] [P4-T1] If wiring a production `BuildSpecProvider` would push `src/gui/app.py` over the 500-line cap (per the P0-T6 flag — app.py measures 497 lines, within the 60-line extraction-at-risk window of the cap), extract the provider construction into `src/gui/_schema_build_specs.py` (or a new `src/gui/_schema_provider_factory.py`) BEFORE wiring it into `app.py`.
  - Acceptance: `src/gui/app.py` <= 500 lines after the change; the provider-construction helper module is <= 500 lines; `<FEATURE>/evidence/other/cap-precheck-phase4.md` records the pre/post line counts for `app.py`.
- [x] [P4-T2] Implement a production `BuildSpecProvider` (satisfying the `BuildSpecProvider` protocol in `src/gui/_schema_build_specs.py`) that maps each source key (`"LE"`, `"aop"`, `"sku_lu"`) to a `CallerBuildSpec` carrying that source's required/optional specs, default key pattern, and a masked preview slice.
  - Acceptance: the provider's `build_spec_for(key)` returns a `CallerBuildSpec` with non-empty required specs per source; a unit test asserts each of the three keys resolves to a distinct spec and that the preview slice contains only synthetic/masked content.
- [x] [P4-T3] Inject the provider into `wire_build_schema_buttons(...)` at the call site in `src/gui/_schema_discovery_wiring.py` (`wire_schema_discovery_and_gating`, L74) by adding a `spec_provider` argument threaded from `wire_schema_discovery_and_gating`'s caller in `app.py`.
  - Acceptance: `wire_build_schema_buttons` is called with a non-`None` `spec_provider`; the menu-action path (`wire_schema_builder`) remains blank by design (Decision 7); `grep` confirms a `BuildSpecProvider` is instantiated in `src/`.
- [x] [P4-T4] Construct the provider in `build_application` (`src/gui/app.py`) and pass it through `wire_schema_discovery_and_gating(...)` so the per-tab "Build/Edit schema" button seeds the builder for its active source.
  - Acceptance: `build_application` constructs the production provider and passes it into the discovery/gating wiring; opening the builder via a per-tab button seeds required/optional specs, default key pattern, and masked preview slice.
- [x] [P4-T5] Add an INTEGRATED test in `tests/gui/test_app_wiring_schema.py` that calls `build_application` (the composition root) and asserts the per-tab build path opens a seeded builder via the injected `BuildSpecProvider` — not an isolated provider unit test.
  - Acceptance: the test exercises `build_application`, triggers a per-tab `build_schema_requested`, and asserts the opened builder received the source's required/optional specs and a masked preview slice (e.g., the seeded presenter state is non-empty); the menu-action path is asserted to remain blank. Test passes under `QT_QPA_PLATFORM=offscreen`.

---

### Phase 5 — Wire new_from_template and on_partial_match into Production (R5, R6)

Closes R5 and R6. Satisfies spec AC 4 and AC 9. The integrated tests that prove
the wiring live in this phase (P5-T3 for R5, P5-T6 for R6), both driven through
`build_application`.

- [x] [P5-T1] Surface a "New from template" affordance (menu action and/or per-tab button) at the composition root that resolves the closest existing schema name and calls `SchemaBuilderPresenter.new_from_template(closest_schema_name)` (`src/gui/presenters/schema_builder_presenter.py` L231).
  - Acceptance: a production call site invokes `new_from_template`; `grep ".new_from_template("` returns at least one match in `src/` (not only `tests/`).
- [x] [P5-T2] Route the new-from-template open through the existing builder open path so the seeded template state renders into the live `SchemaBuilderDialog` (drag tabs from Phases 1–2) with a cleared name awaiting save-as.
  - Acceptance: opening new-from-template renders the template's columns/key/dedup into the live dialog with a blank Identity name; the template file is not overwritten.
- [x] [P5-T3] Add an INTEGRATED test (in `tests/gui/test_app_wiring_schema.py` or `tests/gui/integration/test_behavioral_schema_import.py`) that drives the new-from-template affordance from `build_application` and asserts `new_from_template` is reached and the opened dialog is seeded from the template — not an isolated presenter unit test.
  - Acceptance: the test exercises `build_application`, triggers the new-from-template affordance, and asserts the production presenter's `new_from_template` ran (seeded dialog state mirrors the template with a blank name). Test passes under `QT_QPA_PLATFORM=offscreen`.
- [x] [P5-T4] Pass an `on_partial_match` callback when constructing the three `SourceSelectionPresenter` instances in `build_application` (`src/gui/app.py` L340-347); the callback opens the new-from-template builder (R5 path) for the closest existing schema on a partial activation outcome.
  - Acceptance: each of the three `SourceSelectionPresenter(...)` constructions passes a non-`None` `on_partial_match`; `grep` confirms `on_partial_match=` appears at the three production call sites in `app.py`.
- [x] [P5-T5] Connect the `on_partial_match` callback to the new-from-template open path so a partial activation match surfaces the seeded builder for the closest existing schema (Decision 6), reusing the R5 affordance.
  - Acceptance: invoking the callback with a closest-schema name opens the new-from-template builder seeded from that schema; a no-match still sets the placeholder and keeps Import disabled (existing behavior preserved).
- [x] [P5-T6] Add an INTEGRATED test in `tests/gui/test_source_selection_presenter.py` driven through `build_application` (or asserting the wiring established by `build_application`) that a partial-match activation outcome invokes the injected `on_partial_match` and reaches the new-from-template builder — not an isolated presenter unit test that constructs the seam directly.
  - Acceptance: the test confirms the production `SourceSelectionPresenter` built by `build_application` carries a non-`None` `on_partial_match` and that a simulated partial activation reaches the new-from-template open path. Test passes under `QT_QPA_PLATFORM=offscreen`.

---

### Phase 6 — Non-Blocking Cleanup (N1, N2, N3)

Closes N1, N2, N3. No behavior change; each task is self-validating.

- [x] [P6-T1] Split `tests/test_schema_serialization.py` (669 lines, over the 500-line cap) into focused modules — round-trip serialization vs. forward-migration — preserving every existing test.
  - Acceptance: `tests/test_schema_serialization.py` and the new sibling module (for example `tests/test_schema_migration.py`) are each <= 500 lines; the union of tests equals the prior set (no test deleted); `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest tests/test_schema_serialization.py tests/test_schema_migration.py` exits 0.
- [x] [P6-T2] Remove the dead `# noqa: N802` directives in `src/gui/widgets/_columns_tab_drag.py` (L78, L207, L222) and `src/gui/widgets/_key_tab_drag.py` (L76, L169, L252, L267); the `N` ruleset is not in ruff `select`, so the directives are no-ops.
  - Acceptance: no `# noqa: N802` remains in either file; `env -u VIRTUAL_ENV poetry run ruff check src/gui/widgets/_columns_tab_drag.py src/gui/widgets/_key_tab_drag.py` exits 0 with no new findings.
- [x] [P6-T3] Reconcile the spec text on dedup migration (documentation only): update `spec.md` Decision 1 and AC 14 to state the migration to aggregate mode applies to schemas that have a discriminator (LE); schemas without a discriminator (AOP) correctly retain `mode: none`.
  - Acceptance: `spec.md` Decision 1 and AC 14 reflect the discriminator-conditional wording; no code or schema JSON is changed by this task.

---

### Phase 7 — Final QA Loop and Coverage Comparison

Full toolchain loop for Python (format → lint → type-check → test). Restart from
P7-T1 whenever a step fails or changes files until one clean full pass completes.

- [x] [P7-T1] Run `env -u VIRTUAL_ENV poetry run black .` and re-run until no files change.
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:`.
- [x] [P7-T2] Run `env -u VIRTUAL_ENV poetry run ruff check .` and resolve all findings (no unauthorized suppressions per `python-suppressions.md`).
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:`.
- [x] [P7-T3] Run `env -u VIRTUAL_ENV poetry run pyright` and resolve all type errors (no strictness reduction).
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` (0 errors).
- [x] [P7-T4] Run `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` and confirm all tests pass.
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` including numeric post-change line% and branch% and pass/fail counts.
- [x] [P7-T5] Restart the loop from P7-T1 if any QA step failed or changed files, until one clean full pass of black → ruff → pyright → pytest completes.
  - Acceptance: a single clean pass is recorded across the P7 artifacts (the final-pass artifacts all show `EXIT_CODE: 0`).
- [x] [P7-T6] Compare coverage against the remediation baseline (P0-T5) and verify line >= 85%, branch >= 75%, and no regression on changed lines.
  - Acceptance: `<FEATURE>/evidence/qa-gates/coverage-comparison.md` reports baseline line%/branch% (from P0-T5), post-change line%/branch% (from P7-T4), and changed-lines coverage; verdict PASS only if thresholds and no-regression both hold.
- [x] [P7-T7] Run the confidentiality masking scan across all files changed by this remediation cycle and confirm no real workbook values or proprietary source column names were introduced (Decision 5).
  - Acceptance: `<FEATURE>/evidence/qa-gates/masking-scan.md` with `Command:`, `EXIT_CODE: 0`, `Output Summary:` confirming the changed/added files (especially any new preview-slice fixtures) contain only synthetic/masked content.
- [x] [P7-T8] Verify all modified and new `.py` files are <= 500 lines (`schema_builder_dialog.py`, `_schema_builder_tabs.py`, `app.py`, `_schema_discovery_wiring.py`, `_schema_wiring.py`, `_schema_build_specs.py`, any new helper modules, and the split test modules).
  - Acceptance: `<FEATURE>/evidence/qa-gates/final-file-sizes.md` lists every modified/new `.py` file with its line count; all <= 500.
- [x] [P7-T9] Re-confirm, for each of R1–R6, that the seam has a production caller reachable from `build_application` or the opened `SchemaBuilderDialog` (not only a unit test), and map each R# to its passing integrated test.
  - Acceptance: `<FEATURE>/evidence/other/remediation-traceability.md` maps R1→P1-T6, R2→P2-T5, R3→P3-T4, R4→P4-T5, R5→P5-T3, R6→P5-T6, names each passing integrated test, and records the production grep proving each seam is reachable from `build_application` / the opened dialog; it also confirms N1–N3 closed.
- [x] [P7-T10] Reconcile acceptance-criteria checkboxes in the AC source files (full-feature mode: spec.md AND user-story.md) against the passing integrated tests. For each AC delivered by R1-R6 (spec.md AC 4, 5, 6, 7, 9, 10, 11, 13 and the corresponding user-story.md items), confirm the criterion is proven by its integrated test (P1-T6/P2-T5/P3-T4/P4-T5/P5-T3/P5-T6) before leaving it [x]; if an integrated test does not yet prove it, set the box to [ ] and document the gap. Do not alter criterion text.
  - Acceptance: `<FEATURE>/evidence/qa-gates/ac-reconciliation.md` records, for each remediated AC in spec.md and user-story.md, the integrated test that proves it and the final checkbox state; an AC Status Summary (Source, Total, Checked, Remaining, Items remaining) is included; no AC remains [x] without a named passing integrated test.

## Open Questions / Notes

- This cycle is INTEGRATION wiring only. The model layer (expected_dtype, version
  bump, forward migration, structured key parts, aggregate dedup) and the orphaned
  widget/presenter modules are already implemented and unit-tested; this plan
  reuses them and does not re-author feature logic.
- The verification standard is non-negotiable: each R# acceptance requires a
  production-call-site assertion (the seam is reachable from `build_application` or
  the opened `SchemaBuilderDialog`), per the inputs' "Verification on Re-Review".
  Isolated widget/presenter unit tests do not satisfy R1–R6.
- Cap pre-checks (P1-T1, P4-T1) gate any extraction needed to keep
  `schema_builder_dialog.py`, `_schema_builder_tabs.py`, and `app.py` at or under
  the 500-line cap before new wiring is added.
