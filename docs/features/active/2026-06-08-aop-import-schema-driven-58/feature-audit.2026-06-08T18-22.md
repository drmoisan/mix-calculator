# Feature Audit: aop-import-schema-driven (Issue #58) — Cycle-1 EXIT Reaudit

**Audit Date:** 2026-06-08
**Feature Folder:** `docs/features/active/2026-06-08-aop-import-schema-driven-58`
**Base Branch:** `main`
**Head Branch:** `feat/aop-import-schema-driven` (working tree, uncommitted)
**Work Mode:** `full-feature`
**Audit Type:** Post-remediation acceptance verification (after cycle-1 test-only split)

---

## Scope and Baseline

- **Base branch:** `main` (merge-base commit `63522c00dcd9a2146226d3e01d4f72f5e48a1351`)
- **Head branch/commit:** `feat/aop-import-schema-driven` working tree (uncommitted cycle-0 + cycle-1 changes)
- **Merge base:** `63522c00`
- **Evidence sources:**
  - Primary: independently re-run toolchain in this reaudit (Black/Ruff/Pyright clean; pytest 998 passed; line 98.24%, branch 93.74%).
  - Secondary baseline diff: `git diff 63522c00` over `*.py` and `src/schemas/default_aop.schema.json`.
  - Feature evidence: `docs/features/active/2026-06-08-aop-import-schema-driven-58/evidence/remediation-cycle-1/`.
  - Additional evidence: cycle-0 `feature-audit.2026-06-08T17-39.md` (all nine ACs PASS before the split).
- **Feature folder used:** `docs/features/active/2026-06-08-aop-import-schema-driven-58`
- **Requirements source:** `spec.md` and `issue.md` (canonical AC list AC-1..AC-9; identical in both). `user-story.md` is absent (recorded as cycle-0 Non-blocking N1); no acceptance criterion is lost.
- **Work mode resolution note:** `issue.md` carries the explicit marker `- Work Mode: full-feature`, which resolves AC sources to `spec.md` and `user-story.md`. With `user-story.md` absent, the identical canonical list in `spec.md`/`issue.md` is the authoritative AC source.
- **Scope note:** Working-tree-only validation (the whole feature is uncommitted). This reaudit covers the entire feature #58 because the exit gate governs merge; the cycle-1 split moved tests that are the evidence for several ACs, so each moved test was confirmed to still run and pass.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `issue.md` — primary (canonical list, checkbox-backed)
- `spec.md` — secondary (identical canonical list)

### Acceptance criteria

