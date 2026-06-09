# Remediation Inputs: aop-import-schema-driven (Issue #58)

**Generated:** 2026-06-08T17-39
**Source artifacts:**
- policy-audit-path: docs/features/active/2026-06-08-aop-import-schema-driven-58/policy-audit.2026-06-08T17-39.md
- code-review-path: docs/features/active/2026-06-08-aop-import-schema-driven-58/code-review.2026-06-08T17-39.md
- feature-audit-path: docs/features/active/2026-06-08-aop-import-schema-driven-58/feature-audit.2026-06-08T17-39.md

## Remediation-Required Findings (Blocking)

### B1 — Test files exceed the 500-line file-size cap

- **Policy:** `.claude/rules/general-code-change.md` — "No production code, test code, or reusable script file may exceed 500 lines." The test-file exemptions (throwaway scripts, raw text fixtures, Markdown) do not apply to these reusable Python test modules.
- **Files and current sizes (authoritative `awk` line count):**
  - `tests/gui/test_pipeline_service.py` — 638 lines (baseline at merge-base 63522c00: 471; +167 this feature).
  - `tests/test_schema_loader_core.py` — 501 lines (baseline at merge-base 63522c00: 374; +127 this feature).
- **Attribution:** Both crossed the cap as a direct result of this feature's added AOP/seam tests. This is a regression introduced on the branch, not a pre-existing condition.
- **Why the executor missed it:** `evidence/qa-gates/file-size-final.md` tracked only the four production files and did not scan changed test files.
- **Required action:** Split each file into cohesive sibling test modules so every resulting file is <= 500 lines. Suggested seams:
  - `test_pipeline_service.py`: separate the AOP schema-path tests (import_aop full-year / partial-year / broken-total / header-detection / output-parity) into a dedicated module, e.g. `tests/gui/test_pipeline_service_aop_schema.py`, leaving LE/SKU_LU/run-pipeline tests in place.
  - `test_schema_loader_core.py`: separate the resolver-seam and hypothesis property tests into a dedicated module, e.g. `tests/test_schema_loader_seam.py`.
- **Verification after fix:** re-run the full Python toolchain loop (Black -> Ruff -> Pyright -> Pytest) to confirm no test loss and clean stages; re-run the file-size scan across all changed `.py` files (independent of any executor evidence) to confirm every file <= 500.

## Non-Blocking Findings (recorded, not gating)

### N1 — Missing `user-story.md`

- Work mode `full-feature` resolves AC sources to `spec.md` AND `user-story.md`, but `user-story.md` is absent from the feature folder. The canonical AC list (AC-1..AC-9) is present and identical in `spec.md` and `issue.md`; no acceptance criterion is lost.
- **Suggested action:** add `user-story.md` to the feature folder, or record in feature docs that the canonical AC list resides in `spec.md`/`issue.md` for this refactor.

## Summary

- blocking_count (FAIL or blocking-PARTIAL across all three artifacts): 1
- Blocking findings: B1 (file-size cap on two test files).
- The feature is functionally complete and all nine acceptance criteria pass; B1 is a structural/policy gate that must clear before merge.
