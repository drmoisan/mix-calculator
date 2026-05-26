---
name: hypothesis-float-magnitude-bounds
description: Hypothesis float strategies in this repo's tests must bound magnitude or the abs-tolerance tie-out assertions become unsatisfiable
metadata:
  type: project
---

Hypothesis property tests that feed `st.floats(width=32)` into row-wise pandas
sums and then assert closeness with an absolute tolerance MUST bound magnitude
(the established pattern is `min_value=-1e6, max_value=1e6`). Unbounded float32
operands reach ~3.4e38, where catastrophic cancellation makes any absolute
tolerance unsatisfiable.

**Why:** During issue #7 (load-aop), the pre-existing
`tests/test_normalize_le.py::test_compute_ytg_property` had an unbounded
`st.floats(..., width=32)` strategy with `tol=1e-9`. It passed at baseline only
because Hypothesis had not yet discovered the edge case; it failed mid-run once
Hypothesis persisted a falsifying example like `[..., 3.4e38, 1.0, -3.4e38]` to
its `.hypothesis/` database. Confirmed independent of the change via `git stash`.
The sibling `test_normalize_property_row_count_and_sums` in the same file already
used the bounded pattern.

**How to apply:** When adding or reviewing a Hypothesis float strategy that flows
into a sum + closeness assertion, copy the bounded `min_value/max_value` pattern
from the existing sibling property tests rather than leaving floats unbounded.
A green baseline does not prove such a test is sound — Hypothesis may not have
found the falsifying example yet. See [[pandas-pyright-stubs]] for the related
pandas-strict-typing note.
