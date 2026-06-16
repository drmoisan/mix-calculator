# Feature Audit: schema-builder-ux-overhaul (Issue #72)

**Audit Date:** 2026-06-16
**Feature Folder:** `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72`
**Base Branch:** `main`
**Head Branch:** `feat/schema-builder-ux-overhaul-72`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `0a47fef2869b97d8a290d33570ebeee834c80987`)
- **Head branch/commit:** `feat/schema-builder-ux-overhaul-72` (commit `c6a9f955355ac7cc9866fc8ba11f718aa8e7a5ae`)
- **Merge base:** `0a47fef2869b97d8a290d33570ebeee834c80987`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/evidence/**`
  - Additional evidence: reviewer-independent toolchain run (Black/Ruff/Pyright/Pytest) and regenerated `artifacts/python/lcov.info`
- **Feature folder used:** `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72`
- **Requirements source:** `spec.md` (AC-1..AC-11) and `user-story.md` (full-feature mode)
- **Work mode resolution note:** `issue.md` declares `- Work Mode: full-feature`, resolving AC sources to `spec.md` and `user-story.md`.
- **Scope note:** The reviewer verified the live branch head matches the PR-context head SHA (`c6a9f95`); the summary is current. Scope is the full feature-vs-base diff.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/spec.md` — primary source (AC-1..AC-11)
- `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/user-story.md` — secondary source (8 user-facing criteria)

### From spec.md

1. **AC-1** The schema-builder window can be resized vertically and horizontally and retains min/max/close controls; the user can size below the default.
2. **AC-2** The Identity description is a multi-line widget that wraps text and grows/shrinks vertically with the window; identity get/set round-trips multi-line text.
3. **AC-3** Derived rows render and parse as `name = expression`; an existing `name|expression` is no longer produced.
4. **AC-4** Displayed derived expressions wrap known column references as `[Name]` with the comma separator outside the brackets; stored/validated expressions use `col("Name")` and the formula engine grammar is unchanged.
5. **AC-5** In the New-derived dialog, double-clicking an available column name inserts the bracketed name at the cursor in the expression input.
6. **AC-6** The Columns tab has a row-number chooser; changing it updates each canonical row to show the chosen source row's assigned value to the right of the blue object instead of the dtype checkmark; only masked values are shown.
7. **AC-7** The Key tab is a multi-select of declared canonical columns; selecting columns composes the key and round-trips through `KeySpec` with the model/loader unchanged.
8. **AC-8** The Dedup tab offers an `auto` mode; selecting it does not require a discriminator, and the assembled/loaded schema groups by `dimension` columns and sums `measure` columns; existing modes and the LE explicit path are unchanged.
9. **AC-9** The Preview tab renders the result table from the configured tabs against the masked preview slice using a tabular widget.
10. **AC-10** When a required input is missing or assembly fails, the Preview tab shows a specific message identifying what is missing rather than rendering nothing.
11. **AC-11** Full toolchain passes (Black → Ruff → Pyright → Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines; all production and test files remain <= 500 lines.

### From user-story.md

1. The schema-builder window can be resized vertically as well as horizontally.
2. The Identity description wraps across multiple lines and resizes with the window.
3. The Derived tab renders/parses `name = expression` and brackets column refs with the comma outside the brackets.
4. Double-clicking a column name in the New-derived dialog inserts the bracketed name into the expression.
5. The Columns tab has a row-number chooser that updates every field's displayed value; the value is shown to the right of the blue object instead of a checkmark.
6. The Key tab purpose is resolved (removed/repurposed) per the agreed design; key authored via Derived and assigned via Columns where decided.
7. The Dedup tab purpose is resolved (groupby on non-value assignments) per the agreed design.
8. The Preview tab renders the result table from the configured tabs and reports specific missing inputs.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| AC-1 | Resizable window, sizable below default, min/max/close | PASS | `_schema_builder_window_setup.py` change; `test_dialog_is_resizable_top_level_window_below_default` | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_builder_dialog.py` | Window-flag fix verified by test. |
| AC-2 | Identity multi-line wrap + round-trip | PASS | `QPlainTextEdit` swap in dialog; `test_identity_description_round_trips_multi_line_text`, `test_identity_description_is_wrapping_multiline_widget` | `poetry run pytest tests/gui/test_schema_builder_dialog.py` | `tuple[str,str,str]` contract preserved. |
| AC-3 | Derived `name = expression`, no `\|` | PASS | `test_derived_rows_render_with_equals_separator`, `test_derived_parse_splits_on_first_equals_only` | `poetry run pytest tests/gui/test_schema_builder_dialog.py` | Pipe separator removed. |
| AC-4 | Display `[Name]`, store `col("Name")`, grammar unchanged | PASS | `_schema_builder_derived_format.py` (new); `tests/gui/test_schema_builder_derived_format.py` (8 tests incl. names-with-spaces, evaluator-validates-stored-form) | `poetry run pytest tests/gui/test_schema_builder_derived_format.py` | D-1 verified: no formula-engine file in diff. |
| AC-5 | Double-click inserts bracketed name at cursor | PASS | `_derived_formula_dialog.py:_on_column_double_clicked`; `test_double_click_inserts_bracketed_name`, `test_double_click_inserts_at_cursor_position` | `poetry run pytest tests/gui/test_derived_formula_dialog.py` | Drives real `itemDoubleClicked` signal. |
| AC-6 | Columns row chooser shows masked value, not dtype glyph | PASS | `_columns_tab_presenter.py`, `_columns_tab_protocol.py:set_value_display`; `test_set_preview_row_*`, `test_set_value_display_routes_masked_value_to_row` | `poetry run pytest tests/gui/test_columns_tab_presenter.py tests/gui/test_columns_tab_widgets.py` | Values sourced from masked `PreviewSlice.rows`. |
| AC-7 | Key tab multi-select composes ordered `column-ref` `KeySpec`; model/loader unchanged | PASS | `_key_multiselect_widget.py` (new); `test_key_multiselect_composes_ordered_column_ref_keyspec`, `test_key_multiselect_round_trips_through_assemble_schema`, `test_live_key_tab_is_multiselect_with_seeded_selection` | `poetry run pytest tests/gui/test_schema_builder_dialog.py tests/gui/test_schema_builder_dialog_live.py` | D-2 verified: zero `KeySpec`/`KeyPart` changes in `_schema_model_specs.py` diff. |
| AC-8 | Dedup `auto`: no discriminator, dimension-groupby/measure-sum; LE path unchanged | PASS | `_schema_loader_auto_dedup.py` (new), `_schema_model_specs.py` (auto mode); `test_le_explicit_select_from_dedup_unchanged`, `test_aggregate_still_requires_discriminator_after_auto_added`, `test_dedup_auto_assembles_without_discriminator` | `poetry run pytest tests/test_schema_loader_dedup.py tests/gui/test_schema_builder_dialog_dedup.py` | D-3 verified: invariant relaxed for `auto` only. |
| AC-9 | Preview renders result table from masked slice via tabular widget (wired production path) | PASS | `_schema_preview_table.py` (new), `_schema_open_helpers.py:install_preview_refresh_handler` (calls `update_preview`), wired from `_schema_wiring.py:open_schema_builder`; `test_live_preview_tab_renders_table_from_masked_slice` drives the real `currentChanged` seam | `poetry run pytest tests/gui/test_schema_builder_dialog_live.py` | Production call site verified by grep; integration test, not a direct `update_preview` unit call. |
| AC-10 | Missing-input/assembly-failure shows specific message | PASS | `test_live_preview_shows_no_source_message_for_blank_slice`, `test_live_preview_shows_specific_missing_input_message` | `poetry run pytest tests/gui/test_schema_builder_dialog_live.py` | Surfaces `SchemaValidationError` text. |
| AC-11 | Toolchain green; coverage thresholds; <= 500 lines | PASS | Reviewer independent run: Black 255 unchanged, Ruff clean, Pyright 0 errors, Pytest 1085 passed; coverage 99.04% line / 93.43% branch; all 32 changed files <= 494 lines | `poetry run black --check .`; `poetry run ruff check .`; `poetry run pyright`; `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch` | File-size cap independently re-scanned with `awk NR`. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 11 criteria (AC-1..AC-11) plus all 8 user-story criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Optional: add a render-branch test to `_schema_preview_table.py` to create headroom above the 85%/75% floor.
2. None required for merge.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All AC-1..AC-11 in `spec.md` evaluated PASS and are already checked off (`[x]`) in the source file; no change was required.
- All 8 user-story criteria evaluated PASS and are already checked off (`[x]`) in `user-story.md`; no change was required.
- No PARTIAL/FAIL/UNVERIFIED items remain.

### AC Status Summary

- Source: `spec.md` and `user-story.md`
- Total AC items: 19 (11 spec + 8 user-story)
- Checked off (delivered): 19
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 11 | 11 | 0 | Checkbox-backed; all already `[x]`, all verified PASS |
| `user-story.md` | 8 | 8 | 0 | Checkbox-backed; all already `[x]`, all verified PASS |

No source-file checkbox change was made because every criterion was already checked off by the executor and all are confirmed PASS by this audit.
