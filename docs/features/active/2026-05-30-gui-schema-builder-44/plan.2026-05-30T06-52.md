# gui-schema-builder — Plan

- **Issue:** #44
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30T06-52
- **Status:** Ready for preflight
- **Version:** 1.0
- **Work Mode:** full-feature

## Required References

All work must comply with these repository policies (do not duplicate their content here):

- `CLAUDE.md` (standing instructions)
- `.claude/rules/general-code-change.md`
- `.claude/rules/general-unit-test.md`
- `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
- `.claude/rules/quality-tiers.md`
- `.claude/rules/self-explanatory-code-commenting.md`
- `.claude/rules/tonality.md`

Requirements sources (full-feature): `spec.md` and `user-story.md` (AC1–AC9) in this feature
folder. Research: `artifacts/research/2026-05-29-configurable-schema-subsystem-research.md`
(Section 3 GUI architecture, Section 5.4 wireframes).

## Scope, Decisions, and Invariants (read before executing)

- **Feature D is additive integration.** New modules: `SchemaService`, two view protocols,
  two pure presenters, two passive dialogs (+ helper modules), composition wiring, and a
  schema-aware import path. No CLI/transform/loader module is modified.
- **Consumed (do NOT modify):** `src/schema_registry.py` (`SchemaRegistry`,
  `DiskSchemaFileStore`, `load_bundled_default`), `src/schema_matching.py`
  (`find_best_match_in_registry`, `MatchResult`, `MismatchReport.render`),
  `src/schema_loader.py` (`SchemaLoader.load`), `src/schema_formula.py`
  (`FormulaEvaluator`, `FormulaError`), `src/schema_model.py`,
  `src/schema_settings.py` (`resolve_registry_dir`).
- **Import-flow risk decision (lower-risk option, explicit):** The existing default
  loader path (`PipelineService.import_le/import_aop/import_skulu`) is preserved unchanged
  for known AOP/LE files; their results stay byte-identical and all existing GUI tests stay
  green. `SchemaLoader` is invoked **only** when schema discovery selects a non-default
  (registry/user-built) schema for a file. This avoids re-routing the known-file path through
  `SchemaLoader` and the associated parity risk. A new method
  `PipelineService.import_with_schema(raw, schema)` (additive) provides the schema-driven
  path; existing methods and signatures are untouched.
- **Behavior-preserving edits only** to `app.py`, `pipeline_service.py`, `protocols.py`,
  `main_window.py`: additive members, optional-keyword params with defaults that reproduce
  today's behavior, or new menu/action surface. No existing signature or default behavior
  changes.
- **No new dependency** beyond `asteval` (already present via Feature C).
- **File-size cap:** every new/edited file < 500 lines. The schema builder dialog and
  presenter MUST be split into helper modules (`_schema_builder_*`) to stay under the cap.
- **Presenters are pure Python (no Qt import)** and unit-tested without a `QApplication`
  using plain-Python fakes implementing the view protocols. Dialogs and import-flow wiring
  are tested via `pytest-qt`; the GUI conftest already pins `QT_QPA_PLATFORM=offscreen`.
- **Pyright strict; no new suppressions** beyond pre-authorized patterns. If a suppression
  appears unavoidable, the executor STOPS and escalates per `python-suppressions.md`.
- **Tests:** no temp files, no network, no real DB/Excel. Use in-memory fakes and the
  Feature A in-memory `SchemaFileStore` fake. Schema persistence in tests flows only through
  the injectable `SchemaRegistry` boundary.
- **Per-batch budget:** at most 3 production + 3 test files per implementation phase.

### THIS-feature behavior-preservation check (explicit)

- `git diff --name-only main` will list committed Feature A/B/C ancestry on the shared epic
  branch. That is **NOT** a violation of this feature's scope.
- The correct THIS-feature regression check is: a clean working tree on existing
  CLI/transform/loader paths after Feature D work — i.e. empty
  `git diff --name-only HEAD` and a clean `git status` for
  `src/normalize_le.py`, `src/load_aop.py`, `src/load_skulu.py`, `src/mix_*.py`,
  `src/etl_*.py`, `src/calculator.py`, `src/mix_pipeline*.py`, and the Feature A/B/C
  `src/schema_*.py` modules. Edits to `app.py`/`pipeline_service.py`/`protocols.py`/
  `main_window.py` must be additive and keep all existing GUI tests green.

### Evidence location invariant (non-overridable)

All evidence artifacts MUST be written under
`docs/features/active/2026-05-30-gui-schema-builder-44/evidence/<kind>/` per
`.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Canonical sub-paths used by
this plan: `evidence/baseline/`, `evidence/qa-gates/`, `evidence/regression-testing/`,
`evidence/issue-updates/`. Writing under `artifacts/baselines/`, `artifacts/qa/`,
`artifacts/coverage/`, or any other non-canonical path is a policy violation. If any task or
caller instruction supplies a non-canonical path, the executor substitutes the canonical
path and records `EVIDENCE_LOCATION_OVERRIDE_REJECTED: <supplied> replaced with <canonical>`.

