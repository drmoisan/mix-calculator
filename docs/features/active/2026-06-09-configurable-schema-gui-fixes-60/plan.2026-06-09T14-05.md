# Atomic Implementation Plan — configurable-schema-gui-fixes (Issue #60)

- **Issue:** #60
- **Work Mode:** full-bug (spec-driven; `spec.md` required, `user-story.md` absent by design)
- **Spec (authoritative AC source):** `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/spec.md` (AC-1..AC-13)
- **Research:** `artifacts/research/configurable-schema-gui-fixes-60.md`
- **Issue context:** `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/issue.md`
- **Plan timestamp:** 2026-06-09T14-05
- **Feature folder (`<FEATURE>`):** `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60`
- **Evidence root (canonical, non-overridable):** `<FEATURE>/evidence/<kind>/`

## Scope Summary

Three bundled defects, sequenced per research order (defect 3 → defect 2 → defect 1):

- **Defect 3 (P1):** header-row-aware discovery in `src/gui/presenters/source_selection_presenter.py` — raise `_HEADER_PREVIEW_ROWS` from `1` to `5`, add `_best_header_row` helper that scores each preview row via `service.find_best_match` and selects the highest (earliest row wins ties), fall back to `rows[0]` when no row matches a schema. Must not regress LE (`LE-8 + 4`) or SKU_LU (`SKU_LU`) on row 0; must not crash when the first preview row is blank (#50 guard).
- **Defect 2 (P2):** add `src/schemas/default_sku_lu.schema.json`; flip `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` in `src/gui/_schema_provider_factory.py` from `None` to `"default_sku_lu"`. Country-code mapping stays loader-only (out of scope).
- **Defect 1 (P3):** add "Edit Schema" button + `edit_schema_requested` signal in `src/gui/widgets/source_input_widget.py` (extract construction/gating helpers to `src/gui/widgets/_source_input_button_wiring.py` to stay under 500 lines); add `wire_edit_schema_buttons` in `src/gui/_schema_wiring.py`; call it from `src/gui/_schema_discovery_wiring.py`.
- **Cross-cutting (P4):** classify the five touched-but-unclassified modules in `quality-tiers.yml`; repo-wide 500-line scan; final full toolchain + coverage gate.

## Verified preconditions (read at plan time)

- `src/gui/widgets/source_input_widget.py` is 497/500 lines — extraction is mandatory for Defect 1 (AC-12).
- The following five modules are absent from `quality-tiers.yml` (grep returned no matches) and exist on disk; all must be classified (AC-10):
  `src/gui/widgets/_source_input_button_wiring.py` (T4), `src/gui/_schema_discovery_wiring.py` (T4), `src/gui/_schema_provider_factory.py` (T4), `src/gui/_schema_activation.py` (T2), `src/_header_detection.py` (T2).
- `src/gui/presenters/source_selection_presenter.py` and `src/gui/widgets/source_input_widget.py` and `src/gui/_schema_wiring.py` are already classified (T2/T3/T4 respectively); no new entry needed for those.

## Constraints (enforced on every implementation task)

- **Python toolchain loop, in order, restart on any failure/auto-fix:** `poetry run black .` → `poetry run ruff check .` → `poetry run pyright` → `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Coverage gates: line >= 85%, branch >= 75%, no regression on changed lines.
- **500-line cap on production AND test files.** Each phase that adds/changes `.py` files ends with a cap-scan task.
- **GUI/Qt tests headless-safe.** Tests drive guard/placeholder/no-file/no-sheet/blank-first-row paths, not only the happy path (#50 activation-seam lesson). Offscreen Qt platform (`QT_QPA_PLATFORM=offscreen`) for the Ubuntu runner.
- **No new third-party dependency. No change to legacy CLI loaders or `load_skulu` country-code mapping.**
- **Worker batch budget:** group implementation+test handoffs to the python-typed-engineer at <= 3 production + 3 test files per batch.
- **Evidence path is non-overridable:** all artifacts under `<FEATURE>/evidence/<kind>/`. Any supplied `artifacts/baselines|qa|coverage|evidence/...` path is rejected and substituted.

## AC Coverage Map

| AC | Phase.Tasks |
|----|-------------|
| AC-1  | P3-T1, P3-T2, P3-T5 |
| AC-2  | P3-T3, P3-T4, P3-T6 |
| AC-3  | P3-T1, P3-T3, P3-T5, P3-T6 |
| AC-4  | P2-T1, P2-T3 |
| AC-5  | P2-T2, P2-T3, P2-T4 |
| AC-6  | P2-T1, P2-T3 (negative assertion: no value-map in schema) |
| AC-7  | P1-T2, P1-T3 |
| AC-8  | P1-T2, P1-T4 |
| AC-9  | P1-T2, P1-T4, P3-T6 |
| AC-10 | P4-T1 |
| AC-11 | P1-T4, P2-T4, P3-T6, P4-T3 |
| AC-12 | P1-T5, P2-T5, P3-T7, P4-T2 |
| AC-13 | P0-T4, P4-T3 |

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record evidence. Read `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/benchmark-baselines.md`, `.claude/rules/self-explanatory-code-commenting.md`. Write `<FEATURE>/evidence/baseline/phase0-instructions-read.2026-06-09T14-05.md` with fields `Timestamp:`, `Policy Order:`, and the explicit list of files read.
  - **DoD:** evidence artifact exists at the canonical path with all three required fields populated.

- [x] [P0-T2] Capture format/lint baseline. Run `poetry run black --check .` then `poetry run ruff check .`. Write `<FEATURE>/evidence/baseline/baseline-format-lint.2026-06-09T14-05.md` with `Timestamp:`, `Command:` (both commands), `EXIT_CODE:` (each), `Output Summary:` (pass/fail + counts).
  - **DoD:** artifact records both commands and exit codes; summary states clean-or-dirty status.

- [x] [P0-T3] Capture type-check baseline. Run `poetry run pyright`. Write `<FEATURE>/evidence/baseline/baseline-pyright.2026-06-09T14-05.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).
  - **DoD:** artifact records the command, exit code, and the diagnostic count summary.

