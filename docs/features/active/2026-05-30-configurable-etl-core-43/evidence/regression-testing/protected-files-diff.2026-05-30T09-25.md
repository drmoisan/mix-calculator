# Protected-Files Regression Check (Issue #43)

Timestamp: 2026-05-30T09-25
Command: git diff --name-only HEAD ; git status --porcelain
EXIT_CODE: 0

## git diff --name-only HEAD
- docs/features/active/2026-05-30-configurable-etl-core-43/plan.2026-05-30T06-52.md (superseded plan, deleted)
- docs/features/active/2026-05-30-configurable-etl-core-43/spec.md (AC check-offs)
- docs/features/active/2026-05-30-configurable-etl-core-43/user-story.md (orchestration)
- poetry.lock (asteval ^1.0.8, user-approved 2026-05-30)
- pyproject.toml (asteval ^1.0.8, user-approved 2026-05-30)
- quality-tiers.yml (additive tier entries for the four new modules)

## New (untracked) files added by this feature
- src/schema_formula.py, src/_schema_formula_helpers.py
- src/schema_loader.py, src/_schema_loader_helpers.py
- typings/asteval/__init__.pyi
- tests/test_schema_formula.py, tests/test_schema_loader_core.py,
  tests/test_schema_loader_derived.py, tests/test_schema_loader_parity_le.py,
  tests/test_schema_loader_parity_aop.py, tests/test_schema_loader_integration.py
- docs/features/active/2026-05-30-configurable-etl-core-43/evidence/ (this tree)
- docs/features/active/2026-05-30-configurable-etl-core-43/plan.2026-05-30T07-30.md (active plan)

## Output Summary
No protected path appears as modified. The protected paths are:
src/normalize_le.py, src/load_aop.py, src/_load_aop_helpers.py, src/etl_columns.py,
src/etl_key.py, src/etl_totals.py, src/etl_column_probe.py, src/schema_model.py,
src/schema_serialization.py, src/_schema_json_helpers.py, src/schema_settings.py,
src/schema_registry.py, src/schema_matching.py, src/_schema_matching_helpers.py,
the bundled default schema JSON files, the mix transforms, src/gui/**, the CLI
loaders, and pipeline_service. None of these is present in `git diff --name-only HEAD`
or `git status --porcelain`.

The only changed paths are the new feature files (the four src modules, the asteval
stub, the six new tests), quality-tiers.yml (additive entries only — no existing
entry altered), and the feature-doc / pre-approved-dependency / orchestration files.

Per the P0-T6 note: `git diff --name-only main` would also list committed
Feature A/B ancestry on the shared epic branch, which is NOT a violation. The
authoritative THIS-feature check is the clean `git diff --name-only HEAD` /
`git status` above, which shows no modification to any protected path.
