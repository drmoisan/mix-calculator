---
name: issue2-file-size-watch
description: issue #2 normalize-le test module sits near the 500-line limit; defect-fix coverage pushed test_normalize_le.py over it
metadata:
  type: project
---

For issue #2 (etl-le-topline-input) the test suite is split across
`tests/test_normalize_le.py`, `tests/test_normalize_le_io.py`,
`tests/le_fixtures.py`, `tests/test_le_key.py`, `tests/test_le_columns.py`, and
`src/normalize_le.py` sits at exactly 495 lines (the module was deliberately
factored into `le_columns`/`le_key`/`le_totals`/`pandas_io` to stay under 500).

**Fact:** The 2026-05-26T16-50 re-audit (defect fix at head `636c493`, blank
FY/quarter total fill via new `src/le_totals.py` + per-row Qn validation) found
`tests/test_normalize_le.py` had grown to **532 lines**, over the 500-line hard
limit (which applies to test code). Everything else was clean: zero suppressions,
100% line/branch coverage, all toolchain green, confidentiality clean
(`artifacts/` is gitignored so the confidential `.xlsx`/`.db` are untracked).
Verdict was PARTIAL/remediation for the single file-size FAIL.

**Why:** Adding the four blank-total tests tipped an already-large module over the
limit. The remediation routes to splitting the module with no coverage/assertion loss.

**Resolved (2026-05-26T17-05 re-audit, head `ac098a9`):** The `fill_blank_totals`
tests were moved verbatim into a new `tests/test_normalize_le_totals.py` (121 lines);
`tests/test_normalize_le.py` is now 436 lines. Every src/test file is < 500. Test
count unchanged (77), coverage unchanged (100% line/branch), zero suppressions,
confidentiality clean, full toolchain green (reviewer-run). Verdict: **PASS / GO**,
zero blocking findings — no remediation-inputs produced.

**How to apply:** When re-auditing issue #2 after any test addition, always run
`wc -l tests/*.py src/*.py` — the normalize-le test files cluster near 500 and the
500-line limit is a recurring trip hazard here, distinct from the
suppression-authorization concern in [[pyright-ignore-authorization-scope]]. The
merge-base for this branch is `03eb801` per `git merge-base main HEAD` (a caller
may supply the stale bootstrap SHA `2d86e83`; scope is identical either way).
