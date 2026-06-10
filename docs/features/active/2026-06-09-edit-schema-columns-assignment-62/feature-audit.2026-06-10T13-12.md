# Feature Audit: edit-schema-columns-assignment (#62, Cycle 1 re-audit R4)

**Audit Date:** 2026-06-10
**Feature Folder:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62`
**Base Branch:** `main`
**Head Branch:** `fix/edit-schema-columns-assignment`
**Work Mode:** `minor-audit`
**Audit Type:** Post-remediation acceptance verification (cycle 1)

---

## Scope and Baseline

- **Base branch:** `main` (commit `f7aea0f00475594e254adbd2d17535628713d35c`)
- **Head branch/commit:** `fix/edit-schema-columns-assignment` (commit `150d42afdb7bc0aae7cca8794b8d707b277c2501`)
- **Merge base:** `f7aea0f00475594e254adbd2d17535628713d35c`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` and reviewer-run `git diff f7aea0f..150d42a`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/**`
  - Additional evidence: reviewer-run Black/Ruff/Pyright/Pytest output, `artifacts/python/lcov.info`
- **Feature folder used:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62`
- **Requirements source:** `issue.md` (`## Acceptance Criteria`, AC-1..AC-9)
- **Work mode resolution note:** `issue.md` carries an explicit `- Work Mode: minor-audit` marker; AC source is the explicit `## Acceptance Criteria` section in `issue.md` only.
- **Scope note:** Full branch-vs-base audit. No scope narrowing was applied. The critical-verification focus was the real production behavior (AC-5/AC-6 call-site wiring), verified through the composition root and an end-to-end render test, not only fakes.

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
| 1 | AC-1 persisted alias renders assigned | PASS | `_columns_tab_presenter._seed_from_persisted_aliases` seeds `consumed_columns[canonical]=aliases[0]` for unassigned alias-carrying rows; `test_columns_tab_presenter.py` asserts assignment. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_columns_tab_presenter.py` | Cycle-0 behavior retained. |
| 2 | AC-2 no-alias renders unassigned | PASS | Seeder skips rows with empty `aliases`; row renders `(unassigned)`. | same as AC-1 | Verified by inspection + retained tests. |
| 3 | AC-3 live fuzzy path no regression; one-source-per-row | PASS | Seeder runs strictly after the live fuzzy pass and skips rows already in `consumed_columns` (live-match-wins); seeds at most one alias per row. | `poetry run pytest tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py` | Invariant preserved. |
| 4 | AC-4 edit-then-save preserves aliases | PASS | Round-trip retains column aliases; covered by presenter-core tests. | `poetry run pytest tests/gui/test_schema_builder_presenter_core.py` | No change to save path. |
| 5 | AC-5 Edit pool from real worksheet headers | PASS | `wire_edit_schema_buttons -> _build_edit_preview_slice -> read_worksheet_header_columns` reuses `best_header_row` (honors detected header row) and passes a `preview_slice` into `open_schema_builder`; `app.py` supplies the reader-carrying presenters. | `poetry run pytest tests/gui/test_edit_schema_wiring.py::test_edit_populates_preview_slice_from_real_worksheet_headers` | Production call site verified (`app.py:330-343,424-431`). |
| 6 | AC-6 matching canonical rows render assigned | PASS | End-to-end test drives real `SchemaBuilderDialog`+`SchemaBuilderPresenter`+`DragTabBinder`, emits real `edit_schema_requested`, asserts `row_assignment_text("Customer")=="Customer"` etc. | `poetry run pytest tests/gui/test_edit_schema_wiring.py::test_edit_renders_matching_canonical_rows_as_assigned` | Verifies the user-facing render, not a fake. |
| 7 | AC-7 Columns tab vertically scrollable | PASS | `build_columns_tab` wraps `ColumnsTabWidget` in `QScrollArea(setWidgetResizable(True))`. | `poetry run pytest tests/gui/test_columns_tab_widgets.py` | Bundle still exposes the real widget; binder unaffected. |
| 8 | AC-8 resizable window with min/max/restore | PASS | `apply_schema_builder_window_flags` sets `Window | Minimize | Maximize | Close` hints + default size; applied in `SchemaBuilderDialog.__init__`. | `poetry run pytest tests/gui/test_schema_builder_dialog.py` | New module keeps dialog under 500 lines. |
| 9 | AC-9 graceful no-file/no-sheet seam | PASS | `read_worksheet_header_columns` returns `()` (no reader call) on blank path/sheet; `_build_edit_preview_slice` returns `None`; handler completes without raising. | `poetry run pytest tests/gui/test_edit_schema_wiring.py::test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call` | Issue #50 seam preserved; `reader.preview_calls == []`. |

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

1. None required for acceptance. Optional: manual run against the real AOP workbook to visually confirm the 26-column scroll and Customer→Customer mapping (the end-to-end automated test already covers the render path).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, all nine criteria evaluate to PASS. They are already checked `[x]` in `issue.md` (the executor checked them during delivery), and this audit confirms each PASS verdict, so no checkbox state change is required.

### AC Status Summary

- Source: `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/issue.md`
- Total AC items: 9
- Checked off (delivered): 9
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 9 | 9 | 0 | Checkbox-backed; all AC-1..AC-9 confirmed PASS this cycle. No state change needed (already `[x]`). |

No source-file checkbox change was made because all nine items were already checked and this audit confirms each PASS verdict.