- [x] [P0-T4] Capture test + coverage baseline. Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` with `QT_QPA_PLATFORM=offscreen`. Write `<FEATURE>/evidence/baseline/baseline-pytest-coverage.2026-06-09T14-05.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric headline line-coverage % and branch-coverage % and pass/fail counts.
  - **DoD:** artifact records numeric baseline line% and branch% (not placeholders) and the passed/failed test counts. This is the no-regression reference for AC-13.

---

### Phase 1 — Header-Row-Aware Discovery (Defect 3)

AC focus: AC-7, AC-8, AC-9 (with AC-11 no-regression, AC-12 cap, AC-13 toolchain).

- [x] [P1-T1] Raise the preview-row cap. In `src/gui/presenters/source_selection_presenter.py`, change the module constant `_HEADER_PREVIEW_ROWS` from `1` to `5` so the preview window includes the AOP1 header at index 2. Update the constant's docstring/comment to state the rationale (worst observed header offset).
  - **AC:** AC-7.
  - **DoD:** constant equals `5`; `poetry run black .` → `poetry run ruff check .` → `poetry run pyright` → `poetry run pytest --cov --cov-branch --cov-report=term-missing` all pass in one loop; restart on any failure/auto-fix.

- [x] [P1-T2] Add the best-header-row selector and route discovery through it. In `src/gui/presenters/source_selection_presenter.py`, add a private helper `_best_header_row(rows, service) -> list[str]` that iterates preview rows earliest-first, calls `service.find_best_match(row)`, tracks the highest score (earliest row wins ties), and returns `rows[0]` as a fallback when no row yields a schema match. In `on_schema_discovery`, replace `headers = rows[0]` with `headers = _best_header_row(rows, <schema service>)`. Preserve the existing blank/whitespace guard so a blank first preview row does not raise (AC-9). Add docstrings (purpose, args, returns, side effects) and the loop intent comment per commenting policy.
  - **AC:** AC-7, AC-8, AC-9.
  - **DoD:** `headers` is sourced from `_best_header_row`; the existing blank-row guard is intact; full Python loop passes in one pass.

- [x] [P1-T3] Add presenter unit tests for AOP1-style multi-row-header detection. In `tests/gui/test_source_selection_presenter.py`, add tests using `FakeWorkbookReader(preview_rows=[...])` with a synthetic AOP1-style preview (blank/stray rows at indices 0–1, the real AOP header tokens at index 2) asserting that discovery selects the index-2 row and activates the AOP schema. Use only injected fixtures — no `.xlsx`, no temp files, no computed workbook values. Set `QT_QPA_PLATFORM=offscreen` where Qt is constructed.
  - **AC:** AC-7.
  - **DoD:** new tests fail against the pre-change presenter intent and pass after P1-T1/P1-T2; full Python loop passes.