---

## Implementation Plan (Atomic Tasks)

### Phase 0 — Baseline Capture & Policy Read

- [x] [P0-T1] Read the policy files in required order and record a Phase 0 evidence artifact.
  - Read, in order: `CLAUDE.md`; `.claude/rules/general-code-change.md`;
    `.claude/rules/general-unit-test.md`; `.claude/rules/python.md`;
    `.claude/rules/python-suppressions.md`; `.claude/rules/quality-tiers.md`;
    `.claude/rules/self-explanatory-code-commenting.md`; `.claude/rules/tonality.md`.
  - Acceptance: `evidence/baseline/phase0-instructions-read.md` exists with `Timestamp:`,
    `Policy Order:`, and the explicit list of files read.

- [x] [P0-T2] Capture the Black formatting baseline.
  - Command: `poetry run black --check .`
  - Acceptance: `evidence/baseline/baseline-black.<ISO-8601>.md` with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, `Output Summary:` (pass/fail and any would-reformat count).

- [x] [P0-T3] Capture the Ruff lint baseline.
  - Command: `poetry run ruff check .`
  - Acceptance: `evidence/baseline/baseline-ruff.<ISO-8601>.md` with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, `Output Summary:` (error count).

- [x] [P0-T4] Capture the Pyright strict type-check baseline.
  - Command: `poetry run pyright`
  - Acceptance: `evidence/baseline/baseline-pyright.<ISO-8601>.md` with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).

- [x] [P0-T5] Capture the Pytest + coverage baseline (headline numeric coverage required).
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `evidence/baseline/baseline-pytest.<ISO-8601>.md` with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, `Output Summary:` recording passed-test count, baseline
    total line coverage %, and baseline total branch coverage % (numeric, not placeholders).

- [x] [P0-T6] Record the THIS-feature protected-path baseline (clean pre-work tree proof).
  - Command: `git status --porcelain` and `git diff --name-only HEAD`
  - Acceptance: `evidence/baseline/baseline-protected-paths.<ISO-8601>.md` with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, `Output Summary:` confirming a clean tree before Phase 1 and
    listing the protected-path globs that must remain unchanged (per the THIS-feature check
    above).

### Phase 1 — SchemaService Seam (T2)

Production budget: 1 file. Test budget: 1 file.

