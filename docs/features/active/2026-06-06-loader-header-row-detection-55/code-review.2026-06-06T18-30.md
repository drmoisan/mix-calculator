# Code Review: loader-header-row-detection (#55)

**Review Date:** 2026-06-06
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-06-06-loader-header-row-detection-55`
**Feature Folder Selection Rule:** Single active folder whose suffix (`-55`) matches the issue number in the branch name `fix/loader-header-row-detection`.
**Base Branch:** `main` (merge-base `b655d81`)
**Head Branch:** `fix/loader-header-row-detection` (HEAD `721a1bf`)
**Review Type:** Initial review

---

## Executive Summary

This change replaces the hardcoded `read_excel_sheet(..., header=2)` in `normalize_le.load_source` and `load_aop.load_aop` with deterministic header-row detection. A new internal module `src/_header_detection.py` probes the sheet once with `header=None`, scores each of the first `max_rows` rows by the count of normalized expected column tokens present, and selects the topmost row whose score is the highest and clears a per-loader `min_match` floor. `read_excel_sheet` and its `_PandasReaders` Protocol are widened to `header: int | None` to support the probe read. The scope is small and well-bounded: one new module, two loader call sites, one type widening, and three test modules (one unit, two parity), plus a backward-compatible `leading_rows` keyword on the existing fixtures.

Evidence reviewed: the full branch diff (`git diff main...HEAD`), all changed source and test files, executor evidence under the feature `evidence/` tree (baseline, qa-gates, regression-testing), and an independent re-run of Black, Ruff, Pyright, and the detection + parity test subset. The implementation is correct, fully typed, deterministic, and parity-preserving. Implementation quality is high for the reviewed scope.

**What changed:**
`src/_header_detection.py` (new, 158 lines): `detect_header_row` + `_rewind_if_seekable`. `src/normalize_le.py` and `src/load_aop.py`: detect-then-read wiring with a seekable-buffer rewind before the final read. `src/pandas_io.py`: `header: int | None` on function and Protocol. `tests/test_header_detection.py` (6 tests), `tests/test_normalize_le_header.py` and `tests/test_load_aop_header.py` (2 tests each), `tests/le_fixtures.py` / `tests/aop_fixtures.py` (`leading_rows` keyword, default 2).

**Top 3 risks:**
1. Detection false-positive selecting a data row — mitigated by the `min_match` floor (LE 20/25, AOP 17/24), both above the 12 month tokens a data row could coincidentally supply, plus an explicit threshold-guard test.
2. Parity regression for the standard header-at-index-2 sheets — mitigated by the 53 pre-existing LE/AOP loader tests passing unchanged plus two `assert_frame_equal` parity tests; detection provably selects index 2 for those fixtures.
3. BytesIO buffer not rewound between the probe and final read — mitigated by the rewind in both the helper and each loader call site, with a repeated-call determinism test.

**PR readiness recommendation:** **Go** — All eight acceptance criteria are satisfied with passing tests and a clean toolchain; no Blocker or Major findings.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Nit | `src/normalize_le.py`, `src/load_aop.py` | load_source / load_aop rewind blocks | The seekable-buffer rewind is duplicated in both call sites in addition to `_rewind_if_seekable` inside the helper. The helper rewinds before the probe; the loaders rewind again before the final read. | Optional: expose the rewind as a small public helper in `_header_detection` and reuse it at both call sites to remove the inline `isinstance(..., io.IOBase) and ...seekable()` duplication. | Minor DRY improvement; current code is correct and clearly commented. Not blocking. | `git diff main...HEAD -- src/normalize_le.py src/load_aop.py` |
| Info | `src/_header_detection.py` | line 69 (`_rewind_if_seekable`) | The path/non-seekable arm of the rewind guard is not exercised by unit tests (they use BytesIO), shown as partial branch `69->exit`. | None required; documented in coverage-delta evidence. Optionally add a path-source detection test for completeness. | New-code coverage remains 97% line, above threshold; the uncovered arm is a no-op for path sources. | `evidence/qa-gates/coverage-delta.md` |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- Detection is a single shared pure function consumed by both loaders (satisfies the reuse principle and AC-3), with the read routed through the existing typed `pandas_io` boundary rather than calling pandas directly.
- The selection rule is correct and deterministic: `best_score` initialized to `-1` and a strict `>` comparison guarantee the topmost (smallest-index) row wins ties, matching the documented "topmost-highest" contract. Scoring uses set intersection of normalized tokens, so numeric data cells normalize to non-token strings and a genuine data row scores low.
- Thresholds are sound. LE `min_match=20` of 25 expected tokens and AOP `min_match=17` of 24 expected tokens (verified: AOP `SOURCE_COLUMNS` minus optional `KEY`/`YTG` = 24) both sit well above the 12 month tokens a coincidental data row could match, so a data row cannot be selected while several absent/aliased label columns are tolerated.
- The `header: int | None` widening is applied in lockstep to both the function and the `_PandasReaders` Protocol, so existing integer callers (parity tests) are unaffected and the probe read can pass `None`. Re-verified Pyright-clean.
- Fail-fast error handling: no silent fallback to `header=2`; a `ValueError` names the sheet, scan window, floor, and expected columns.

#### Typing and API notes

- `detect_header_row` is fully annotated with keyword-only `max_rows`/`min_match` and returns `int`. `expected_tokens: frozenset[str]` is immutable and appropriate. No `Any`. The new public surface is one function in an internal (`_`-prefixed) module, consumed only by the two loaders.

#### Error handling and logging

- The detection module emits no logging (documented) and raises a specific `ValueError`. Loaders retain their existing `logging` warnings. No broad exception handlers introduced.

---

## Test Quality Audit

The change adds 10 tests (suite 966 → 976), covering positive detection at index 0/2/3, the no-match ValueError (asserting both sheet name and a normalized expected column appear in the message), the coincidental-token threshold guard, BytesIO rewind determinism, and LE/AOP flat-sheet resolve plus index-0-equals-index-2 parity via `pd.testing.assert_frame_equal`. The pre-existing 53 LE/AOP loader tests pass unchanged, which is the primary parity evidence.

### Reviewed test and QA artifacts

- `tests/test_header_detection.py` — 6 unit tests on `detect_header_row`; in-memory BytesIO workbooks, AAA structure, single behavior each.
- `tests/test_normalize_le_header.py` / `tests/test_load_aop_header.py` — flat-sheet resolve + parity-equality tests; split into sibling modules to keep `test_normalize_le.py` (446) and `test_load_aop.py` (494) under the 500-line cap.
- `evidence/regression-testing/parity-le-aop.md` — 53 pre-existing LE/AOP tests pass after the wiring change, confirming detection selects index 2 for the standard layout (AC-2).
- `evidence/qa-gates/coverage-delta.md` — 98% line / ~93.9% branch; 0 missed changed statements across all four in-scope modules.
- `evidence/qa-gates/suppression-guard.md` and independent `git diff` scan — no `noqa`/`type: ignore` added.

### Quality assessment prompts

- **Determinism:** No wall-clock, randomness, network, or temp files; rewind makes repeated calls deterministic (asserted).
- **Isolation:** Each test builds its own buffer and asserts one behavior.
- **Speed:** 63-test detection+parity subset ran in 4.69s (this audit).
- **Diagnostics:** `assert_frame_equal` and message-substring assertions give actionable failures.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff contains no credentials or tokens; inspected all changed files. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess use; reads go through the typed `pandas_io`/openpyxl boundary. |
| Input validation at boundaries | ✅ PASS | Detection raises a clear `ValueError` when no header row qualifies; `min_match` floor rejects data rows. |
| Error handling remains explicit | ✅ PASS | Specific `ValueError`, no broad catch, no silent fallback. |
| Configuration / path handling is safe | ✅ PASS | `_rewind_if_seekable` rewinds only seekable buffers; path sources are reopened by pandas, no shared-position hazard. |

---

## Research Log

No external research was required. All findings are grounded in the branch diff, the feature-folder evidence artifacts, and an independent toolchain re-run.

---

## Verdict

The change is ready for normal PR flow. The implementation is correct, deterministic, fully typed, and parity-preserving, with thresholds that demonstrably reject coincidental data-row matches. The two recorded findings are a Nit (rewind duplication) and an Info (an unexercised no-op branch in the path-source rewind arm); neither blocks merge. This conclusion is consistent with the Findings Table and the Go recommendation above. Exit-gate count (FAIL + blocking-PARTIAL) is 0.
