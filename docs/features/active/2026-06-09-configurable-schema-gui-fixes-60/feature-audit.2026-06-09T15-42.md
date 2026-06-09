# Feature Audit: configurable-schema-gui-fixes (Issue #60)

**Audit Date:** 2026-06-09
**Feature Folder:** `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/`
**Base Branch:** `main`
**Head Branch:** `fix/configurable-schema-gui-fixes`
**Work Mode:** `full-bug`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `1d27514`)
- **Head branch/commit:** `fix/configurable-schema-gui-fixes` (commit `4856661`)
- **Merge base:** `1d27514`
- **Evidence sources:**
  - Primary: live diff `1d27514...4856661` (the PR context summary at `artifacts/pr_context.summary.txt` is stale — it describes PR #56 / issue #55, head `bd49647` — so the live diff was used as the authority)
  - Feature evidence: `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/evidence/**` (baseline + qa-gates)
  - Reviewer re-run: Black/Ruff/Pyright/Pytest against branch head; `artifacts/python/lcov.info`
- **Feature folder used:** `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/`
- **Requirements source:** `spec.md` (full-bug → spec.md only)
- **Work mode resolution note:** `issue.md` line 11 marks `- Work Mode: full-bug`; AC source resolves to `spec.md` AC-1..AC-13.
- **Scope note:** Full branch diff against the resolved base; no scope narrowing applied. No `.github/workflows/**` files in the diff, so `modified-workflow-needs-green-run` does not apply.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/spec.md` — only source (full-bug)

### Acceptance criteria

1. AC-1: An "Edit Schema" button is present beside each per-input Import button in `SourceInputWidget` (LE, AOP, SKU_LU tabs).
2. AC-2: Clicking "Edit Schema" with a real schema selected opens the schema builder seeded from that schema via `schema_builder_presenter.load_existing(<selected name>)`.
3. AC-3: The "Edit Schema" button is disabled when no real schema is selected (placeholder `<Choose Schema>`), mirroring the Import button's gating; the wiring additionally short-circuits (no builder, no crash) on placeholder/empty.
4. AC-4: A bundled `src/schemas/default_sku_lu.schema.json` exists with columns SKU, SKU Description, Category, Country; `Country` alias `["International"]`; key parts `[SKU]` with `sku_coercion=false`; `header_row` 0; `dedup.mode` "none"; empty `derived_columns`, `fill_rules`, `drop_columns`. It parses against the schema model.
5. AC-5: The registry auto-discovers `default_sku_lu` (appears in the dropdown at startup) and `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` maps to `"default_sku_lu"`, so the SKU_LU "Build new schema" button seeds from it and a SKU_LU sheet auto-matches it.
6. AC-6: The country-code mapping (`"0" -> "US"`, `"1" -> "Canada"`) is not encoded in `default_sku_lu.schema.json` and remains in `load_skulu` unchanged.
7. AC-7: `SourceSelectionPresenter.on_schema_discovery` reads a multi-row preview and selects the best-matching header row, so a sheet whose real header is on a later row (AOP1: index 2, stray/blank leading rows) auto-matches and activates its schema.
8. AC-8: Discovery for LE (`LE-8 + 4`) and SKU_LU (`SKU_LU`), whose headers are on row 0, is unchanged: the best-header-row selection returns row 0 and the same schema activates (no regression).
9. AC-9: Discovery does not crash when the first preview row is blank or when no file/sheet/schema is selected (the #50 activation-seam guard paths are exercised by tests).
10. AC-10: Every production module touched by this change is classified in `quality-tiers.yml` (no unclassified project remains; tier-classification stays green).
11. AC-11: No regression to existing LE / AOP / SKU_LU import, schema discovery, or schema-builder behavior; the existing test suite passes.
12. AC-12: All changed and added files (production, test, reusable scripts) remain <= 500 lines.
13. AC-13: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Edit Schema button present per tab | PASS | `build_edit_schema_button` constructs the button; `assemble_source_input_layout` adds it beside Build in the schema-button row; widget exposes `edit_schema_btn`. Widget tests assert presence on all tabs. | inspected `_source_input_button_wiring.py:185-203`, `source_input_widget.py:140-207` | Button shared by all three source widgets. |
| 2 | Edit opens builder seeded via `load_existing(name)` | PASS | `_open_edit` reads `current_schema()`, opens builder, then calls `load_existing(name)`; test asserts `presenters[0].loaded == ["le_v1"]`. | `pytest tests/gui/test_edit_schema_wiring.py` | Seeds the retained composition-root presenter. |
| 3 | Edit disabled on placeholder + wiring short-circuit | PASS | Button starts disabled; `_on_schema_changed` calls `set_edit_enabled(is_real)`; `_open_edit` returns early on placeholder/empty. Tests: placeholder short-circuit, no-schema seam. | `pytest tests/gui/test_edit_schema_wiring.py tests/gui/test_source_input_widget.py` | Defense in depth (widget + wiring). |
| 4 | `default_sku_lu.schema.json` exists and parses | PASS | Reviewer loaded it via production `SchemaRegistry.load_bundled_default`: cols SKU/SKU Description/Category/Country, Country alias `('International',)`, key SKU sku_coercion=False, header_row 0, dedup none, derived/fill/drop empty. | `poetry run python` registry load (reviewer) | Verified against the schema model, not only fixtures. |
| 5 | Registry auto-discovers default_sku_lu + mapping | PASS | `reg.list_schemas()` → `['default_aop','default_le','default_sku_lu']`; `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"] = "default_sku_lu"`. | `poetry run python` `list_schemas()` (reviewer); inspected `_schema_provider_factory.py:42-46` | Production registry surfaces it; not asserted only in tests. |
| 6 | Country mapping stays in load_skulu, not schema | PASS | `_COUNTRY_CODE_MAP = {"0": "US", "1": "Canada"}` in `src/load_skulu.py`; schema JSON contains no code mapping (Country is a plain dimension with `International` alias). | grep `load_skulu.py`; inspected schema JSON | Loader-side transform unchanged. |
| 7 | Multi-row best-header-row selection (AOP1) | PASS | `_best_header_row` selects the schema-binding row; test `..selects_header_on_later_row_aop1_style` asserts index-2 header matches and preview window cap is 5. | `pytest tests/gui/test_source_selection_presenter_header_row.py` | `_HEADER_PREVIEW_ROWS` 1→5. |
| 8 | LE/SKU_LU row-0 unchanged (no regression) | PASS | Dedicated row-0 regression tests for LE and SKU_LU select row 0 and activate the same schema; strict-`>` tie-break keeps earliest row. | `pytest tests/gui/test_source_selection_presenter_header_row.py` | Fallback returns `rows[0]` when no row binds. |
| 9 | No crash on blank first row / no file-sheet-schema | PASS | Blank-first-row test; no-schema seam test across all three tabs; presenter guards blank path/sheet and empty preview. | `pytest tests/gui/test_source_selection_presenter_header_row.py tests/gui/test_edit_schema_wiring.py` | #50 activation-seam guard paths exercised. |
| 10 | Touched production modules classified | PASS | `quality-tiers.yml` adds `_source_input_button_wiring.py`, `_schema_discovery_wiring.py`, `_schema_provider_factory.py` (T4) and `_schema_activation.py`, `_header_detection.py` (T2); existing presenter/widget already classified. All 7 touched `.py` modules classified. | inspected `quality-tiers.yml` diff | New JSON file is data, not a tiered project. |
| 11 | No regression; suite passes | PASS | 1023 passed, 0 failed on reviewer re-run; baseline was 998. Coverage delta +0.01 pp line / +0.09 pp branch. | `poetry run pytest --cov --cov-branch` (reviewer) | LE/AOP/SKU_LU and builder tests unchanged and passing. |
| 12 | All changed files <= 500 lines | PASS | Reviewer `wc -l`: max production 498 (`source_input_widget.py`), max test 482 (`test_source_input_widget.py`); all others lower. | `wc -l` on all changed files | Test files counted against the cap per orchestrator memory. |
| 13 | Full toolchain + coverage thresholds, no changed-line regression | PASS | Black clean; Ruff clean; Pyright 0/0; Pytest 1023 pass; repo-wide 99.09% line / 94.05% branch; changed-module 98% line. | `poetry run black --check .` / `ruff check .` / `pyright` / `pytest --cov --cov-branch` | Reviewer-reproduced exit 0 on each stage. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 13 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Manual GUI validation of AOP1 auto-match end-to-end against the real workbook layout (subagents cannot open `.xlsx`; this is the spec's stated post-fix manual step, not an AC gap).
2. None further; the change is ready for merge.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** are checked off in the authoritative source file when represented as markdown checkboxes.
- All 13 AC items in `spec.md` were already checked off by the executor and remain `[x]`; all 13 are confirmed PASS by this audit, so no check-off change was required.

### AC Status Summary

- Source: `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/spec.md`
- Total AC items: 13
- Checked off (delivered): 13
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 13 | 13 | 0 | Checkbox-backed; all confirmed PASS, already checked by executor |

No source-file checkbox change was made because all 13 items were already `[x]` and all are confirmed PASS.
