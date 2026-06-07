# Code Review: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 3 EXIT Reaudit

**Review Date:** 2026-06-05
**Timestamp:** 2026-06-05T23-23
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `cc5b282` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature
**Scope:** full branch diff `main...HEAD`; cycle-3 delta `fd8a022..cc5b282`

## Executive Summary

Cycle 3 remediated a post-PR runtime crash reported in the field: activating a source tab raised `KeyError: 'Worksheet  does not exist.'` because the schema-discovery wiring fired `currentTextChanged` during combo population — before a worksheet was selected — and the reader was called with a blank sheet. The fix has two coupled parts: B1 (guard discovery against a blank/whitespace path or sheet) and B2 (make the reader raise `ValueError` rather than `KeyError` for an absent sheet so the presenter's existing ValueError-only error policy routes it to the view instead of crashing).

The cycle-3 commit diff (`fd8a022..cc5b282`) touches three production files (`source_selection_presenter.py`, `_schema_discovery_wiring.py`, `workbook_reader.py`) and three test files. The changes are small, well-scoped, fully typed, and documented; no `.py` file exceeds 500 lines and no suppressions were introduced.

B1 is closed: `on_schema_discovery` returns early on a blank/whitespace path or sheet (`source_selection_presenter.py:233-235`), and `_on_tab_activated` short-circuits the same way as defense in depth (`_schema_discovery_wiring.py:131-138`). The proof is wiring-level — the new tests drive the real `tab_combo.currentTextChanged` signal over a `MainWindow`/`build_application` composition, not isolated presenter calls.

B2 is closed: `read_sheet_preview` checks `sheet_name not in workbook.sheetnames` and raises `ValueError` inside the `try` (so the `finally` still closes the workbook), and both the `WorkbookReaderProtocol` and `WorkbookReader` docstrings were updated from `KeyError` to `ValueError`.

One blocking finding remains and it is **not a code-quality defect in the cycle-3 diff**: the full pytest suite is RED (940 pass, 1 fail) because of a pre-existing `col`-shadowing defect in `src/schema_formula.py` (out of cycle-3 scope; not in the branch diff). It is recorded as a blocking finding below for completeness because a RED suite blocks merge, and attributed to the formula engine, not to B1/B2.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|----------|------|----------|---------|----------------|-----------|----------|
| Blocking | src/schema_formula.py | 301-307 (`_build_symtable`); surfaced by tests/test_schema_formula.py:306 | The symbol table seeds the whitelisted `col` callable, then the alias-binding loop `symtable[alias] = context[column]` overwrites `symtable["col"]` when a source column is literally named `col`, so `col(name)` evaluates `0.0(...)` and raises `TypeError: '0.0' is not callable`. The full suite is RED, which blocks merge. | Bind the `col` accessor (and other whitelisted names) AFTER the alias loop, or skip aliasing any column whose alias collides with a reserved whitelisted name. Then re-run the toolchain to green. | A RED suite is a blocking merge/CI condition regardless of cause. This defect is pre-existing and out of cycle-3 scope — `src/schema_formula.py` and `tests/test_schema_formula.py` are NOT in the `main...HEAD` diff — so it is attributed to the formula engine, NOT to the B1/B2 changes. | `pytest` -> `1 failed, 940 passed`; `git diff --stat main...HEAD -- src/schema_formula.py` is empty; falsifying example `{'col': 0.0}`. |

## Best-Practices Review

| Area | Status | Evidence |
|------|--------|----------|
| Guard placement (B1) | PASS | Guard in `on_schema_discovery` makes the presenter contract safe for ANY caller; the `_on_tab_activated` short-circuit is documented defense-in-depth that also avoids an unnecessary call. Both docstrings updated to state the no-op. |
| Error-contract clarity (B2) | PASS | `read_sheet_preview` now raises a specific `ValueError` naming the missing sheet, replacing a leaking `KeyError`; the conversion is inside `try` so the `finally` still closes the workbook. Both protocol and impl `Raises:` sections updated in lockstep. |
| Fail-fast / specific exceptions | PASS | The chosen contract (reader raises ValueError) aligns with the presenter's existing `on_file_selected`/`on_render_tab`/`on_schema_discovery` ValueError-only policy; no broad except introduced. |
| Wiring-level test fidelity | PASS | B1 proofs drive the real `tab_combo.currentTextChanged` signal (`test_tab_activation_no_file_selected_does_not_call_reader`, `test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet`); AC-2 proof builds the real composition root via `build_application`. These are integration tests, not isolated presenter mocks that pre-set a valid sheet. |
| No-regression (prior seams) | PASS | Drag Columns/Key tabs, derived dialog, `BuildSpecProvider`, `new_from_template`, and `on_partial_match` remain wired at `app.py:327-430`, `schema_builder_dialog.py:98`, and `_schema_open_helpers.py`; cycle-3 diff touches none of them. AC-2 auto-select confirmed by the `build_application` test. |
| File-size discipline | PASS | No changed `.py` file in the branch diff exceeds 500 lines (file-size scan over `main...HEAD`). |
| Suppressions | PASS | No `noqa`/`type: ignore`/`pyright: ignore`/`# pragma: no cover` added to any code file in `fd8a022..cc5b282` (the only diff matches are documentation prose). Pre-existing test `# type: ignore[arg-type/misc]` on Qt drag-event stubs are from cycle 1/2, not this cycle. |
| Typing | PASS | Pyright strict 0 errors; cycle-3 changes fully annotated. |
| Coverage on changed code | PASS | `_schema_discovery_wiring.py` 100% line, `source_selection_presenter.py` 99% line, `workbook_reader.py` 100% line (live per-module re-run at HEAD `cc5b282`). |
| Confidentiality | PASS | Masking scan over cycle-3 changed lines reports no secrets/PII/real values; test fixtures use fabricated names (`Customer`, `Sales`, `book.xlsx`). |
| Tonality | PASS | Cycle-3 docstrings/comments free of prohibited hyperbole/humor. |

## Verdict

**REQUEST CHANGES (1 blocking, pre-existing/out-of-scope).** The cycle-3 B1/B2 code changes are clean, minimal, well-tested at the wiring level, and introduce no code-quality defects; AC-2 is preserved. The single blocking finding is the RED suite caused by the pre-existing `col`-shadowing defect in `src/schema_formula.py:301-307`, which is out of cycle-3 scope and must be fixed in the next cycle before merge. The cycle-3 B1/B2 objectives themselves are met independent of that pre-existing failure.
