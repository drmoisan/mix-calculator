# Remediation Inputs — schema-builder-ux-overhaul (Issue #50) — Cycle 4 Entry

- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main`; Head: `cc5b282`; Merge-base: `5e659f2`; PR #51 (open)
- Source: cycle-3 EXIT reaudit (`policy-audit.2026-06-05T23-23.md`).
- Timestamp: 2026-06-05T23-23
- Consolidated blocking_count (entry): 1 blocking defect (pre-existing, out of cycle-3 scope).

## Status of Prior Cycle (cycle 3)

Cycle-3 objectives B1 and B2 are MET (closed) and are NOT carried forward:

- B1 (closed): `on_schema_discovery` (`src/gui/presenters/source_selection_presenter.py:233-235`) and `_on_tab_activated` (`src/gui/_schema_discovery_wiring.py:131-138`) no-op on a blank/whitespace path or sheet; proven by wiring-level integration tests driving the real `tab_combo.currentTextChanged` / `build_application` path.
- B2 (closed): `read_sheet_preview` (`src/gui/services/workbook_reader.py:164-165`) raises `ValueError` for an absent/blank sheet (workbook still closed by `finally`); both protocol and impl docstrings updated; presenter routes it to `show_error` without crashing.
- AC-2 re-confirmed (no regression): `test_ac2_full_match_through_build_application_auto_selects_and_enables`.

## Remediation-Required Findings (blocking)

### C1 — Formula engine `col`-shadowing defect (pre-existing, out of cycle-3 scope)

- Symptom: the full pytest suite is RED (940 pass, 1 fail). A RED suite is a blocking merge/CI condition.
- Failing test: `tests/test_schema_formula.py::test_property_col_round_trips_values` (line 306), a Hypothesis property test.
- Falsifying example: `values={'col': 0.0}` -> `FormulaError: failed to evaluate formula 'col(name)': ... TypeError: '0.0' is not callable`.
- Root cause: `src/schema_formula.py._build_symtable` (`src/schema_formula.py:301-307`) seeds the whitelisted `col` callable into the symbol table (line 304), then the alias-binding loop `symtable[alias] = context[column]` (lines 306-307) overwrites `symtable["col"]` with the column value when a source column is literally named `col`. The whitelisted helper is then shadowed by a scalar, so `col(name)` evaluates `0.0(...)`.
- Attribution: this defect is in `src/schema_formula.py`, which is NOT in the `main...HEAD` branch diff (`git diff --stat main...HEAD -- src/schema_formula.py` is empty). It predates the feature branch and is NOT attributable to the cycle-3 B1/B2 changes. It is a latent formula-engine defect surfaced by the property test.

- Suggested fix (next cycle): preserve the whitelisted callables against column-name collisions. Options:
  - Bind the whitelisted callables (`safe_div`, `sum`, `col`) AFTER the alias-binding loop so a column named `col`/`sum`/`safe_div` cannot overwrite the helper; or
  - In the alias loop, skip (or rename) any alias that collides with a name in `WHITELISTED_FUNCTIONS`, and ensure `col(name)` still resolves the exact-name value via the `context`-bound accessor; and
  - Add a regression test asserting a column literally named `col` (and `sum`) round-trips through `col("col")` without shadowing the helper.
- Acceptance: `tests/test_schema_formula.py::test_property_col_round_trips_values` passes; the full suite is green (`pytest` EXIT 0); no new suppressions; `src/schema_formula.py` stays <= 500 lines; coverage thresholds hold.

## Verification on Re-Review (cycle 4 EXIT)

- Full toolchain green: Black/Ruff/Pyright (already green at `cc5b282`) AND Pytest EXIT 0 (no failures).
- Coverage line >= 85% / branch >= 75%, no regression on changed lines.
- Masking scan clean; no new file over 500 lines; no unauthorized suppressions.
- No `.github/workflows/**` or `scripts/benchmarks/**` change.
- Confirm B1/B2 (cycle 3) and prior R1–R6 wiring remain intact and AC-2 still auto-selects for a real match.
