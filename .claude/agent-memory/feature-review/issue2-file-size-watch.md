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

**Still under limit under issue #7 (2026-05-26T14-40 audit, head `5329c9f`):**
The load-aop feature renamed the LE leaf modules to `etl_*` and touched
`tests/test_normalize_le.py` (+13 net lines, now 446) and `src/normalize_le.py`
(now 495). Every changed src/test file remains < 500; largest are
`normalize_le.py` at 495 and `test_normalize_le.py` at 446. Verdict PASS, zero
blocking findings.

**How to apply:** When re-auditing the normalize-le / etl module family after any
test addition (issue #2 or any sibling ETL like issue #7), always run
`wc -l tests/*.py src/*.py` — these files cluster near 500 and the 500-line limit
is a recurring trip hazard here, distinct from the suppression-authorization
concern in [[pyright-ignore-authorization-scope]]. `src/normalize_le.py` sits at
495 lines and has essentially no headroom; any further growth needs extraction.
The issue #7 merge-base is `c586ac07` (resolved base `main`).