- [x] [P1-T1] Add `SchemaServiceProtocol` and `SchemaService` in
  `src/gui/services/schema_service.py`.
  - The protocol carries the call surface the presenters and import-flow wiring depend on
    (no Qt import): `list_schema_names() -> list[str]`,
    `load_schema(name: str) -> SchemaDefinition`,
    `save_schema(schema: SchemaDefinition) -> None`,
    `find_best_match(headers: Sequence[str]) -> MatchResult`, and
    `build_loader(schema: SchemaDefinition) -> SchemaLoader`.
  - `SchemaService` is constructed with an injected `SchemaRegistry` and an optional
    `FormulaEvaluator` (default `FormulaEvaluator()`); it wraps
    `SchemaRegistry.list_schemas/load/save`, `find_best_match_in_registry`, and builds a
    `SchemaLoader(schema, formula_evaluator=...)`. It performs no Qt, no direct disk, and no
    transform logic; all persistence flows through the injected registry.
  - Add a module-level factory `build_default_schema_service(*, env, platform, home) ->
    SchemaService` that resolves the registry dir via `resolve_registry_dir` and constructs a
    `SchemaRegistry(registry_dir, DiskSchemaFileStore())`, so the composition root has one
    call and tests can inject an in-memory store directly.
  - Acceptance: file < 500 lines; class/function docstrings per
    `self-explanatory-code-commenting.md`; no Qt import; imports only Feature A/B/C public
    surface.

- [x] [P1-T2] Add a `FakeSchemaService` to `tests/gui/fakes/fake_services.py` implementing
  `SchemaServiceProtocol`.
  - Records `save_schema` calls, returns controlled `list_schema_names`, controlled
    `MatchResult` from `find_best_match`, and a real `SchemaLoader` from `build_loader`. Uses
    the pre-authorized `# noqa: ARG002 - match SchemaServiceProtocol API` pattern only where a
    Protocol method legitimately ignores a parameter.
  - Acceptance: fake added; existing fakes unchanged; no `QApplication` needed.

- [x] [P1-T3] Add `tests/gui/test_schema_service.py` unit tests for `SchemaService`.
  - Cover: `list_schema_names`/`load_schema`/`save_schema` delegate to the injected registry
    (in-memory `SchemaFileStore` fake); `find_best_match` returns the registry best match for
    given headers (positive: suitable match; negative: no/low match yields the `MatchResult`
    with mismatch report); `build_loader` returns a `SchemaLoader` whose `load` applies the
    schema; `build_default_schema_service` resolves a registry from injected
    `env/platform/home`. Arrange–Act–Assert; deterministic; no temp files/network/real disk.
  - Acceptance: tests pass; service-module changed-line coverage observed in P1-T4.

- [x] [P1-T4] Run the per-phase Python toolchain loop for Phase 1 and confirm green.
  - Command sequence (restart on any failure/auto-fix): `poetry run black .` →
    `poetry run ruff check .` → `poetry run pyright` →
    `poetry run pytest tests/gui/test_schema_service.py --cov=src/gui/services/schema_service --cov-branch --cov-report=term-missing`
  - Acceptance: all stages green in one pass; `schema_service.py` line coverage >= 85% and
    branch coverage >= 75%. (Recorded in the Phase 5 coverage-delta artifact; no separate
    per-phase artifact required.)

### Phase 2 — View Protocols + Pure Presenters (T2)

Production budget: 3 files. Test budget: 2 files.

- [x] [P2-T1] Add `SchemaBuilderViewProtocol` and `ColumnMatchingViewProtocol` to
  `src/gui/protocols.py` (additive, no Qt import).
  - `ColumnMatchingViewProtocol` methods (presenter-driven): `set_unmatched_required(items)`,
    `set_source_columns(names)`, `set_fuzzy_suggestions(items)`, `set_assignment(required,
    source)`, `mark_ignored(required)`, `show_error(message)`, and a result reader the
    presenter consults (e.g. `get_assignments() -> dict[str, str]`). Use plain Python types
    (`list`/`dict`/`tuple` of `str`/`float`), no Qt types.
  - `SchemaBuilderViewProtocol` methods covering the tabbed surface: identity getters/setters,
    column-row get/set, key get/set, dedup get/set, derived/formula get/set, preview render
    (`show_preview(rows)`), and `show_formula_error(message)` / `clear_formula_error()`.
  - Do NOT modify the existing four protocols. Update `__all__` to include the two new names.
  - Acceptance: `protocols.py` stays < 500 lines (split is not expected; if it would exceed
    the cap, STOP and escalate before splitting); both protocols are `@runtime_checkable`;
    full docstrings; no Qt import.

