---
name: pytest-cov-module-vs-path-arg
description: In this repo, --cov must use dotted module form (src.gui.runners), not path form (src/gui/runners), or coverage reports "module not imported / no data"
metadata:
  type: feedback
---

When re-measuring per-module coverage to verify a feature-review claim, pass `--cov` the dotted module path, not the filesystem path.

- Works: `--cov=src.gui.runners --cov=src.gui._shutdown_wiring`
- Fails silently: `--cov=src/gui/runners` → emits `CoverageWarning: Module src/gui/runners was never imported (module-not-imported)` and `No data was collected`, producing an empty report even though tests pass.

**Why:** the repo's pyproject/coverage config resolves source by import name; the path-style argument does not match the imported module name, so coverage attaches to nothing.

**How to apply:** during R-audit coverage re-verification (e.g. issue #48 cycle 2), use the dotted form. If a targeted `--cov` run reports 0 data while tests pass, suspect the path-vs-module form before concluding the tests do not exercise the module. Confirm full-suite figures with `-k` selection over `tests/` plus dotted `--cov` (gave runners.py 100%/100% on #48).
