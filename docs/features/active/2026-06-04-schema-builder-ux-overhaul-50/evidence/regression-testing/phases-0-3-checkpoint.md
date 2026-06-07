# Phases 0–3 Checkpoint

Timestamp: 2026-06-05T12-30
Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest -q
EXIT_CODE: 0
Output Summary:
- 842 passed, 1 warning (baseline was 818; +24 new model/serialization/migration tests).
- Black: clean (192 files unchanged).
- Ruff: All checks passed (after autofix of import ordering).
- Pyright: 0 errors, 0 warnings, 0 informations.

Phase boundary state:
- P0 (baseline + policy read + masking-scan helper): complete.
- P1 (model split into src/_schema_model_specs.py; expected_dtype; DTYPE_VOCAB +
  derive_expected_dtype; structured KeyPart/KeySpec; aggregate in DEDUP_MODES;
  SCHEMA_FORMAT_VERSION="2.0"): complete.
- P2 (serialization of expected_dtype, structured key parts, aggregate mode,
  version emission): complete.
- P3 (forward migration in schema_from_json: legacy key.columns -> column-ref
  parts; numeric -> expected_dtype float backfill; version bump on parse;
  alias persistence documented + round-trip test; idempotency test): complete.

Cap-sensitive file sizes after P1–P3:
- src/_schema_model_specs.py: 461
- src/schema_model.py: 283
- src/schema_serialization.py: 423
(all <= 500)

Breaking model change (KeySpec.columns -> KeySpec.parts, Decision 2) rippled to
all in-repo callers; production callers (schema_serialization, _schema_builder_state,
schema_builder_presenter) and all affected test files were updated to the structured
API. No compatibility shim retained (Decision 3).

Resume point: [P4-T1] (extend SchemaBuilderState with source-column pool,
consumed-column tracking, structured key-part state, masked preview slice).
