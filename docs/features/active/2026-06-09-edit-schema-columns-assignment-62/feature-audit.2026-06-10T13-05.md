# Feature Audit: edit-schema-columns-assignment Cycle-1 (#62)

**Audit Date:** 2026-06-10
**Feature Folder:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/`
**Base Branch:** `main`
**Head Branch:** `fix/edit-schema-columns-assignment`
**Work Mode:** `minor-audit`
**Audit Type:** Post-remediation acceptance verification (cycle-1 R4)

---

## Scope and Baseline

- **Base branch:** `main` (commit `f7aea0f00475594e254adbd2d17535628713d35c`)
- **Head branch/commit:** `fix/edit-schema-columns-assignment` (commit `150d42afdb7bc0aae7cca8794b8d707b277c2501`)
- **Merge base:** `f7aea0f00475594e254adbd2d17535628713d35c`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` (cross-checked against live `git diff f7aea0f...150d42a`)
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/**`
  - Additional evidence: refreshed `artifacts/python/lcov.info` (full-suite run this audit)
- **Feature folder used:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/`
- **Requirements source:** `issue.md` `## Acceptance Criteria` (minor-audit).
- **Work mode resolution note:** `issue.md` carries `- Work Mode: minor-audit`; the explicit `## Acceptance Criteria` section (AC-1..AC-9) is the sole authoritative AC source.
- **Scope note:** Full branch-vs-base audit. The branch spans cycle-0 (alias-seeding) and cycle-1 (real production fix). Head SHA verified against the caller-supplied head via `git rev-parse HEAD`; the live diff was used as the authoritative scope. No scope narrowing was attempted by the caller.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/issue.md` — only source (minor-audit)

### Acceptance criteria

1. AC-1: After `SchemaBuilderPresenter.load_existing(name)`, each canonical column that carries a persisted alias renders as assigned to that alias on the Columns tab — `view.set_assignment(canonical, <alias>)` is called with the persisted source column, not `None`.
2. AC-2: A canonical column loaded with no persisted alias renders unassigned (`set_assignment(canonical, None)`).
3. AC-3: The existing blank "Build new schema" path and the seeded per-tab "Build/Edit schema" path that supplies a live `preview_slice` keep their current fuzzy-prepopulation behavior with no regression (a live source pool still drives matching; persisted-alias seeding does not override or duplicate a live match, and the one-source-per-row consumption invariant holds).
4. AC-4: An edit-then-save round-trip through the builder preserves the persisted assignments (the saved schema's column aliases are retained).
5. AC-5: When the per-tab "Edit Schema" button opens the builder for a tab that has a selected workbook file and worksheet, the Columns tab's "Source columns" pool is populated with that worksheet's actual header columns (read via the same workbook-reader + best-header-row path the schema discovery flow uses, honoring the detected header row).
6. AC-6: With the source pool populated (AC-5), each canonical column of the loaded schema that matches a worksheet header (by name, persisted alias, or the existing fuzzy threshold) renders as assigned to that source column on the Columns tab — i.e. editing `default_aop` against the AOP worksheet shows Customer→Customer, SKU #→SKU #, Jan→Jan, etc., not "(unassigned)".
7. AC-7: The Columns tab is vertically scrollable so all canonical column rows are reachable when they exceed the visible height (the AOP schema has 26 columns).
8. AC-8: The Schema Builder window is resizable and exposes the standard minimize and maximize/restore window controls (in addition to close).
9. AC-9: The Edit Schema path degrades gracefully when no file/worksheet is selected (no crash; the builder opens with an empty source pool rather than raising), preserving the issue #50 no-file/no-sheet seam guard.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC-1 persisted alias renders assigned | PASS | `_seed_from_persisted_aliases` in `_columns_tab_presenter.py`; `test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool` asserts `consumed_columns == {Customer: cust_col, Sales: sales_amt}`. | `pytest tests/gui/test_columns_tab_presenter.py` | Retained cycle-0 fallback. |
| 2 | AC-2 alias-free row unassigned | PASS | `test_prepopulate_leaves_alias_free_row_unassigned_empty_pool` asserts `(Sales, None)` and `Sales not in consumed_columns`. | `pytest tests/gui/test_columns_tab_presenter.py` | |
| 3 | AC-3 live-match-wins, no regression, one-source-per-row | PASS | `test_live_fuzzy_match_wins_over_persisted_alias` asserts live source wins over persisted alias and consumed sources are distinct; seed pass runs strictly after the live pass. | `pytest tests/gui/test_columns_tab_presenter.py` | Build/Edit path unchanged; no source-pool reflection of seeded alias. |
| 4 | AC-4 edit-save round-trip preserves aliases | PASS | Aliases are loaded into column rows by `_state_from_schema` and read back via `get_columns`; `test_schema_builder_presenter_core.py` exercises load_existing render and round-trip. Aliases are never mutated by the seed pass (documented in `_seed_from_persisted_aliases`). | `pytest tests/gui/test_schema_builder_presenter_core.py` | |
| 5 | AC-5 Edit populates pool from real worksheet headers | PASS | `read_worksheet_header_columns` (reader + `best_header_row`, honoring detected header row); `test_edit_populates_preview_slice_from_real_worksheet_headers` asserts seeded slice header == ("Customer","SKU","Jan"). Wired at `app.py:424`→`wire_edit_schema_buttons`→`_build_edit_preview_slice`. | `pytest tests/gui/test_edit_schema_wiring.py tests/gui/test_worksheet_header_columns.py` | Production reachability verified (composition root passes the three presenters). |
| 6 | AC-6 matching rows render assigned (rendered state) | PASS | `test_edit_renders_matching_canonical_rows_as_assigned` drives real `SchemaBuilderDialog`+`SchemaBuilderPresenter`, resolves the live `ColumnsTabWidget` via `findChild`, asserts `row_assignment_text("Customer")=="Customer"`, `"SKU"`, `"Jan"`. | `pytest tests/gui/test_edit_schema_wiring.py` | Asserted against rendered widget label, not internal presenter state. |
| 7 | AC-7 Columns tab vertically scrollable | PASS | `build_columns_tab` wraps `ColumnsTabWidget` in `QScrollArea` with `setWidgetResizable(True)`; `tests/gui/test_schema_builder_dialog.py` verifies scroll-area presence. | `pytest tests/gui/test_schema_builder_dialog.py` | Inner widget still referenced so binder wiring is unaffected. |
| 8 | AC-8 window resizable with min/max/restore | PASS | `apply_schema_builder_window_flags` sets `Qt.Window | Min | Max | Close` and a default size; applied in `SchemaBuilderDialog.__init__`; `tests/gui/test_schema_builder_dialog.py` verifies window flags. | `pytest tests/gui/test_schema_builder_dialog.py` | Extracted to keep dialog under 500 lines. |
| 9 | AC-9 graceful no-file/no-sheet degradation | PASS | `test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call` asserts `reader.preview_calls == []` and seeded slice `[None]`; placeholder short-circuit and all-tabs no-schema seam tests. | `pytest tests/gui/test_edit_schema_wiring.py` | Reader never called with blank sheet; issue #50 seam preserved. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 9 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. None required for acceptance. Optional: a manual smoke of editing `default_aop` against a real AOP worksheet in a desktop session to visually confirm AC-6/AC-7/AC-8 (automated offscreen tests already cover the behavior).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** may be checked off in the authoritative source file(s) if they are markdown checkboxes and not already checked.
- Criteria evaluated as **PARTIAL**, **FAIL**, or **UNVERIFIED** must remain unchecked.

All nine AC items (AC-1..AC-9) are evaluated PASS and are already represented as checked `[x]`
checkboxes in `issue.md` (the executor checked them off as each task passed verification). This
audit confirms each check-off is supported by evidence; no checkbox state change was required.

### AC Status Summary

- Source: `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/issue.md`
- Total AC items: 9
- Checked off (delivered): 9
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 9 | 9 | 0 | Checkbox-backed; all confirmed PASS with evidence this audit. |