- [x] [P2-T2] Add `ColumnMatchingPresenter` in
  `src/gui/presenters/column_matching_presenter.py` (pure Python, no Qt).
  - Constructor-injected: a `ColumnMatchingViewProtocol` view and a `SchemaServiceProtocol`.
    Drives the manual-matching workflow from a `MatchResult`/headers: present unmatched
    required columns with their aliases, present source columns, compute fuzzy suggestions
    with similarity scores (consume Feature B `MismatchReport.unmatched_required[*].candidates`
    — do not re-implement scoring), accept point-and-click assignments, allow marking optional
    columns ignored, and, when the user opts to persist, build alias additions and save the
    updated schema via `SchemaServiceProtocol.save_schema`.
  - Acceptance: no Qt import; file < 500 lines; deterministic (no clock/RNG); full docstrings;
    persistence flows only through the service/registry boundary.

- [x] [P2-T3] Add `SchemaBuilderPresenter` in
  `src/gui/presenters/schema_builder_presenter.py` plus a pure helper module
  `src/gui/presenters/_schema_builder_state.py` (no Qt) to hold the in-progress schema state
  and the per-tab assembly logic, keeping both files < 500 lines.
  - `SchemaBuilderPresenter` is constructor-injected with a `SchemaBuilderViewProtocol` and a
    `SchemaServiceProtocol`. Responsibilities: hold the in-progress `SchemaDefinition` data as
    plain Feature A model objects; coordinate identity/columns/key/dedup/derived edits;
    validate runtime formula entry through `FormulaEvaluator.validate` against the known
    column set, surfacing `FormulaError.args[0]` via `show_formula_error` (inline reject) and
    `clear_formula_error` on success; apply the in-progress schema to loaded preview rows via
    `SchemaService.build_loader(schema).load(...)` for the Preview tab; and persist via
    `SchemaService.save_schema` on save. `_schema_builder_state.py` owns the pure
    state-to-`SchemaDefinition` assembly (raises `SchemaValidationError` from the model on
    structurally invalid input, surfaced by the presenter as an error).
  - Acceptance: neither file imports Qt; each file < 500 lines; full docstrings; formula
    validation routes through Feature C only; no new dependency.

- [x] [P2-T4] Add `FakeColumnMatchingView` and `FakeSchemaBuilderView` to
  `tests/gui/fakes/fake_views.py` implementing the two new protocols.
  - Record presenter calls and return controlled getter data (assignments, identity fields,
    column rows, formula text), with no Qt and no logic. Use the pre-authorized
    `# noqa: ARG002 - match <Protocol> API` pattern only where required.
  - Acceptance: fakes added; existing fakes unchanged.

- [x] [P2-T5] Add `tests/gui/test_column_matching_presenter.py` and
  `tests/gui/test_schema_builder_presenter.py` (presenter unit tests, no `QApplication`).
  - `test_column_matching_presenter.py` (AC3): unmatched-required columns and source columns
    are pushed to the view; fuzzy suggestions carry similarity scores from the Feature B
    report; a point-and-click assignment is recorded; an optional column can be marked
    ignored; "accept and save" persists alias additions via the fake service
    (`save_schema` called with the expected alias-augmented schema); negative flow: assigning a
    required column to no source surfaces an error and does not persist.
  - `test_schema_builder_presenter.py` (AC4, AC5): identity/columns/key/dedup/derived edits
    assemble a valid `SchemaDefinition`; saving calls `save_schema`; Preview applies the
    in-progress schema to preview rows via the fake service's `build_loader`; runtime formula
    entry — valid expression accepted and `clear_formula_error` called; invalid/unsafe/
    unknown-column expression rejected inline with the descriptive `FormulaError` message via
    `show_formula_error` (parametrize at least: syntax error, disallowed construct, unknown
    column); structurally invalid assembly surfaces the model `SchemaValidationError` as an
    error. Arrange–Act–Assert; deterministic; no temp files/network/real disk.
  - Acceptance: both test files pass without a `QApplication`.

