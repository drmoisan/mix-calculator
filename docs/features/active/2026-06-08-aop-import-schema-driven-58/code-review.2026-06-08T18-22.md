# Code Review: aop-import-schema-driven (Issue #58) — Cycle-1 EXIT Reaudit

**Review Date:** 2026-06-08
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-06-08-aop-import-schema-driven-58`
**Base Branch:** `main`
**Head Branch:** `feat/aop-import-schema-driven` (working tree, uncommitted)
**Review Type:** Post-remediation re-review (cycle-1 test-only split)

---

## Executive Summary

This review covers the whole feature #58 at its current working-tree state against merge-base `63522c00`: the cycle-0 schema-driven AOP import plus the cycle-1 test-only split refactor that closed Blocking finding B1 (two test files over the 500-line cap). The production delta is small and well-scoped: `PipelineService.import_aop` now delegates to a new thin helper `src/gui/_aop_schema_import.py` that loads `default_aop`, resolves the header row via `detect_header_row`, reads the raw frame, and transforms it through `SchemaLoader.load`; `SchemaLoader.load` gained keyword-only `resolver`/`is_tty`/`prompt` seams with defaults that preserve existing positional callers.

The cycle-1 work changed no production logic. It relocated the five AOP schema-path tests and the three resolver-seam tests verbatim into new cohesive sibling modules, and moved the shared helpers (`_patch_loaders`; `_load_default`/`_MONTHS_A`/`_MONTHS_B`) into two new underscore-prefixed fixture modules with `__all__` exports, following the existing `tests/_mix_rollups_fixtures.py` pattern. No suppressions were added.

**What changed:**
Production: `pipeline_service.py` (delegation + docstring), `_aop_schema_import.py` (new helper), `schema_loader.py` (resolver seam), `default_aop.schema.json` (cycle-0: `header_row` 0->2, `fill_rules` emptied). Tests: two over-cap files split into four new modules; remaining test files updated only for relocated-helper imports.

**Top 3 risks:**
1. The new helper uses function-local imports for its collaborators; this is intentional (keeps the top-level import surface minimal and lets tests patch the read boundary at source) but means import errors surface at call time rather than module load. Mitigated by 100% line coverage of the helper.
2. Cross-module test-private helpers are now imported between test modules; correctness depends on the `__all__` exports staying in sync. Verified present and Pyright-clean under strict mode.
3. `pipeline_service.py` sits exactly at the 500-line cap, leaving no headroom for future edits without a further split. Not a defect; noted for maintainers.

**PR readiness recommendation:** **Go** — B1 is closed, no new defect was introduced, and the toolchain is clean (independently re-run).

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/pipeline_service.py` | line 500 (EOF) | File is exactly at the 500-line cap, leaving no headroom for future additions. | When next modifying this module, extract another cohesive seam rather than appending. | Not a violation (cap is "may not exceed 500"), but future edits will need a split. | `awk 'END{print NR}'` = 500; `wc -l` = 500 with trailing newline. |
| Info | `src/gui/_aop_schema_import.py` | lines 91-97 | Collaborators imported function-locally inside `import_aop_via_schema`. | Keep as-is; documented as intentional for patchability and minimal import surface. | Trades load-time import errors for call-time, acceptable for a single-entry helper. | Module docstring + inline comment explain the choice. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The AOP detect/read/transform sequence was extracted into a single cohesive helper, keeping `pipeline_service.py` within the file cap while leaving `import_aop` a readable thin delegator with an accurate docstring that explains the schema-driven routing and the empty-`fill_rules` consequence.
- The `SchemaLoader.load` seam is the smallest change that enables GUI-side non-interactive KEY resolution: keyword-only `resolver`/`is_tty`/`prompt` with defaults (`sys.stdin.isatty`, `input`, `None`) so every existing positional caller is unaffected. The backward-compatibility test (`test_load_backward_compatible_without_seam_arguments`, AC-8) confirms this.
- The cycle-1 split follows behavior seams: AOP schema-path tests in one module, resolver-seam/property tests in another, with the LE/SKU_LU/orchestration tests left in the originals. Shared helpers were relocated (not duplicated), keeping the suite DRY.
- The new fixture modules carry `__all__` and clear docstrings, matching the established `tests/_mix_rollups_fixtures.py` pattern; this satisfies strict Pyright `reportPrivateUsage` for cross-module test-private imports without any suppression.

