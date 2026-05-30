# Baseline — Protected-Files HEAD State (Issue #43)

Timestamp: 2026-05-30T07-45
Command: git status --porcelain ; git rev-parse HEAD
EXIT_CODE: 0

HEAD SHA: 18bd5fb310010d53e419fcd134fc93fa93373e74
Branch: epic/configurable-schema-subsystem-40

Output Summary:
At feature start, the working tree contains only the expected orchestration/feature-doc changes and the pre-approved dependency entries:
- D  docs/features/active/2026-05-30-configurable-etl-core-43/plan.2026-05-30T06-52.md (superseded plan)
- M  docs/features/active/2026-05-30-configurable-etl-core-43/spec.md
- M  docs/features/active/2026-05-30-configurable-etl-core-43/user-story.md
- M  poetry.lock (asteval ^1.0.8, user-approved 2026-05-30)
- M  pyproject.toml (asteval ^1.0.8, user-approved 2026-05-30)
- ?? docs/features/active/2026-05-30-configurable-etl-core-43/plan.2026-05-30T07-30.md (active plan)
- ?? docs/features/active/2026-05-30-configurable-etl-core-43/evidence/ (this evidence tree)

No protected source path is modified. The protected paths are:
src/normalize_le.py, src/load_aop.py, src/_load_aop_helpers.py, src/etl_columns.py, src/etl_key.py, src/etl_totals.py, src/etl_column_probe.py, src/schema_model.py, src/schema_serialization.py, src/_schema_json_helpers.py, src/schema_settings.py, src/schema_registry.py, src/schema_matching.py, src/_schema_matching_helpers.py, the bundled default schema JSON files, the mix transforms, src/gui/**, the CLI loaders, pipeline_service.

Note for the final regression check (per plan P0-T6): on the shared epic branch, `git diff --name-only main` will list committed Feature A/B ancestry, which is NOT a violation. The correct THIS-feature check is that `git diff --name-only HEAD` and `git status` show no modifications to any protected path.
