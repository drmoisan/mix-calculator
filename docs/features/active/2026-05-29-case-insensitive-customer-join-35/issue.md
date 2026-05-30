# case-insensitive-customer-join (Issue #35)

- Date captured: 2026-05-29
- Author: Dan Moisan
- Status: Active -> docs/features/active/2026-05-29-case-insensitive-customer-join-35/
- Issue: #35
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/35
- Last Updated: 2026-05-29
- Work Mode: minor-audit
- Promotion Type: feature

## Summary

Make the mix-decomposition pipeline robust to case-only and
whitespace-only differences in the `Customer` column between the AOP
and LE sources. Joining `Customer` is currently case-sensitive and
whitespace-sensitive, which produces silently-split per-SKU rate
components when the same Customer name is recorded with different
casings on the two sides of the comparison.

This work is a follow-up to a diagnostic session that traced the
`nrr_summary.Check = ERROR` outcome from
`artifacts/Input Files.xlsx` to two Winco SKUs (69005 and 69007) whose
LE-side Off Invoice $ and Non-Trade $ deduction rows are filed under
`WINCO` (uppercase) while the matching AOP rows use `Winco` (title
case). The orphaned rows contribute $63,995.25 of LE-side deductions
that never reach the per-SKU `rate_impacts` build-up but do count in
the topline SUMIF. The realization and the build-up therefore differ
by exactly that amount, and the `Check` row correctly reports the
inconsistency.

This is a small-path, minor-audit feature. AC source is this issue.md
(per minor-audit convention). Branched off PR #34's HEAD; the
modified files (`src/mix_lookups.py`, `tests/test_mix_lookups.py`)
are disjoint from #34's changes.

## Environment

- OS: Windows 10/11
- Python: 3.12 - 3.13
- Pandas: ^2.2
- Affected modules: `src/mix_lookups.py` only (production)
- Affected tests: `tests/test_mix_lookups.py` (modified)

## Scope

In scope:

- Add a Customer-key normalization helper in `src/mix_lookups.py`
  that yields a canonical join key via
  `.str.strip().str.casefold()`.
- Apply the helper in `build_aop_norm`, `build_le_norm`, and
  `build_aop_vs_le` so the AOP/LE merge becomes case-insensitive
  and whitespace-insensitive.
- Apply `.str.strip()` to the `Customer` column in
  `build_customer_lu` so the displayed lookup is consistent with
  `aop_vs_le`.
- On the displayed `Customer` column in `aop_vs_le`, prefer the
  AOP-side casing when both sides match; fall back to the LE-side
  casing for LE-only orphans. The original Customer string is
  preserved (no `.title()` / `.upper()` mutation).
- New tests covering: identical-customer different-case rows merge,
  whitespace-only differences merge, AOP-side casing wins on
  display, LE-only Customer retains LE casing, the canonical
  workbook regresses zero rows, and the Winco/WINCO end-to-end
  fixture reaches `Check = CHECK`.

Out of scope:

- Modifying the loaders (`src/normalize_le.py`, `src/load_aop.py`).
- Normalizing `SKU #`, `Country`, `Category`, or any other join
  key. The reported failure is Customer-specific; broader
  normalization is a separate follow-up if needed.
- Modifying `build_mix_base` (it joins on SKU only, and inherits
  the normalized Customer column transparently).
- Changes to the CLI surface or the GUI.

## Acceptance Criteria

- [x] AC1: A new module-private helper in `src/mix_lookups.py`
      produces the canonical Customer join key via
      `.str.strip().str.casefold()`. The helper is a pure function
      on `pd.Series[str]` and has a Google-style docstring.
- [x] AC2: `build_aop_norm` and `build_le_norm` apply `.str.strip()`
      to the emitted `Customer` column (preserving original casing,
      removing leading/trailing whitespace).
- [x] AC3: `build_aop_vs_le` performs its pivot/merge on the
      casefolded Customer join key so that AOP `Winco` and LE
      `WINCO` (and any whitespace variants) merge into one
      `(Customer, SKU)` pair in the output. The output frame's
      displayed `Customer` column carries the AOP-side casing when
      both sides match. When only the LE side has a row, the
      LE-side casing is preserved.
- [x] AC4: `build_customer_lu` applies `.str.strip()` to the
      `Customer` column so its display is consistent with
      `aop_vs_le`.