- [x] [P1-T4] Add presenter regression + guard tests for row-0 sources and blank first row. In `tests/gui/test_source_selection_presenter.py`, add tests asserting: (a) an LE-style single-correct-header preview (header tokens at index 0) still selects row 0 and activates LE; (b) a SKU_LU-style preview (header at index 0) still selects row 0; (c) a preview whose first row is blank does not raise and discovery completes; (d) a no-file/no-sheet/no-schema invocation does not crash (the existing guard path). Drive the guard paths, not only the happy path.
  - **AC:** AC-8, AC-9, AC-11.
  - **DoD:** all four scenarios pass; full Python loop passes; no regression vs. P0-T4 baseline coverage on changed lines.

- [x] [P1-T5] Phase-1 500-line cap scan. Scan every `.py` created/changed in Phase 1 (`src/gui/presenters/source_selection_presenter.py`, `tests/gui/test_source_selection_presenter.py`) for the 500-line cap; extract a helper module if any file exceeds 500 lines, then re-run the full Python loop. Write `<FEATURE>/evidence/qa-gates/phase1-line-cap.2026-06-09T14-05.md` with `Timestamp:`, `Command:` (the line-count command), `EXIT_CODE:`, `Output Summary:` (per-file line counts; all <= 500).
  - **AC:** AC-12.
  - **DoD:** artifact lists each changed Phase-1 `.py` with line count <= 500; if any extraction occurred, the full Python loop re-passes.

---

### Phase 2 — Default SKU_LU Schema + Provider Wiring (Defect 2)

AC focus: AC-4, AC-5, AC-6 (with AC-11 no-regression, AC-12 cap, AC-13 toolchain).

- [x] [P2-T1] Add the bundled SKU_LU schema file. Create `src/schemas/default_sku_lu.schema.json` mirroring the structure of `src/schemas/default_le.schema.json` and `src/schemas/default_aop.schema.json` and the `SchemaDefinition`/`ColumnSpec`/`KeySpec` model in `src/schema_model.py`: columns `SKU`, `SKU Description`, `Category`, `Country` (canonical order); `Country` carries `aliases: ["International"]`, all other columns `aliases: []`; key `parts: [{"kind": "column-ref", "value": "SKU"}]` with `sku_coercion: false`; `header_row: 0`; `dedup.mode: "none"` with null discriminator and empty measure aggregations; empty `derived_columns`, `fill_rules`, `drop_columns`; `source_sheet_hints: ["SKU_LU"]`. Do NOT encode any country-code value mapping (0→US, 1→Canada) — that stays loader-only (AC-6). Confirm `sku_coercion` serializes as `false` against `src/schema_model.py`.
  - **AC:** AC-4, AC-6.
  - **DoD:** file parses against the schema model (verified by P2-T3 test); no value-map field present; full Python loop passes.

- [x] [P2-T2] Flip the SKU_LU default-schema mapping. In `src/gui/_schema_provider_factory.py`, change `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` from `None` to `"default_sku_lu"`. No other key changes. This is the only code change for registry auto-discovery (the registry already scans `src/schemas/`).
  - **AC:** AC-5.
  - **DoD:** mapping value is `"default_sku_lu"`; full Python loop passes.

- [x] [P2-T3] Add schema-model parse + shape tests for `default_sku_lu`. In `tests/test_default_schemas.py`, add tests asserting: parses without error against the schema model; canonical column order `[SKU, SKU Description, Category, Country]`; `Country` has alias `International`; key is `SKU` with `sku_coercion is False`; `header_row == 0`; `dedup.mode == "none"`; `derived_columns`, `fill_rules`, `drop_columns` are empty; and explicitly assert there is no country-code value mapping encoded in the schema (AC-6 negative check).
  - **AC:** AC-4, AC-6.
  - **DoD:** tests pass; full Python loop passes.

- [x] [P2-T4] Add provider-factory + auto-discovery tests. In `tests/gui/test_schema_provider_factory.py`, update/add a test asserting `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"] == "default_sku_lu"`. Add (in the appropriate registry/dropdown test, e.g. `tests/test_default_schemas.py` or the existing registry-listing test) an assertion that `default_sku_lu` appears in the registry's listed bundled names so it surfaces in the dropdown at startup. Confirm LE/AOP default mappings are unchanged (no regression).
  - **AC:** AC-5, AC-11.
  - **DoD:** tests pass; LE/AOP mappings asserted unchanged; full Python loop passes.