- [x] [P2-T6] Run the per-phase Python toolchain loop for Phase 2 and confirm green.
  - Command sequence (restart on failure/auto-fix): `poetry run black .` →
    `poetry run ruff check .` → `poetry run pyright` →
    `poetry run pytest tests/gui/test_column_matching_presenter.py tests/gui/test_schema_builder_presenter.py --cov=src/gui/presenters/column_matching_presenter --cov=src/gui/presenters/schema_builder_presenter --cov=src/gui/presenters/_schema_builder_state --cov-branch --cov-report=term-missing`
  - Acceptance: all stages green in one pass; each presenter/state module line coverage
    >= 85% and branch coverage >= 75% (final values recorded in the Phase 5 delta artifact).

### Phase 3 — Passive Qt Dialogs (T3, pytest-qt)

Production budget: 3 files (+ split helpers as needed to respect the cap). Test budget: 2 files.

- [x] [P3-T1] Add `src/gui/widgets/column_matching_dialog.py` — a passive `QDialog`
  implementing `ColumnMatchingViewProtocol`.
  - Two side-by-side lists (unmatched required with aliases; source columns with status), a
    fuzzy-suggestions area showing top candidates with scores, an Ignore control (enabled only
    for optional columns), an "Accept and save to schema" checkbox, and accept/cancel buttons.
    Holds no logic; user actions are exposed as signals/public methods the composition root
    wires to `ColumnMatchingPresenter`. Provide public test seams (e.g.
    `set_item_checked`/`select_*`) mirroring the `ExportDialog` pattern.
  - Acceptance: file < 500 lines; structurally satisfies `ColumnMatchingViewProtocol`; no
    transform/service logic.

- [x] [P3-T2] Add `src/gui/widgets/schema_builder_dialog.py` plus helper modules
  `src/gui/widgets/_schema_builder_tabs.py` (tab construction) and, if needed,
  `src/gui/widgets/_schema_builder_columns_tab.py` — a passive tabbed `QDialog` implementing
  `SchemaBuilderViewProtocol`.
  - Tabs: Identity, Columns (canonical name / role / required / aliases), Key (ordered key
    columns + sku coercion), Dedup (none/collapse, discriminator, per-measure additive vs
    select-from), Derived/Formula (name + formula text with inline validation surface), and
    Preview. The dialog is passive: it renders state the presenter pushes and exposes user
    edits via getters/signals; it constructs no service. Split tab construction into the
    helper module(s) so every file stays < 500 lines.
  - Acceptance: each file < 500 lines; structurally satisfies `SchemaBuilderViewProtocol`; no
    logic beyond view state; full docstrings.

- [x] [P3-T3] Add `tests/gui/test_column_matching_dialog.py` (pytest-qt).
  - Verify the dialog renders unmatched-required and source lists, shows fuzzy suggestions with
    scores, toggles the Ignore control for optional vs required columns, reports assignments
    via `get_assignments`, and reflects the "accept and save" checkbox. Use `qtbot.addWidget`;
    fabricated data only; no temp files/network.
  - Acceptance: tests pass under `QT_QPA_PLATFORM=offscreen` (already pinned by the GUI
    conftest).

- [x] [P3-T4] Add `tests/gui/test_schema_builder_dialog.py` (pytest-qt).
  - Verify each tab renders the pushed state and reports edits back through the protocol
    getters: identity round-trip, a column row round-trip (name/role/required/aliases), key
    selection, dedup mode switch revealing discriminator/per-measure controls, derived/formula
    entry surfacing the inline error label on `show_formula_error` and clearing it on
    `clear_formula_error`, and `show_preview` rendering preview rows. Use `qtbot.addWidget`;
    fabricated data only.
  - Acceptance: tests pass headless.

- [x] [P3-T5] Run the per-phase Python toolchain loop for Phase 3 and confirm green.
  - Command sequence (restart on failure/auto-fix): `poetry run black .` →
    `poetry run ruff check .` → `poetry run pyright` →
    `poetry run pytest tests/gui/test_column_matching_dialog.py tests/gui/test_schema_builder_dialog.py --cov-branch --cov-report=term-missing`
  - Acceptance: all stages green in one pass; widget behavior exercised via pytest-qt.