- [x] AC5: A regression test exercises the Winco/WINCO scenario
      end-to-end with a synthetic fixture (no external xlsx
      dependency): AOP has `('Winco', 69005)` with Off Invoice $
      and Non-Trade $ deductions; LE has `('WINCO', 69005)` with
      the same deductions and `('Winco', 69005)` with Gross Sales
      and Lbs. The test asserts the resulting `aop_vs_le` has
      exactly one `(Customer, SKU)` row per attribute keyed on
      `Winco`.
- [x] AC6: Unit tests cover, individually:
      (a) identical Customer values with different casings
          (`'Winco'`, `'WINCO'`, `'winco'`) merge to one key;
      (b) trailing-only whitespace (`'Winco '`) and leading-only
          whitespace (`' Winco'`) merge to the same key as `'Winco'`;
      (c) AOP-side casing wins on display when both sides match;
      (d) LE-only Customer (no AOP counterpart) retains LE casing
          on display;
      (e) the join key is independent of the original `Customer`
          string (a single Customer with five different casings in
          a frame produces one output row per attribute).
- [x] AC7: Existing tests in `tests/test_mix_lookups.py` continue
      to pass without modification of their assertions. The
      canonical end-to-end pipeline run against
      `artifacts/LE v AOP Gross to Net Decomp.xlsx` produces an
      identical `nrr_summary` (including `Check = CHECK`).
- [x] AC8: Coverage on `src/mix_lookups.py` remains >= 85% line and
      >= 75% branch (uniform thresholds per
      `.claude/rules/quality-tiers.md`).
- [x] AC9: `src/mix_lookups.py` and `tests/test_mix_lookups.py`
      each remain under the 500-line cap.
- [x] AC10: Full mandatory Python toolchain passes in a single
      loop: Black -> Ruff -> Pyright -> Pytest. No new suppressions
      introduced beyond pre-authorized patterns.

## Design Notes (for the planner)

- **Normalization rule.** `.str.strip().str.casefold()` is the
  chosen rule. `casefold` is preferred over `lower` because it
  handles non-ASCII letterforms (Turkish 'I', German 'ß', etc.)
  correctly. None of the canonical customers in the training
  workbook are non-ASCII, but the broader robustness is free and
  the standard pandas idiom.
- **Display casing precedence.** AOP wins on display because AOP
  is the planning baseline. Implementation: after the
  pivot-on-casefolded-key, re-attach the canonical Customer
  display via a left-join on the casefolded key. AOP-side display
  values take priority; LE-side display values fill where the
  casefolded key has no AOP match.
- **No surface change.** The output columns of `build_aop_norm`,
  `build_le_norm`, `build_aop_vs_le`, and `build_customer_lu`
  remain identical to the current contract (same column names,
  same types). The only observable change is that rows previously
  split across different casings now merge.
- **Pivot mechanics.** The current `build_aop_vs_le` pivots on
  `["Customer", "SKU #", "Attribute"]`. The new implementation
  pivots on the casefolded key, then re-attaches the display
  `Customer`.

## Test Strategy

- Unit tests only against synthetic in-memory fixtures (no real
  workbook reads in unit tests, per existing repo policy).
- An end-to-end smoke test verifies the canonical training
  workbook still produces `Check = CHECK`. If the existing test
  suite does not already exercise this end-to-end path, a small
  new test is added.

## Reference Artifacts

- Bug diagnosis (this conversation): root cause is a Customer-name
  casing inconsistency in `artifacts/Input Files.xlsx` LE-8 + 4
  sheet for Winco SKUs 69005 and 69007. The pipeline correctly
  detected the inconsistency ($63,995.25 mismatch between
  realization and build-up Price/Mix).
- Casefold-collision probe (run during scoping): 22 distinct
  customers in the canonical training workbook produce zero
  casefold-collisions, confirming the normalization is safe.

## Out-of-Scope Follow-ups (tracked elsewhere if needed)

- Normalizing other join keys (Country, Category) if similar
  inconsistencies emerge.
- Loader-level canonicalization at read time (would simplify the
  downstream chain but expands the touch surface).
- A data-quality lint pass that flags input-side casing
  inconsistencies as a `WARNING` log at import time.
