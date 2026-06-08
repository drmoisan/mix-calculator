# Phase 5 — Acceptance-Criteria Verification (Issue #55)

Timestamp: 2026-06-07T02-36

AC source (work mode: full-bug): `spec.md` (canonical), mirrored in `issue.md`.

| AC | Criterion | Satisfying evidence | Result |
|----|-----------|---------------------|--------|
| AC-1 | LE sheet with header on index 0 resolves columns, no "Source schema mismatch" | `test_normalize_le_header.py::test_flat_sheet_header_at_index_zero_resolves_columns`; full suite final-pytest.md (976 passed) | PASS |
| AC-2 | Standard `LE-8 + 4`/`AOP1` (header index 2) still load; detection selects 2; parity preserved | regression-testing/parity-le-aop.md (53 passed); `test_*_header.py` index-0/index-2 parity asserts | PASS |
| AC-3 | Header detection shared between LE and AOP via a single helper | `src/_header_detection.detect_header_row`, imported by both `normalize_le.load_source` and `load_aop.load_aop` | PASS |
| AC-4 | No resolvable header raises clear ValueError naming sheet and expected columns | `test_header_detection.py::test_no_qualifying_row_raises_value_error_naming_sheet_and_columns`; ValueError message in `_header_detection.py` | PASS |
| AC-5 | Deterministic; rejects a data row with a few coincidental tokens (threshold guard) | `test_header_detection.py::test_data_row_with_few_coincidental_tokens_below_threshold_not_selected` and `::test_bytesio_rewind_makes_repeated_calls_deterministic` | PASS |
| AC-6 | `read_excel_sheet` accepts `header=None` for probe; existing integer callers unaffected | `pandas_io.py` `header: int | None` (fn + Protocol); final-pyright.md (0 errors); parity-le-aop.md | PASS |
| AC-7 | All changed/added files <= 500 lines | qa-gates/file-size-guard.md (max 494) | PASS |
| AC-8 | Full toolchain pass + coverage >= 85% line / >= 75% branch, no regression on changed lines | final-black/ruff/pyright/pytest.md; coverage-delta.md (98% line, ~93.9% branch, 0 missed changed stmts) | PASS |

Verdict: every acceptance criterion maps to passing evidence (AC-1..AC-8 PASS).