### Phase 4 — Composition Wiring + Import-Flow Integration (additive, behavior-preserving)

Production budget: 3 files. Test budget: 2 files.

- [x] [P4-T1] Add the schema-aware import path to `src/gui/pipeline_service.py` (additive only).
  - Add `import_with_schema(raw: pd.DataFrame, schema: SchemaDefinition) -> pd.DataFrame` that
    builds a `SchemaLoader(schema)` and returns `loader.load(raw)`; add the same method to
    `PipelineServiceProtocol`. Do NOT change the signatures, defaults, or behavior of
    `import_le`/`import_aop`/`import_skulu`/`import_sources`/`run_pipeline`/`save_to_db`/
    `open_db`. The known-file path remains the default loaders (import-flow risk decision
    above); `import_with_schema` is used only when discovery selects a non-default schema.
  - Acceptance: only additive members; all existing `tests/gui/test_pipeline_service.py`
    tests stay green; file < 500 lines.

- [x] [P4-T2] Add the "Schema Builder..." action to `src/gui/main_window.py` (additive).
  - Add a menu bar with a "Schema Builder..." action and a `schema_builder_requested` signal
    emitted on trigger. Do NOT alter existing widgets, signals, properties, or the control
    row. Keep `main_window.py` < 500 lines.
  - Acceptance: existing `tests/gui/test_main_window.py` stays green; new signal exposed.

- [x] [P4-T3] Wire schema discovery and dialog launch in the composition root.
  - Add `src/gui/_schema_wiring.py` (a new wiring helper, analogous to
    `_import_dispatch_wiring.py`, to keep `app.py` < 500 lines) that: (a) connects
    `window.schema_builder_requested` to open the `SchemaBuilderDialog` driven by a
    `SchemaBuilderPresenter` over the injected `SchemaService` (AC6, outside the import flow);
    and (b) integrates schema discovery into the import flow — after a sheet preview, read the
    header row and call `SchemaService.find_best_match(headers)`; on a suitable match above the
    acceptance threshold, proceed via the existing default loader for known files (or
    `import_with_schema` for a non-default matched schema); on no suitable match, surface
    `MatchResult.report.render()` and offer two actions (open the manual `ColumnMatchingDialog`
    or open the `SchemaBuilderDialog`).
  - In `src/gui/app.py`, build/inject the `SchemaService` via
    `build_default_schema_service(...)` (additive: add an optional `schema_service` keyword to
    `build_application`, defaulting to the production service so tests can inject a fake) and
    call the new `_schema_wiring` helper. Extend `WiredApplication` with the new collaborators
    (additive dataclass fields). Do NOT change existing wiring behavior or existing
    `build_application` defaults.
  - Acceptance: `app.py`, `_schema_wiring.py`, and `main_window.py` each < 500 lines; existing
    `tests/gui/test_app_*.py` and `tests/gui/integration/*` tests stay green; discovery
    threshold uses the Feature B default (do not invent a new constant — reuse
    `MatchResult.score` against the documented acceptance bar).

- [x] [P4-T4] Add `tests/gui/test_app_wiring_schema.py` (pytest-qt) for the composition wiring.
  - Verify: `build_application(schema_service=FakeSchemaService(...))` wires the
    "Schema Builder..." action to open the builder (AC6); a suitable-match header set drives
    import without surfacing a mismatch; a no-match header set surfaces the rendered mismatch
    explanation and exposes the two action paths (AC2). Inject fakes/synchronous runner; no
    real Excel/DB.
  - Acceptance: tests pass headless; no existing test modified to pass.

