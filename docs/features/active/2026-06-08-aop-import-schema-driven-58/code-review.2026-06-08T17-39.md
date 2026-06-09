# Code Review: aop-import-schema-driven (Issue #58)

**Review Date:** 2026-06-08
**Branch:** `feat/aop-import-schema-driven`
**Base (merge-base):** `63522c00`
**Verdict:** PASS (no blocking code-quality findings)

## Executive Summary

The change reroutes the GUI AOP import from the legacy arithmetic-validating `src.load_aop.load_aop` to the schema-driven `SchemaLoader(default_aop)` path. The implementation is correct, well-factored, and backward-compatible:

- **Schema-driven `import_aop`.** `PipelineService.import_aop` is now a thin delegator to `src.gui._aop_schema_import.import_aop_via_schema`, which loads the bundled `default_aop` schema, derives the expected header tokens from the schema's required columns (excluding optional `KEY`/`YTG`), resolves the header row via `detect_header_row` (issue #55) with a 17-token floor matching the legacy `load_aop` detection, reads the raw frame at the detected header through `read_excel_sheet`, and transforms via `SchemaLoader.load`. The detect/read/transform sequence was extracted into the helper specifically to keep `pipeline_service.py` within the 500-line cap; behavior is unchanged by the extraction.
- **Resolver/seam forwarding preserves issue #52 behavior.** `import_aop_via_schema` forwards the injected resolver CALLABLE (not its result) plus `never_tty`/`no_stdin_prompt` into `SchemaLoader.load`, which forwards them into `resolve_key`. The resolver fires only on genuine KEY divergence; a GUI session stays off stdin. The `SchemaLoader.load` signature's `is_tty`/`prompt` defaults (`sys.stdin.isatty`, `input`) exactly mirror the pre-existing `resolve_key` defaults, so default callers see identical behavior.
- **Buffer rewind handled.** `detect_header_row` rewinds a seekable buffer before its probe; `read_excel_sheet` reopens a path or reads the rewound buffer. The test harness re-seeks the shared `io.BytesIO` at each boundary, confirming rewind correctness.
- **`default_aop` schema edit.** `fill_rules` cleared to `[]` (the existing `if totals_to_months:` guard in the loader short-circuits, so no code change is needed to disable filling) and the informational `header_row` set to `2`. Both verified by a round-trip test.
- **`SchemaLoader.load` seam extension (T1).** Three new keyword-only optional parameters, additive and backward-compatible; all existing callers (positional `load(raw)` / `load(raw, schema)`) remain intact, with an explicit backward-compat test.

No dead code, no missing error handling, and no seam regression were found. The single quality concern relevant here is file size, which is recorded in the policy audit (two changed test files exceed the 500-line cap); the production code is within cap.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Non-blocking | src/gui/pipeline_service.py | docstring line 8; module body | The module docstring still references `:mod:`src.load_aop`` while noting it "remains the CLI path"; the runtime `load_aop` import was correctly removed. | None required. The reference is accurate (it documents the CLI contrast) and not a live dependency. | Confirms the import removal is complete and intentional; no stale code dependency. | `git diff 63522c00 -- src/gui/pipeline_service.py` shows `from src import load_skulu, normalize_le` (load_aop dropped); `grep load_aop src/gui/pipeline_service.py` returns only the docstring line. |
| Non-blocking | src/gui/_aop_schema_import.py | lines 91-97 | Schema-path collaborators are imported locally inside `import_aop_via_schema` rather than at module top. | Keep as-is. | The local import is deliberate: it minimizes the import surface and, critically, lets tests patch `detect_header_row`/`read_excel_sheet`/`SchemaLoader` at their source modules (the `_patch_loaders` strategy depends on this). Documented in the inline comment. | `src/gui/_aop_schema_import.py:86-97`; `tests/gui/test_pipeline_service.py:269-274` patches at `src._header_detection.detect_header_row` / `src.pandas_io.read_excel_sheet`. |
| Non-blocking | src/gui/_aop_schema_import.py | line 102 | `SchemaRegistry(Path("."), DiskSchemaFileStore()).load_bundled_default("default_aop")` passes `Path(".")` as a registry dir that `load_bundled_default` ignores. | Optional: a comment already explains this. No change needed. | The comment states `load_bundled_default` ignores the `registry_dir` argument and resolves from the packaged `bundled_dir`, matching how the parity tests construct it; the constructor requires the argument. | `src/gui/_aop_schema_import.py:99-104` inline comment; consistent with parity-test construction. |

## Detailed Review Notes

### Correctness of schema-driven `import_aop`

- Header detection: `expected_tokens` derived via `normalize_name(column.canonical_name)` for required columns, excluding `_OPTIONAL_AOP_COLUMNS = {KEY, YTG}`, with `min_match=_AOP_HEADER_MIN_MATCH = 17`. This reproduces the legacy `load_aop` detection floor for behavioral parity. Verified by `test_import_aop_header_detection_drives_the_read` (AC-7), which places the header at index 0 (a flat sheet) where a hardcoded `header=2` would misread, and asserts the correct row loads.
- Schema load: `SchemaRegistry(...).load_bundled_default("default_aop")` — the same construction the parity suite uses.
- Output parity: `test_import_aop_output_columns_and_key_match_prior_loader` (AC-6) and the re-targeted `test_schema_loader_parity_aop.py` confirm column set/order and KEY composition (`Customer + coerce_sku(SKU #) + Type`). The parity contract (only `Customer`, `Customer Master`, `Super Category`, `PPG`, `SKU Descripiton`, `SKU #`, `Type`, `YTG`, `KEY` are consumed downstream) holds; no downstream stage reads `YTD`/`Q1`-`Q4`/`Jan`-`Dec`, so removing fill/validation does not change any transform result.

### Seam extension on `SchemaLoader.load`

- The new parameters are keyword-only (`*`-separated) and optional. `resolver` defaults to `None`; `is_tty`/`prompt` default to the same callables `resolve_key` already uses, so the function-definition-time binding of `sys.stdin.isatty`/`input` is identical to the forwarded target — no behavior change for default callers.
- Forwarding verified by `test_load_forwards_resolver_seams_to_resolve_key_on_divergence` (the resolver is the decision source on divergence and the prompt is never invoked) and the hypothesis property test `test_property_resolver_action_governs_key_on_divergence` (for both `trust` and `overwrite` actions the resolved action governs the KEY), satisfying the T1 property obligation. Backward compatibility verified by `test_load_backward_compatible_without_seam_arguments`.

### Schema edit and dead-code check

- `fill_rules: []` relies on the existing `if totals_to_months:` guard short-circuiting; no loader code path becomes dead, and no new branch is introduced. `header_row: 2` is informational only (the read is driven by `detect_header_row`, not the schema field), as the helper docstring states.

### Error handling

- `ValueError` propagation is documented and exercised on two paths: header-detection floor not met, and KEY-resolution failure. No broad `except` is introduced.

### Test-harness validity (non-vacuous patching)

- The risk that re-routing leaves stale `monkeypatch.setattr("src.load_aop.load_aop", ...)` patches passing vacuously is addressed: the five flagged sites were re-targeted to the schema path. `_patch_loaders` patches the real `detect_header_row`/`read_excel_sheet` at their source modules and delegates to the real implementations against a shared in-memory buffer, so the detection/read logic genuinely executes. The AOP resolver-forwarding test intercepts at `SchemaLoader.load`.

## Recommendation

Mergeable from a code-quality standpoint. The file-size cap violations on two test files (tracked as Blocking in the policy audit) should be resolved before merge; they are a structural/policy matter, not a correctness defect in the reviewed logic.
