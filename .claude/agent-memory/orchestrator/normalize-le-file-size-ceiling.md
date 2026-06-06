---
name: normalize-le-file-size-ceiling
description: src/normalize_le.py sits at the 500-line repo ceiling with no headroom; plan extraction, not in-place additions, for future work there.
metadata:
  type: project
---

`src/normalize_le.py` was at 495 lines against the repository's hard 500-line
file-size limit (`.claude/rules/general-code-change.md`). It previously failed
that limit at 532 lines under issue #2 and was brought under by extracting the
shared ETL leaf modules. Under issue #52 (PR #53) it was reduced to 450 lines by
extracting LE column resolution into `src/_normalize_le_columns.py` to make room
for the KEY-mismatch `resolver` pass-through. Once PR #53 merges, the file has
~50 lines of headroom; until then main still shows 495.

**Why:** The repo enforces a 500-line cap on production/test/script files.
The normalize-le/etl module family has repeatedly approached it; under issue #7
the AOP loader had to be split into `src/load_aop.py` + `src/_load_aop_helpers.py`
for the same reason.

**How to apply:** When scoping future changes that touch `src/normalize_le.py`
(or the `etl_columns`/`etl_key`/`etl_totals` leaves), plan to extract logic into
a new helper module rather than adding lines in place, and have the planner
budget an extraction task. Confirm current line counts before planning since the
file may have changed.
