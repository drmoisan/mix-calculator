# Feature Audit — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature
- Audit timestamp: 2026-05-26T10-03
- Auditor: feature-review agent

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: The MCP `feature-audit-template` asset is not
> available; this artifact uses the canonical five major sections per fail-closed
> guidance.

## Scope and Baseline

- Base branch (resolved): `main`
- Merge-base SHA: `2d86e836f89f43df011ed7528ac8decbd82cd761`
- Head SHA: `dc39c977cb023130409a94c369688f2dcda343c3`
- Range: `2d86e836f89f43df011ed7528ac8decbd82cd761..dc39c977cb023130409a94c369688f2dcda343c3`
- Audit type: re-audit after a behavior change. Since the prior review (`74743671`), the
  ETL extraction was made position-independent (new `src/le_columns.py`) and KEY
  create/trust/resolve handling was added (new `src/le_key.py`), with public symbols
  re-exported from `src/normalize_le.py`.

Work Mode is `full-feature` (from `issue.md` marker `- Work Mode: full-feature`).
Per the acceptance-criteria contract, the authoritative AC sources are `spec.md` (the
`## Definition of Done` section) and `user-story.md` (the `## Acceptance Criteria`
section). The `issue.md` `## Acceptance Criteria` section carries the same 13 criteria as
`user-story.md` and is tracked as a mirror.

The new behavior maps directly to five user-story / issue criteria that were still
unchecked at the start of this re-audit (column resolution, missing-column halt,
extra-column warn, `coerce_sku`, KEY handling). These are the focus of this audit.

## Acceptance Criteria Inventory

`user-story.md` `## Acceptance Criteria` (13 items, UST-1..UST-13); `issue.md`
`## Acceptance Criteria` mirrors these (ISS-1..ISS-13). `spec.md` `## Definition of Done`
(7 items, DOD-1..DOD-7).

User-story / issue criteria:
- UST/ISS-1: CLI with listed defaults; `--output` required SQLite path; SQLite only sink.
- UST/ISS-2: `header=2`; drops blank `Customer`.
- UST/ISS-3: position-independent column resolution (position pass, then normalized
  equality, then `difflib` >= 0.85); canonical rename. (was unchecked)
- UST/ISS-4: unmatched required column halts with a naming error. (was unchecked)
- UST/ISS-5: extra actual columns logged as a warning; run continues. (was unchecked)
- UST/ISS-6: `coerce_sku` integer-string rendering; non-numeric verbatim; pattern
  `Customer + coerce_sku(SKU #) + Type`. (was unchecked in user-story)
- UST/ISS-7: KEY handling (absent->created; matching->trusted; diverging->`--key-mismatch`
  with TTY prompt and non-TTY fail-fast). (was unchecked in user-story)
- UST/ISS-8: 26 columns A..Z exact order; one row per KEY; first-appearance; `YTD/YTG`
  absent; derived `YTG` after `Q4` before `Super Category`.
- UST/ISS-9: text from first row per KEY; `Jan..Dec`/`FY`/`Q1..Q4` summed (blanks as 0).
- UST/ISS-10: `YTG = sum(May..Dec)` on the output row.
- UST/ISS-11: `Super Category` and `PPG` both from source `PPG` (quirk), identical.
- UST/ISS-12: validation (row-count, `1e-6` tie-outs, `FY == sum(months)`); fail non-zero.
- UST/ISS-13: stdout summary; SQLite persist via `to_sql(if_exists="replace",
  index=False)` (the user-story splits these across two checkboxes; tracked together).

Definition of Done (spec.md): DOD-1 AC documented and mapped to tests; DOD-2 behavior
matches AC; DOD-3 tests added; DOD-4 edge/error cases covered; DOD-5 docs updated; DOD-6
telemetry/logging; DOD-7 toolchain pass.

## Acceptance Criteria Evaluation