#### Typing and API notes

- New code is fully annotated; no `Any`. Seam callables are typed (`Callable[[list[tuple[str, str]]], str]`, `Callable[[], bool]`, `Callable[[str], str]`) under `TYPE_CHECKING`.
- `import_aop_via_schema(source, sheet, resolver)` is a clear, narrow public-within-package surface. `ExcelSource` is referenced under `TYPE_CHECKING`.
- No public API of `PipelineService` changed; `import_aop` keeps its `(path, sheet) -> DataFrame` signature.

#### Error handling and logging

- `logger.info` retained in `import_aop`; no print statements.
- `ValueError` propagation from header detection and the schema loader is documented in both the delegator and helper docstrings; no broad except introduced.
- No import cycle: `pipeline_service` imports `_aop_schema_import` only via a function-local import; `_aop_schema_import` does not import `pipeline_service`. Verified by grep.

---

## Test Quality Audit

The relocated tests were inspected line-by-line and assert the same behavior as before the split: column set/order and KEY composition parity against `load_aop` (AC-6), broken-total pass-through with no validation error (AC-1), header detection driving the read (AC-7), full-year and partial-year imports (AC-2/AC-3), and the resolver-forwarding/property/backward-compat seam behaviors (AC-5, AC-8). No assertion was weakened or removed. The post-split suite count (998) equals the pre-split baseline (998), confirming no test loss. No duplicate test-function names exist across the split modules (verified by `grep`/`uniq -d`).

### Reviewed test and QA artifacts

- `tests/gui/test_pipeline_service_aop_schema.py` — five relocated AOP tests; in-memory workbooks only; assertions unchanged.
- `tests/test_schema_loader_seam.py` — three relocated seam tests including the Hypothesis property test; explicit prompt-never-reached guard.
- `tests/gui/_pipeline_service_fixtures.py`, `tests/_schema_loader_fixtures.py` — relocated shared helpers with `__all__`; no temp files.
- `evidence/remediation-cycle-1/final-pytest-coverage.md` — 998 passed, 98.24% line, 93.74% branch (corroborated by independent reaudit run).
- `evidence/remediation-cycle-1/file-size-final.md`, `coverage-delta.md`, `b1-closure.md` — B1 closure evidence.

### Quality assessment prompts

- **Determinism:** No wall-clock/RNG; Hypothesis draws from a fixed 2-value set; BytesIO inputs.
- **Isolation:** Each test exercises one behavior; function-scoped `monkeypatch`.
- **Speed:** Two new modules run in ~1.3s; full suite 37.90s for 998 tests.
- **Diagnostics:** Behavioral assertions on KEY and column order; explicit `AssertionError` guard messages.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No credentials/keys in the diff; test data is fabricated. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess in the changed code. |
| Input validation at boundaries | ✅ PASS | Header detection enforces a token floor; `ValueError` on failure; numeric coercion via schema. |
| Error handling remains explicit | ✅ PASS | Specific `ValueError` propagation; no broad except added. |
| Configuration / path handling is safe | ✅ PASS | Bundled schema resolved via `SchemaRegistry`/`DiskSchemaFileStore`; no user-controlled path construction added. |

---

## Research Log

No external research was required. The review relied on working-tree inspection, the cycle-1 evidence artifacts, and independently re-run toolchain commands.

---

## Verdict

The cycle-1 split is a clean, behavior-preserving refactor that closes B1 without introducing new defects. Production logic is unchanged from cycle 0; the relocated tests assert identical behavior and the suite count held at 998. Typing, error handling, module cohesion, and import-cycle freedom are all satisfied, and the toolchain is clean in a single pass. The change is ready for normal PR flow.