- [x] [P4-T5] Add `tests/gui/integration/test_behavioral_schema_import.py` (pytest-qt,
  end-to-end-ish through the composition root with fakes).
  - AC1 parity assertion (explicit, required by the constraints): assert that for a known
    AOP fixture and a known LE fixture, the schema-aware import flow produces a frame
    **identical** to the current default loader output on the same fixture (the default path is
    retained for known files, so this asserts the known-file path is unchanged). Use the
    existing in-repo fixtures (`tests/aop_fixtures.py`, `tests/le_fixtures.py`) and
    `pandas.testing.assert_frame_equal`. Also assert AC2 end-to-end: a non-matching header set
    surfaces the mismatch report and offers manual-match / build options.
  - Acceptance: parity test passes; no temp files/network/real DB.

- [x] [P4-T6] Update `quality-tiers.yml` to classify every new module.
  - Add: `src/gui/services/schema_service.py: T2`;
    `src/gui/presenters/column_matching_presenter.py: T2`;
    `src/gui/presenters/schema_builder_presenter.py: T2`;
    `src/gui/presenters/_schema_builder_state.py: T2`;
    `src/gui/widgets/column_matching_dialog.py: T3`;
    `src/gui/widgets/schema_builder_dialog.py: T3`;
    `src/gui/widgets/_schema_builder_tabs.py: T3`;
    `src/gui/widgets/_schema_builder_columns_tab.py: T3` (only if created);
    `src/gui/_schema_wiring.py: T4` (composition glue, sibling of `_import_dispatch_wiring`).
  - Acceptance: every new module has exactly one tier entry; the tier-classification stage
    would pass (no unclassified new project). Tiers match spec section "API/CLI Surface"
    (service/presenters T2; widgets T3).

- [x] [P4-T7] Run the per-phase Python toolchain loop for Phase 4 and confirm green.
  - Command sequence (restart on failure/auto-fix): `poetry run black .` →
    `poetry run ruff check .` → `poetry run pyright` →
    `poetry run pytest tests/gui --cov-branch --cov-report=term-missing`
  - Acceptance: all stages green in one pass; the full GUI suite (existing + new) passes.

### Phase 5 — Final QA Loop, Coverage Delta, Regression & Issue Mirror

- [x] [P5-T1] Run the final Black formatting gate.
  - Command: `poetry run black --check .`
  - Acceptance: `evidence/qa-gates/final-black.<ISO-8601>.md` with `Timestamp:`, `Command:`,
    `EXIT_CODE:`, `Output Summary:`. If this reformats or fails, restart the loop at P5-T1.

- [x] [P5-T2] Run the final Ruff lint gate.
  - Command: `poetry run ruff check .`
  - Acceptance: `evidence/qa-gates/final-ruff.<ISO-8601>.md` with the four schema fields;
    error count 0. On failure/auto-fix, restart at P5-T1.

- [x] [P5-T3] Run the final Pyright strict gate.
  - Command: `poetry run pyright`
  - Acceptance: `evidence/qa-gates/final-pyright.<ISO-8601>.md` with the four schema fields;
    0 errors; no new suppressions beyond pre-authorized patterns. On failure, fix and restart
    at P5-T1.

- [x] [P5-T4] Run the final Pytest + coverage gate (coverage mode mandatory).
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `evidence/qa-gates/final-pytest.<ISO-8601>.md` with `Timestamp:`, `Command:`,
    `EXIT_CODE:`, and `Output Summary:` recording passed-test count, post-change total line
    coverage %, and post-change total branch coverage % (numeric). On failure/auto-fix,
    restart at P5-T1.

- [x] [P5-T5] Record the coverage-delta / threshold verification artifact.
  - Compare P0-T5 baseline against P5-T4 post-change values, and report new/changed-code
    coverage for the new presenter/service modules
    (`src/gui/services/schema_service.py`, `src/gui/presenters/column_matching_presenter.py`,
    `src/gui/presenters/schema_builder_presenter.py`,
    `src/gui/presenters/_schema_builder_state.py`).
  - Acceptance: `evidence/qa-gates/coverage-delta.<ISO-8601>.md` reports baseline coverage,
    post-change coverage, and new-code coverage; new presenter/service code meets >= 85% line
    and >= 75% branch; no regression on changed lines. If any required value is unavailable,
    the outcome is remediation-required (NOT PASS).

