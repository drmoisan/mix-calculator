---
name: gui-activation-seam-guards
description: GUI activation/discovery seams crash on empty/placeholder selection; integration tests must drive the no-file/no-sheet path, not just the happy path
metadata:
  type: feedback
---

GUI signal-wired discovery seams must guard empty/blank inputs before doing I/O, and integration tests must exercise the empty/placeholder activation path — not only the happy path with valid state pre-set.

**Why:** In #50 the `on_schema_discovery` seam wired to `tab_combo.currentTextChanged` crashed at runtime (`KeyError: 'Worksheet  does not exist.'`) because activation fires on combo population / before a worksheet is selected, passing a blank sheet into `read_sheet_preview`. Every unit and integration test passed because they pre-set a valid file+sheet, so none drove the real no-selection activation path. This shipped green through full feature-review and CI, then crashed on the user's first launch. A separate latent defect (a column named `col` shadowing the `col()` formula helper) was only caught by a Hypothesis property test on a fresh seed.

**How to apply:** For any GUI signal wiring (currentTextChanged, activation, selection), require an integration test that drives the real signal with (a) nothing selected and (b) a partially-selected/placeholder state, asserting no exception propagates and no downstream I/O runs with blank args. Treat reader/error-contract mismatches (e.g. openpyxl raising KeyError while the caller only catches ValueError) as guard gaps. Pair with [[audit-verify-production-call-site]]: a wired-and-tested seam can still crash if tests only cover valid state.