| ID | Criterion (abbrev.) | Verdict | Evidence |
|---|---|---|---|
| UST/ISS-1 | CLI defaults; `--output` required; SQLite-only | PASS | `src/normalize_le.py:402-439` (`--output required=True`, choices/defaults), `442-479` (`write_sqlite` only sink); `tests/test_normalize_le_io.py:216-221` (missing `--output` non-zero), `309-339` (custom sheet/table) |
| UST/ISS-2 | `header=2`; blank-`Customer` drop | PASS | `src/normalize_le.py:168-206`; `tests/test_le_columns.py:136-149`; load tests in `tests/test_normalize_le.py` |
| UST/ISS-3 | Position-independent resolution + canonical rename | PASS | `src/le_columns.py:60-204` (position pass, normalized-equality, `difflib` >= 0.85), `src/normalize_le.py:182-199` (select + rename to canonical); `tests/test_le_columns.py:47-93, 136-149` (exact, reordered, trailing-space, fuzzy typo) |
| UST/ISS-4 | Unmatched required column halts naming it | PASS | `src/le_columns.py:191-197` (`ValueError` names unmatched); `tests/test_le_columns.py:96-104, 119-128`; `tests/test_normalize_le_io.py:224-243` (CLI non-zero naming `PPG`) |
| UST/ISS-5 | Extra columns warned; run continues | PASS | `src/le_columns.py:199-204` (returns extras), `src/normalize_le.py:188-189` (`logger.warning`); `tests/test_le_columns.py:106-116, 152-168` |
| UST/ISS-6 | `coerce_sku` rendering; rebuilt pattern | PASS | `src/le_key.py:37-103`; `tests/test_normalize_le.py` (`coerce_sku` matrix + integer property, `rebuild_key`) |
| UST/ISS-7 | KEY handling (create/trust/resolve; TTY prompt; non-TTY fail-fast) | PASS | `src/le_key.py:127-262` (`decide_key_action`, `resolve_key`); `tests/test_le_key.py:43-209` (all branches, injected `is_tty`/`prompt`); `tests/test_normalize_le_io.py:246-306` (CLI prompt non-TTY non-zero; overwrite succeeds) |
| UST/ISS-8 | 26 columns exact order; one row/KEY; first-appearance; derived `YTG` placement | PASS | `src/normalize_le.py:107-120` (`TARGET_COLUMNS`), `236-278` (`normalize`, `groupby(sort=False)`); `tests/test_normalize_le.py` (column order, first-appearance, no `YTD/YTG`) |
| UST/ISS-9 | First-row text; summed numerics (blanks as 0) | PASS | `src/normalize_le.py:253-269`; `tests/test_normalize_le.py` (2-row pair, 3+ rows NaN-as-0) |
| UST/ISS-10 | `YTG = sum(May..Dec)` on output | PASS | `src/normalize_le.py:219-233, 273` (`compute_ytg`); `tests/test_normalize_le.py` (`compute_ytg` + property) |
| UST/ISS-11 | Super Category/PPG quirk identical | PASS | `src/normalize_le.py:274-275`; `tests/test_normalize_le.py` (quirk invariant test asserts both equal source `PPG`) |
| UST/ISS-12 | Validation (row-count, `1e-6`, `FY==sum`) non-zero on fail | PASS | `src/normalize_le.py:281-326` (`validate_tieouts`); `tests/test_normalize_le_io.py:42-132` (pass + 3 failure paths + property) |
| UST/ISS-13 | stdout summary + SQLite persist semantics | PASS | `src/normalize_le.py:329-358` (`write_sqlite` replace/no-index), `361-399` (`print_summary`); `tests/test_normalize_le_io.py:140-213, 347-363` (round-trip columns/order/rows, replace-no-duplication, stdout lines, empty-output branch) |
| DOD-1 | AC documented and mapped to tests | PASS | spec.md `## Definition of Done` maps each criterion to a named test; mapping confirmed against the test files above |
| DOD-2 | Behavior matches AC in documented environments | PASS | All 72 tests pass (auditor run); behavior verified against each criterion above |
| DOD-3 | Tests added (unit/integration) | PASS | Four test modules added (1174 test lines across `test_le_columns`, `test_le_key`, `test_normalize_le`, `test_normalize_le_io`) |
| DOD-4 | Edge/error cases covered | PASS | Negative paths: missing column, extra column, unrelated-column-not-bound, tie-out failures, FY mismatch, missing `--output`, non-TTY prompt; edge: reordered/typo columns, NaN-as-0, singleton/3+ keys, empty output |
| DOD-5 | Docs updated | PASS | `README.md` usage section; feature docs (spec, user-story, issue, plan) present in the diff |
| DOD-6 | Telemetry/logging | PASS | stdlib `logging` warnings for extra columns (`src/normalize_le.py:189`) and trust/overwrite KEY resolution (`src/le_key.py:251-260`); tie-out summary via `print` by design |
| DOD-7 | Toolchain pass (format/lint/type/test) | PASS | Auditor re-ran all four stages clean (policy-audit Section 7 / Appendix B) |

No criterion is FAIL, PARTIAL, or UNVERIFIED. The suppression-authorization PARTIAL in
the policy audit is a cross-cutting policy item; it does not unmet any individual
acceptance criterion (every criterion's behavior is implemented and tested), so it does
not change an AC verdict here, but it is the reason remediation is triggered overall.

## Summary

All 13 user-story/issue acceptance criteria and all 7 Definition-of-Done items are PASS.
The five previously-unchecked user-story criteria (UST/ISS-3 through UST/ISS-7), which
correspond to the new position-independent extraction and KEY-mismatch behavior, are
implemented, deterministically tested (injected interactivity, no real stdin, no temp
files), and covered at 100% line/branch on the new source modules. The feature is
behaviorally complete relative to the baseline.

PR readiness from the feature-audit perspective: the acceptance criteria are met. The
overall review verdict is PARTIAL only because of the suppression-authorization
procedural gap recorded in the policy audit and routed to remediation; that gap is not a
behavioral or acceptance-criteria defect.

## Acceptance Criteria Check-off

The five previously-unchecked PASS criteria in `user-story.md` (UST-3..UST-7) are checked
off in that source file as part of this audit, per `acceptance-criteria-tracking`. The
corresponding `issue.md` mirror items were already `[x]`. The `spec.md` Definition-of-Done
items were already `[x]`. No criterion was downgraded.

### Acceptance Criteria Status
- Source: `docs/features/active/2026-05-25-etl-le-topline-input-2/user-story.md` (13),
  `docs/features/active/2026-05-25-etl-le-topline-input-2/spec.md` Definition of Done (7),
  `docs/features/active/2026-05-25-etl-le-topline-input-2/issue.md` mirror (13)
- Total AC items (user-story): 13
- Checked off (delivered): 13 (5 newly checked off this audit: UST-3, UST-4, UST-5,
  UST-6, UST-7; 8 already checked)
- Remaining (unchecked): 0
- Items remaining: none