- [x] [P2-T5] Phase-2 500-line cap scan. Scan every `.py` created/changed in Phase 2 (`src/gui/_schema_provider_factory.py`, `tests/test_default_schemas.py`, `tests/gui/test_schema_provider_factory.py`) for the cap; extract if any exceeds 500 lines; re-run the full Python loop. Write `<FEATURE>/evidence/qa-gates/phase2-line-cap.2026-06-09T14-05.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (per-file line counts; all <= 500). The JSON schema file is data, not subject to the .py cap, but record its presence.
  - **AC:** AC-12.
  - **DoD:** artifact lists each changed Phase-2 `.py` with line count <= 500.

---

### Phase 3 — Edit Schema Button + Extraction (Defect 1)

AC focus: AC-1, AC-2, AC-3 (with AC-9 guard reuse, AC-11 no-regression, AC-12 cap, AC-13 toolchain).
Ordering note: extraction (P3-T1) runs before adding new widget surface so `source_input_widget.py` never exceeds 500 lines mid-phase.

- [x] [P3-T1] Extract button construction/gating helpers to keep the widget under cap. In `src/gui/widgets/_source_input_button_wiring.py`, add `build_edit_schema_button() -> QPushButton` (constructs the disabled-by-default "Edit Schema" `QPushButton`) and `set_edit_enabled(button, enabled) -> None` (mirrors the existing `set_import_enabled`). Move enough existing widget construction/gating logic into this module so that after P3-T2 adds the new surface, `source_input_widget.py` stays <= 500 lines. Add docstrings (purpose, args, returns, side effects).
  - **AC:** AC-1, AC-3 (gating helper), AC-12 (extraction).
  - **DoD:** helpers exist with full docstrings; full Python loop passes.

- [x] [P3-T2] Add the Edit Schema button, signal, and property to the widget. In `src/gui/widgets/source_input_widget.py`: add `edit_schema_requested: Signal = Signal()`; construct `self._edit_schema_button` via `build_edit_schema_button()` (disabled at start); place it beside the per-input Import button in the layout; connect `self._edit_schema_button.clicked` → `self.edit_schema_requested.emit`; expose an `edit_schema_btn` property mirroring `build_schema_btn`/import-button exposure.
  - **AC:** AC-1.
  - **DoD:** button is present beside Import on all three source tabs (LE, AOP, SKU_LU); signal and property exist; full Python loop passes.

- [x] [P3-T3] Gate the Edit button on real-vs-placeholder selection. In `src/gui/widgets/source_input_widget.py`, update `_on_schema_changed` so that the existing `is_real_schema(name, _SCHEMA_PLACEHOLDER)` check also drives `set_edit_enabled(self._edit_schema_button, is_real)` — enabled only for a real schema, disabled on the placeholder `<Choose Schema>` or empty.
  - **AC:** AC-3.
  - **DoD:** Edit button enable state tracks the same gate as Import; full Python loop passes.

- [x] [P3-T4] Add the `wire_edit_schema_buttons` wiring function. In `src/gui/_schema_wiring.py`, add `wire_edit_schema_buttons(window, service, ...)` mirroring `wire_build_schema_buttons`: iterate the three `(key, widget)` pairs; for each, connect `widget.edit_schema_requested` to a closure that (a) reads `widget.current_schema()`, (b) short-circuits (return, no crash) if the name is the placeholder or empty, (c) opens the builder via the existing `open_schema_builder(window, service, ...)` path (without caller specs, so it opens blank and retains the presenter on `window.schema_builder_presenter`), then (d) calls `window.schema_builder_presenter.load_existing(name)` via `getattr` (the established `_seed_presenter` pattern) to seed the builder from the selected schema. Do not change `load_existing`'s contract or `open_schema_builder`.
  - **AC:** AC-2, AC-3.
  - **DoD:** closure opens-then-`load_existing` with the selected name and short-circuits on placeholder/empty; full Python loop passes.

- [x] [P3-T5] Call the new wiring from the composition root. In `src/gui/_schema_discovery_wiring.py`, have `wire_schema_discovery_and_gating` call `wire_edit_schema_buttons` alongside the existing `wire_build_schema_buttons` call. No other call-site changes.
  - **AC:** AC-1, AC-3.
  - **DoD:** Edit wiring is invoked from the same composition root as build wiring; full Python loop passes.

- [x] [P3-T6] Add widget + wiring tests for the Edit Schema path (incl. guard paths). Tests, headless-safe (`QT_QPA_PLATFORM=offscreen`):
  - In `tests/gui/test_source_input_widget.py`: Edit button is present on each source tab; disabled on the placeholder; enabled after a real schema is selected; emits `edit_schema_requested` on click.
  - In `tests/gui/test_edit_schema_wiring.py` (new) or `tests/gui/test_schema_discovery_wiring.py`: clicking Edit with a real schema opens the builder and calls `schema_builder_presenter.load_existing(<selected name>)`; invoking the closure with the placeholder or empty name short-circuits (no builder opens, no crash); a no-file/no-schema invocation does not crash (#50 seam).
  - **AC:** AC-1, AC-2, AC-3, AC-9, AC-11.
  - **DoD:** all listed scenarios pass including the placeholder/empty/no-file guard paths; full Python loop passes.

- [x] [P3-T7] Phase-3 500-line cap scan. Scan every `.py` created/changed in Phase 3 (`src/gui/widgets/source_input_widget.py`, `src/gui/widgets/_source_input_button_wiring.py`, `src/gui/_schema_wiring.py`, `src/gui/_schema_discovery_wiring.py`, `tests/gui/test_source_input_widget.py`, and the new/edited wiring test file) for the cap; extract further if any exceeds 500 lines; re-run the full Python loop. Write `<FEATURE>/evidence/qa-gates/phase3-line-cap.2026-06-09T14-05.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (per-file line counts; all <= 500, with explicit confirmation `source_input_widget.py <= 500`).
  - **AC:** AC-12.
  - **DoD:** artifact confirms `source_input_widget.py` and every other changed Phase-3 `.py` is <= 500 lines.

