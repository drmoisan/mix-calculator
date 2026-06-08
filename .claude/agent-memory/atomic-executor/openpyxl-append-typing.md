---
name: openpyxl-append-typing
description: openpyxl Worksheet.append rejects Sequence under strict Pyright; pass list/tuple, and use Sequence covariance only at the function boundary
metadata:
  type: feedback
---

When a test helper builds in-memory workbooks and accepts rows of mixed cell
types (e.g. `list[list[object]]`), strict Pyright rejects passing concrete
literals like `list[list[str | int]]` to a `list[list[object]]` parameter
because `list` is invariant. Widen the parameter to
`Sequence[Sequence[object]]` (covariant) so callers type-check.

But `openpyxl`'s `Worksheet.append` is typed to accept
`list | tuple | range | generator | dict`, NOT an arbitrary `Sequence`. So after
widening the parameter, materialize each row with `list(row)` at the `append`
call site.

**Why:** Both errors appeared in #55's `tests/test_header_detection.py`. Fixing
only the parameter moved the error into the append loop; both fixes are needed.

**How to apply:** For any openpyxl-backed test fixture builder under strict
Pyright: parameter = `Sequence[Sequence[object]]`, append = `worksheet.append(list(row))`.
This is a typing pattern, not a suppression — no `# type: ignore` is needed or allowed.
