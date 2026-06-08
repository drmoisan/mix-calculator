# le-loader-required-vs-output-columns (Issue #57)

- Date captured: 2026-06-07
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/le-loader-required-vs-output-columns/ (Issue #57)

- Issue: #57
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/57
- Last Updated: 2026-06-08
- Work Mode: full-bug

## Problem / Why

After header-row detection (#55) resolves the header correctly, importing an LE
sheet that lacks the intermediate `YTD/YTG` discriminator column still fails:

```
ValueError: Source schema mismatch: could not resolve required column(s):
['YTD/YTG']. Actual columns: ['Customer', 'SKU Descripiton', 'SKU #', 'Type',
'GtN Mapping', 'Jan', ... 'Q4', 'YTG', 'Super Category', 'PPG'].
```

The protected LE loader (`src/normalize_le.load_source` via
`src/_normalize_le_columns.resolve_le_columns`) requires every source column
except `KEY` (`EXPECTED_COLUMNS = SOURCE_COLUMNS - {KEY}`), including columns that
are not part of the final output and are never read for output:

- `YTD/YTG` is required but is dropped — `normalize()` emits `TARGET_COLUMNS`
  (which excludes it) and never reads it (`src/normalize_le.py:223-265`).
- `Super Category` (source) is required but ignored — `normalize()` sets the
  output `Super Category` from the source `PPG` column
  (`output["Super Category"] = first_rows["PPG"]`), so the source `Super Category`
  value is never used.

This is the same "required only to be deleted" anti-pattern fixed for the
schema-driven loader in #54 (`ColumnSpec.in_output`), but the protected
`normalize_le` loader was not changed by #54.

## Proposed Behavior

- The protected LE loader requires only the "must-have" source columns that
  contribute to the final output. Intermediate/derived-overwritten columns are
  located by name if present (and dropped/ignored) but are NOT required.
- Must-have (required) LE source columns: `Customer`, `SKU Descripiton`, `SKU #`,
  `Type`, `GtN Mapping`, `Jan`..`Dec`, `FY`, `Q1`..`Q4`, `PPG`.
- Optional/intermediate (not required; located by name; tolerated if absent):
  `YTD/YTG` (dropped), `Super Category` (output is derived from `PPG`). `KEY`
  remains optional/created as today.
- A source missing a genuine must-have column still fails with a clear error.

## Acceptance Criteria

Canonical AC list (mirrors spec.md v1.0):

- [x] AC-1: An LE sheet without a `YTD/YTG` column imports successfully (no
      "could not resolve required column(s): ['YTD/YTG']" error).
- [x] AC-2: An LE sheet without a source `Super Category` column imports
      successfully; output `Super Category` is still derived from `PPG`.
- [x] AC-3: The protected LE loader requires only the 23 must-have source columns
      (`Customer`, `SKU Descripiton`, `SKU #`, `Type`, `GtN Mapping`, `Jan`..`Dec`,
      `FY`, `Q1`..`Q4`, `PPG`); `YTD/YTG` and source `Super Category` are optional
      (located by name, carried if present, tolerated if absent).
- [x] AC-4: The standard `LE-8 + 4` source (with `YTD/YTG` + `Super Category`
      present) produces byte-identical output to today (parity; existing LE loader
      tests pass).
- [x] AC-5: A source missing a genuine must-have column raises a clear
      column-resolution error naming the missing column.
- [x] AC-6: A flat LE sheet (header row 0, no `YTD/YTG`, no `KEY`) imports to the
      full `TARGET_COLUMNS` set.
- [x] AC-7: `load_aop` is unchanged; AOP imports unaffected.
- [x] AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage
      >= 85% line / >= 75% branch and no regression on changed lines; all files
      <= 500 lines.

## Constraints & Risks

- Parity: standard LE source output must not change.
- Scope: protected LE loader only; confirm whether `load_aop` has any
  required-only-to-drop column (likely none) via research.
- This change is folded into the open #55 branch/PR (robust LE import) so the
  non-standard-sheet import works end-to-end.

## Test Conditions to Consider

- [ ] Unit: resolve_le_columns requires must-have only; YTD/YTG and Super
      Category optional (present-and-carried, absent-and-tolerated).
- [ ] LE loader parity for the standard source (YTD/YTG + Super Category present).
- [ ] Integration: load_source of a YTD/YTG-less sheet yields TARGET_COLUMNS.
- [ ] Negative: a missing must-have column raises.

## Next Step

- [ ] Promote to GitHub issue
- [ ] Create active feature folder from the template