1. AC-1: The default GUI AOP import runs through `SchemaLoader(default_aop)` and applies no arithmetic identity validation (`YTD/YTG/quarter == sum(...)`); a source whose totals do not satisfy those identities imports without error.
2. AC-2: A full-year-YTD source imports successfully through `import_aop` (regression for the reported failure).
3. AC-3: A partial-year-YTD source imports successfully through `import_aop`.
4. AC-4: No blank-total fill is applied on the AOP import path; a source row with a blank total cell (e.g. blank `YTD`) yields `0` in that column after numeric coercion, not the computed month sum.
5. AC-5: `SchemaLoader.load` accepts and forwards `resolver`, `is_tty`, and `prompt` to `resolve_key`, and `PipelineService.import_aop` wires `self._key_mismatch_resolver`, `never_tty`, and `no_stdin_prompt` (the resolver forwarded as a callable, invoked only on KEY divergence).
6. AC-6: The schema-driven AOP output column set and order, and KEY semantics, match the prior loader for columns present and populated in the source.
7. AC-7: `import_aop` resolves the AOP header row via `detect_header_row` (issue #55) rather than a hardcoded row; a source whose header sits at a non-default offset still imports.
8. AC-8: Existing `SchemaLoader` callers and the LE and SKU_LU import paths are unaffected.
9. AC-9: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage >= 85% line / >= 75% branch, no regression on changed lines, and the T1 property/mutation obligations for `src/schema_loader.py` satisfied.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC-1 no arithmetic identity validation | PASS | `import_aop` delegates to `import_aop_via_schema` which routes through `SchemaLoader(default_aop)` with empty `fill_rules`; `test_import_aop_imports_source_with_broken_totals` asserts a `YTD=999999` row imports and passes through. | `pytest tests/gui/test_pipeline_service_aop_schema.py -q` | Moved test confirmed running/passing post-split. |
| 2 | AC-2 full-year-YTD imports | PASS | `test_import_aop_imports_full_year_ytd_source` passes; uses `build_full_year_ytd_workbook`. | `pytest tests/gui/test_pipeline_service_aop_schema.py -q` | Relocated verbatim. |
| 3 | AC-3 partial-year-YTD imports | PASS | `test_import_aop_imports_partial_year_ytd_source` passes; uses `build_aop_workbook`. | `pytest tests/gui/test_pipeline_service_aop_schema.py -q` | Relocated verbatim. |
| 4 | AC-4 no blank-total fill | PASS | `default_aop.schema.json` has `fill_rules: []` (diff shows fill_rules emptied); `tests/test_default_schemas.py` asserts `fill_rules == ()`; `tests/test_schema_loader_parity_aop.py` blank-total case retained (not part of the cycle-1 split). | `pytest tests/test_default_schemas.py tests/test_schema_loader_parity_aop.py -q` | Unchanged by cycle 1. |
| 5 | AC-5 resolver/is_tty/prompt seam forwarded | PASS | `SchemaLoader.load` forwards `resolver`/`is_tty`/`prompt` to `resolve_key` (schema_loader diff lines 192-205); `import_aop_via_schema` wires `never_tty`/`no_stdin_prompt` and the injected resolver. `test_load_forwards_resolver_seams_to_resolve_key_on_divergence` and the property test pass. | `pytest tests/test_schema_loader_seam.py -q` | Relocated verbatim; prompt-never-reached guard intact. |
| 6 | AC-6 output column set/order and KEY parity | PASS | `test_import_aop_output_columns_and_key_match_prior_loader` asserts `list(frame.columns) == list(prior.columns)` and matching rebuilt KEY against `load_aop`. | `pytest tests/gui/test_pipeline_service_aop_schema.py -q` | Relocated verbatim. |
| 7 | AC-7 header row via detect_header_row | PASS | `import_aop_via_schema` calls `detect_header_row(source, sheet, expected_tokens, min_match=17)`; `test_import_aop_header_detection_drives_the_read` imports a non-default-offset workbook. | `pytest tests/gui/test_pipeline_service_aop_schema.py -q` | Relocated verbatim. |
| 8 | AC-8 LE/SKU_LU and existing callers unaffected | PASS | `test_load_backward_compatible_without_seam_arguments` confirms positional `load(raw)`/`load(raw, schema)` unchanged; LE/SKU_LU loaders unmodified; full suite (998) green. | `pytest -q` | Backward-compat test relocated; LE parity suite untouched. |
| 9 | AC-9 toolchain + coverage + T1 obligations | PASS | Black `--check` exit 0 (236 unchanged), Ruff exit 0, Pyright 0 errors, pytest 998 passed; line 98.24% >= 85%, branch 93.74% >= 75%; no regression on changed production lines (3 changed modules 100% line; schema_loader 100% branch). T1 property test for `schema_loader` (`test_property_resolver_action_governs_key_on_divergence`) present and passing. | `black --check .; ruff check .; pyright; pytest --cov --cov-branch` | All re-run independently in this reaudit. |

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

1. None required for the exit gate. Optionally add `user-story.md` (or a note that the canonical AC list resides in `spec.md`/`issue.md`) to clear the cycle-0 Non-blocking N1 documentation gap.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules: all nine criteria evaluate to PASS. They are already checked off (`- [x]`) in `issue.md` (and mirrored in `spec.md`) from cycle 0; the cycle-1 split preserved the satisfying tests, so the check-off state remains accurate. No further check-off change is required.

### AC Status Summary

- Source: `issue.md` (canonical), mirrored in `spec.md`
- Total AC items: 9
- Checked off (delivered): 9
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 9 | 9 | 0 | Checkbox-backed; all `- [x]`. |
| `spec.md` | 9 | 9 | 0 | Mirrors `issue.md`; canonical AC list. |

No source-file checkbox change was made in this reaudit because all nine items were already checked off in cycle 0 and remain valid after the behavior-preserving split.