- [x] [P5-T6] Run the THIS-feature protected-files regression check.
  - Command: `git status --porcelain` and
    `git diff --name-only HEAD -- src/normalize_le.py src/load_aop.py src/load_skulu.py "src/mix_*.py" "src/etl_*.py" src/calculator.py "src/mix_pipeline*.py" "src/schema_*.py" "src/_schema_*.py" "src/_load_aop_helpers.py"`
  - Acceptance: `evidence/regression-testing/protected-files.<ISO-8601>.md` with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, `Output Summary:` showing an empty diff for the protected
    CLI/transform/loader and Feature A/B/C paths (no THIS-feature modification). Edits to
    `app.py`/`pipeline_service.py`/`protocols.py`/`main_window.py` are expected and listed
    separately as additive. A non-empty protected-path diff is a Blocking finding.

- [x] [P5-T7] Mirror the issue-update record for issue #44.
  - Acceptance: `evidence/issue-updates/issue-44.<ISO-8601>.md` with `Timestamp:`, the exact
    text intended/posted, and `PostedAs:` (`body`, `comment`, or `unknown`); if not posted,
    a `POSTING BLOCKED` header and reason. Per the conventions skill.

## Test Plan

- **Unit (no QApplication):** `SchemaService` (P1-T3); `ColumnMatchingPresenter` and
  `SchemaBuilderPresenter`/`_schema_builder_state` (P2-T5), covering positive flows, negative
  flows (invalid/unsafe/unknown-column formulas via Feature C), and structural validation.
- **Widget (pytest-qt, offscreen):** `ColumnMatchingDialog` (P3-T3) and `SchemaBuilderDialog`
  + tab helpers (P3-T4).
- **Composition / integration (pytest-qt, offscreen):** schema-builder action + import-flow
  discovery wiring (P4-T4); end-to-end schema import with the AC1 known-file parity assertion
  and the AC2 no-match path (P4-T5).
- **Regression:** full existing GUI suite stays green (P4-T7); protected CLI/transform/loader
  and Feature A/B/C paths unchanged (P5-T6).
- **Coverage evidence:**
  - Baseline: `evidence/baseline/baseline-pytest.<ISO-8601>.md` (total line + branch %).
  - Post-change: `evidence/qa-gates/final-pytest.<ISO-8601>.md` (total line + branch %).
  - Delta/new-code: `evidence/qa-gates/coverage-delta.<ISO-8601>.md`
    (>= 85% line / >= 75% branch on new presenter/service code; no regression on changed lines).

## Acceptance-Criteria Traceability (AC1–AC9)

- AC1 → P4-T1, P4-T3, P4-T5 (known-file parity asserted).
- AC2 → P4-T3, P4-T4, P4-T5.
- AC3 → P2-T2, P2-T5, P3-T1, P3-T3.
- AC4 → P2-T3, P2-T5, P3-T2, P3-T4.
- AC5 → P2-T3 (FormulaEvaluator), P2-T5, P3-T2, P3-T4.
- AC6 → P4-T2, P4-T3, P4-T4.
- AC7 → P2-T5 (no QApplication), P3-T3/T4 + P4-T4/T5 (pytest-qt).
- AC8 → P5-T1..T5 (Black/Ruff/Pyright/coverage), P4-T6 (quality-tiers).
- AC9 → P4-T1/T2/T3 (additive), P4-T7 (suite green), P5-T6 (protected-files regression).

## Open Questions / Notes

- Discovery acceptance threshold: reuse the Feature B default (`DEFAULT_THRESHOLD` already
  drives `find_best_match_in_registry`) and treat `MatchResult.score` against the documented
  acceptance bar; do not introduce a new threshold constant. If the acceptance bar is
  ambiguous at execution time, STOP and escalate rather than guessing.
- If `protocols.py` would exceed 500 lines after adding the two protocols, STOP and escalate
  before splitting (the existing four protocols must not move).
- Any seemingly unavoidable Pyright suppression: STOP and escalate per
  `.claude/rules/python-suppressions.md` (try >= 5 distinct approaches first).