---

### Phase 4 — Tier Classification, Repo-Wide Cap Scan, and Final QA

AC focus: AC-10, AC-11, AC-12, AC-13.

- [x] [P4-T1] Classify the five touched-but-unclassified modules in `quality-tiers.yml`. Add `projects` entries (each with a tier-rationale comment per the file's existing convention): `src/gui/widgets/_source_input_button_wiring.py: T4`, `src/gui/_schema_discovery_wiring.py: T4`, `src/gui/_schema_provider_factory.py: T4`, `src/gui/_schema_activation.py: T2`, `src/_header_detection.py: T2`. Before editing, re-grep `quality-tiers.yml` to confirm none are already present; if any module is already classified, do not duplicate it and note the reconciliation. Confirm no unclassified `src/**` project remains by cross-checking against the source tree.
  - **AC:** AC-10.
  - **DoD:** all five entries present (or reconciled if pre-existing); tier-classification invariant holds (no unclassified project); `quality-tiers.yml` parses.

- [x] [P4-T2] Repo-wide 500-line cap scan on all changed/created files. Scan every production AND test `.py` created or changed across P1–P4 for the 500-line cap. Write `<FEATURE>/evidence/qa-gates/final-line-cap.2026-06-09T14-05.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` listing each changed `.py` with its line count and an explicit `ALL <= 500` (or per-file remediation note). If any file exceeds 500 lines, extract and re-run the full Python loop before proceeding.
  - **AC:** AC-12.
  - **DoD:** artifact enumerates every changed `.py` <= 500 lines.

- [x] [P4-T3] Final full toolchain + coverage gate. Run, in order, restarting on any failure/auto-fix: `poetry run black .`, `poetry run ruff check .`, `poetry run pyright`, `poetry run pytest --cov --cov-branch --cov-report=term-missing` (with `QT_QPA_PLATFORM=offscreen`). Write one final-QC artifact per command step under `<FEATURE>/evidence/qa-gates/`:
  - `final-qc-black.2026-06-09T14-05.md`, `final-qc-ruff.2026-06-09T14-05.md`, `final-qc-pyright.2026-06-09T14-05.md`, `final-qc-pytest-coverage.2026-06-09T14-05.md`.
  - Each artifact: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. The pytest artifact MUST record numeric post-change line% and branch% and the delta vs. the P0-T4 baseline, and confirm no regression on changed lines (line >= 85%, branch >= 75%).
  - **AC:** AC-11, AC-13.
  - **DoD:** all four command steps exit 0; numeric post-change coverage recorded and >= thresholds with no changed-line regression vs. baseline; no `EXIT_CODE: SKIPPED`.

---

## Final QA Loop Note

If any final-QC step (P4-T3) fails or auto-fixes files, restart the full loop (format → lint → type-check → test) from the top until a single clean pass completes. Coverage evidence must contain numeric values, not placeholders; if coverage values are unavailable, the outcome is remediation-required and MUST NOT be reported as PASS.
