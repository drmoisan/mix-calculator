# loader-header-row-detection (Issue #55)

- Date captured: 2026-06-06
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/loader-header-row-detection/ (Issue #55)

- Issue: #55
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/55
- Last Updated: 2026-06-07
- Work Mode: full-bug

## Problem / Why

Importing an LE source through the GUI fails with a column-resolution error when
the source sheet's header is not on Excel row 3:

```
ValueError: Source schema mismatch: could not resolve required column(s):
['YTD/YTG', 'Customer', 'SKU Descripiton', 'SKU #', 'Type', 'GtN Mapping', ...].
Actual columns: ['Able Sales Company33105Gross Sales', 'Able Sales Company',
'Lightly Breaded Tallow-Fried Nuggets 20oz', '33105', 'Gross Sales',
'Gross Sales.1', '0', '0.1', ...].
```

The "actual columns" are data values (note pandas' `.1`/`.2` dedup suffixes on
repeated numbers), which means the sheet was read with the header on a data row.

Root cause: `src/normalize_le.load_source` and `src/load_aop.load_aop` both
hardcode `read_excel_sheet(..., header=2)` (treat Excel row 3 as the header).
The standard pipeline sheets (`LE-8 + 4`, `AOP1`, `GS YTD April + YTG 5.8`) do
have their header on row index 2, but other real sheets do not — e.g. the flat
`LE84Data` sheet has its header on row index 0. Reading such a sheet with
`header=2` lands on a data row, so column resolution fails.

Evidence (probe across artifacts/*.xlsx, 2026-06-06): `LE-8 + 4`/`AOP1`/`GS YTD`
sheets -> header at row index 2; `LE84Data` -> header at row index 0. The GUI
exposes no header-row selection for the default LE/AOP import path, so the
hardcoded `header=2` is the only behavior.

## Proposed Behavior

- The LE and AOP loaders locate the header row by detection rather than a
  hardcoded index: scan the first N rows and pick the row that matches the
  expected canonical column names (normalized), then read with that header.
- Detection picks row index 2 for the standard sheets (preserving current
  behavior and parity) and row index 0 for flat sheets like `LE84Data`.
- A sheet whose header cannot be located still fails with a clear, actionable
  error.

## Acceptance Criteria

Canonical AC list (mirrors spec.md v1.0):

- [x] AC-1: Importing an LE sheet whose header is on Excel row 1 (index 0)
      resolves columns and completes without the "Source schema mismatch" error.
- [x] AC-2: The standard `LE-8 + 4` and `AOP1` sheets (header at index 2) still
      load correctly; detection selects index 2 and loader output is unchanged
      (parity preserved; existing LE/AOP loader tests pass).
- [x] AC-3: Header detection is shared between the LE and AOP loaders via a
      single helper.
- [x] AC-4: A sheet with no resolvable header row within the scan window raises a
      clear `ValueError` naming the sheet and the expected columns (no silent
      fallback).
- [x] AC-5: Detection is deterministic and rejects a data row that coincidentally
      contains a few expected tokens (threshold guard).
- [x] AC-6: `read_excel_sheet` accepts `header=None` for the probe read; existing
      `header=2` callers are unaffected.
- [x] AC-7: All changed/added files remain <= 500 lines.
- [x] AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Constraints & Risks

- Parity: the protected loaders' existing outputs for the standard sheets must
  not change (detection must select the same header row, index 2, for them).
- Detection must be deterministic and robust against a data row coincidentally
  matching expected tokens (require a minimum match count; first match wins).
- Scope: confirm whether the schema-driven reader (`schema.header_row`) and any
  GUI header-row affordance should also benefit (research).

## Test Conditions to Consider

- [ ] Unit: detect header at row 0, row 2; no-match raises; min-threshold guard.
- [ ] LE/AOP loader parity unchanged for header-at-row-2 fixtures.
- [ ] Integration: LE import of a header-at-row-0 sheet resolves columns.

## Next Step

- [ ] Promote to GitHub issue
- [ ] Create active feature folder from the template