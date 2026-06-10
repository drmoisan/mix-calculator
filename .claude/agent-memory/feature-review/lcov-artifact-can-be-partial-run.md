---
name: lcov-artifact-can-be-partial-run
description: artifacts/python/lcov.info may reflect a partial/targeted pytest run, not the full suite; re-run full suite before trusting per-file coverage in an R-audit
metadata:
  type: feedback
---

`artifacts/python/lcov.info` can be left over from a partial or targeted pytest
run, so per-file coverage extracted from it understates true full-suite coverage.

**Why:** On the issue #62 cycle-1 re-audit (2026-06-10), the stored `lcov.info`
(timestamped 09:24) reported `src/gui/_schema_discovery_wiring.py` at 67.4% line
and `source_selection_presenter.py` at 47.9% line. A fresh full-suite run
(`QT_QPA_PLATFORM=offscreen poetry run pytest tests/ --cov=... --cov-branch`)
rewrote the artifact and showed both at 100% line — the executor's reported
figures were correct; the stored artifact was a partial run.

**How to apply:** When verifying coverage from `artifacts/python/lcov.info` in an
R-audit, do not trust a surprisingly-low per-file number at face value. Re-run the
full suite with the dotted `--cov=` module form (see
[[pytest-cov-module-vs-path-arg]]) to refresh the artifact, then extract per-file
LF/LH/BRF/BRH. The full run also re-confirms a single-pass green suite. Related:
[[pr-context-summary-can-be-stale]] (independent verification over stored
artifacts).
