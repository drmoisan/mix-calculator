# Baseline — THIS-feature Protected Paths (clean pre-work tree proof)

Timestamp: 2026-05-30T07-20
Command: git status --porcelain  ;  git diff --name-only HEAD
EXIT_CODE: 0
Output Summary:
Working tree before Phase 1 implementation contains only the Feature D planning docs and the
new evidence directory. No source files are modified.

git status --porcelain:
- M docs/features/active/2026-05-30-gui-schema-builder-44/plan.2026-05-30T06-52.md
- M docs/features/active/2026-05-30-gui-schema-builder-44/spec.md
- M docs/features/active/2026-05-30-gui-schema-builder-44/user-story.md
- ?? docs/features/active/2026-05-30-gui-schema-builder-44/evidence/

git diff --name-only HEAD: only the three planning docs above (no src/** changes).

Protected-path globs that MUST remain unchanged by Feature D (THIS-feature regression check):
- src/normalize_le.py
- src/load_aop.py
- src/load_skulu.py
- src/mix_*.py
- src/etl_*.py
- src/calculator.py
- src/mix_pipeline*.py
- src/schema_*.py (Feature A/B/C: schema_registry, schema_matching, schema_loader,
  schema_formula, schema_model, schema_settings, schema_serialization)

Allowed additive edits (NOT protected): src/gui/app.py, src/gui/pipeline_service.py,
src/gui/protocols.py, src/gui/main_window.py — additive members only, existing GUI tests stay green.

Conclusion: clean baseline confirmed before Phase 1.
