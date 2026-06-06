# Feature Audit: schema-required-output-semantics (#54)

**Audit Date:** 2026-06-06
**Feature Folder:** `docs/features/active/2026-06-06-schema-required-output-semantics-54`
**Base Branch:** `7bfa57c` (rebased #50 HEAD immediately before #54 work)
**Head Branch:** `feature/schema-builder-ux-overhaul-50` @ `55261bf` (rides in PR #51)
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review (isolated #54 delta)

---

## Scope and Baseline

- **Base branch:** `7bfa57c` (rebased #50 HEAD immediately before #54 work began)
- **Head branch/commit:** `feature/schema-builder-ux-overhaul-50` @ `55261bf`
- **Merge base:** `7bfa57c` (the supplied isolation point for the #54 delta within PR #51)
- **Evidence sources:**
  - Primary: `git diff 7bfa57c..HEAD` and `git log 7bfa57c..HEAD` (single commit `55261bf`)
  - Feature evidence: `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/**`
  - Additional evidence: independent toolchain re-run during this audit (Black/Ruff/Pyright/Pytest)
- **Feature folder used:** `docs/features/active/2026-06-06-schema-required-output-semantics-54`
- **Requirements source:** `issue.md` and `spec.md` (work mode `full-feature`). Note: `user-story.md` is not present in this feature folder; `issue.md` carries an explicit `## Acceptance Criteria` section (AC-1..AC-8) that mirrors `spec.md` v1.0 verbatim, and both are used as the authoritative AC source.
- **Work mode resolution note:** `issue.md` line 10 declares `- Work Mode: full-feature`. AC-1..AC-8 are identical in `issue.md` and `spec.md`.
- **Scope note:** Audit is the full isolated #54 delta (`7bfa57c..HEAD`), which is the full-feature scope of the #54 sub-feature within PR #51. No scope narrowing applied.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `issue.md` — primary (full-feature; explicit `## Acceptance Criteria` AC-1..AC-8)
- `spec.md` — secondary (full-feature; identical AC-1..AC-8)
- `user-story.md` — not present in this feature folder

### Acceptance criteria (verbatim)

1. AC-1: No bundled schema requires a column only to drop it; `default_le` `YTD/YTG` is `required: false` and `in_output: false`, and `drop_columns` is `[]`.
2. AC-2: The schema loader determines output columns by inclusion (`in_output` true, plus `KEY` and derived columns), not by a `drop_columns` by-name list.
3. AC-3: LE schema-driven load output equals `normalize_le.TARGET_COLUMNS` exactly (set, order, values).
4. AC-4: AOP schema-driven load output equals the `load_aop` output exactly, including the optional-but-output `YTG`.
5. AC-5: A processing-only column (required:false, in_output:false) is present in the source, used for dedup, and excluded from the output.
6. AC-6: `ColumnSpec.in_output` defaults to `True`; JSON without the field loads as `True`; a schema with `in_output:false` round-trips.
7. AC-7: The #50 schema-builder carries `in_output` end-to-end (`assemble_schema` -> `ColumnSpec`), and the provider-factory split places LE `YTD/YTG` in the optional set.
8. AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC-1 LE `YTD/YTG` required:false, in_output:false, drop_columns [] | PASS | `default_le.schema.json` diff: `YTD/YTG` now `"required": false`, `"in_output": false`; tail of file `"drop_columns": []`. Test `tests/test_default_schemas.py::test_le_drops_ytd_ytg_source_column` asserts all three. | `git diff 7bfa57c..HEAD -- src/schemas/default_le.schema.json` | No other bundled schema requires-then-drops; AOP `drop_columns` already `[]`. |
| 2 | AC-2 output by `in_output` inclusion, not `drop_columns` | PASS | `_schema_loader_helpers.py::_output_column_order` -> `[c.canonical_name for c in schema.columns if c.in_output]`; `none`-mode emit filters by `excluded = {c.canonical_name for c in schema.columns if not c.in_output}`. Tests `test_in_output_true_column_is_included_in_output`, `test_in_output_false_column_is_excluded_from_output`. `git grep drop_columns` shows no source path consults it for output. | `poetry run pytest tests/test_schema_loader_derived.py` | drop_columns retained in shape only (compatibility). |
| 3 | AC-3 LE output equals `normalize_le.TARGET_COLUMNS` | PASS | `tests/test_schema_loader_parity_le.py` (5 tests) pass; pins schema-driven LE output to `normalize_le.TARGET_COLUMNS` (set/order/values). | `poetry run pytest tests/test_schema_loader_parity_le.py -v` | Top invariant; confirmed in independent run (5 pass). |
| 4 | AC-4 AOP output equals `load_aop`, incl. `YTG` | PASS | `tests/test_schema_loader_parity_aop.py` (4 tests) pass; AOP `YTG` set `in_output:true` in `default_aop.schema.json`, kept in output. | `poetry run pytest tests/test_schema_loader_parity_aop.py -v` | Confirmed in independent run (4 pass). |
| 5 | AC-5 processing-only column present, used for dedup, excluded | PASS | `test_processing_only_discriminator_used_for_dedup_but_excluded`: two key-sharing rows with distinct discriminators collapse to one row with summed `Amt` (15.0), discriminator absent from output. `_by_name_optional_columns` now includes `YTD/YTG` (required:false) and carries it through `resolve_and_rename`/`collapse_by_key`. | `poetry run pytest tests/test_schema_loader_derived.py` | Exclusion at emit only. |
| 6 | AC-6 in_output defaults True; absent loads True; round-trips | PASS | `ColumnSpec.in_output: bool = True`; `schema_serialization._object_to_column` parses with `optional_bool(..., default=True)`. Tests `test_absent_in_output_defaults_to_true` (inline legacy JSON), `test_in_output_false_round_trips`, property `_draw_column` draws `in_output` independently. | `poetry run pytest tests/test_schema_serialization.py` | No SCHEMA_FORMAT_VERSION bump (stays "2.0"). |
| 7 | AC-7 builder carries in_output end-to-end; provider-factory split | PASS | `assemble_schema` forwards `in_output=in_output` into `ColumnSpec`; 4-tuple->5-tuple migration complete at state, presenter, columns-tab, drag-tabs, dialog, view protocol, fakes (Pyright 0 errors). `_schema_provider_factory` splits on `column.required`, so LE `YTD/YTG` lands optional. Tests `test_assemble_schema_forwards_in_output_true_and_false`, `test_real_bundled_le_ytd_ytg_is_in_optional_specs`. | `poetry run pytest tests/gui/test_schema_builder_assemble.py tests/gui/test_schema_provider_factory.py` | No code change needed in provider factory (keyed on required). |
| 8 | AC-8 full toolchain + coverage >= 85%/75% + no regression | PASS | Independent re-run: Black clean (223 files unchanged), Ruff "All checks passed", Pyright "0 errors, 0 warnings", Pytest 966 passed. Coverage 99.07% line / 94.15% branch; edited modules >=92% line; baseline->post-change delta +0.00% (no regression). | `poetry run black --check`; `ruff check`; `pyright`; `pytest --cov=src --cov-branch` | Exceeds thresholds. |

---

## Parity Confirmation (CRITICAL)

The top invariant — byte-identical output to the protected loaders — was independently verified:

- LE: `tests/test_schema_loader_parity_le.py` (5 tests) PASS. Schema-driven LE output equals `normalize_le.TARGET_COLUMNS` (set, order, values). The `YTD/YTG` discriminator, now `in_output:false`, is excluded by inclusion exactly where the old `drop_columns` removed it.
- AOP: `tests/test_schema_loader_parity_aop.py` (4 tests) PASS. AOP output equals `load_aop` output, including the optional-but-output `YTG` (`required:false, in_output:true`).
- The protected loaders `src/normalize_le.py` and `src/load_aop.py` are not in the diff (unmodified), satisfying the spec invariant.

Bundled-schema spec conformance confirmed by diff inspection: `default_le` `YTD/YTG` is `required:false, in_output:false`, `drop_columns: []`; every other LE/AOP column carries explicit `in_output:true`; AOP `YTG` is `required:false, in_output:true`; both `drop_columns` are `[]`.

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 8 criteria (AC-1..AC-8)
- **PARTIAL:** 0
- **UNVERIFIED:** 0
- **FAIL:** 0

**Top gaps preventing PASS:**
1. None.

**Recommended follow-up verification steps:**
1. None required for the #54 delta. The change is ready to merge as part of PR #51.

---

## Acceptance Criteria Check-off

All eight criteria evaluate to PASS and are already checked `[x]` in both `issue.md` and `spec.md` (checked by the executor during delivery). This audit confirms each check-off is supported by passing evidence; no checkbox state change was required.

### AC Status Summary

- Source: `issue.md` and `spec.md`
- Total AC items: 8
- Checked off (delivered): 8
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 8 | 8 | 0 | Checkbox-backed; AC-1..AC-8 already `[x]`, confirmed PASS. |
| `spec.md` | 8 | 8 | 0 | Checkbox-backed; identical AC-1..AC-8 already `[x]`, confirmed PASS. |

No source-file checkbox change was made because all criteria were already correctly checked and all evaluate to PASS.
