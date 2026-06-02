# Remediation Summary — Surface bundled default schemas (Issue #48 / PR #49)

Timestamp: 2026-06-01T23-31

## Toolchain (final, single clean pass)

| Stage | Command | Result |
|---|---|---|
| Format | poetry run black --check . | EXIT 0; 187 files unchanged |
| Lint | poetry run ruff check . | EXIT 0; all checks passed |
| Type | poetry run pyright | EXIT 0; 0 errors / 0 warnings |
| Test | pytest --cov --cov-branch | EXIT 0; 811 passed; line 99.47%, branch 96.61% |

## Remediation Acceptance Criteria

| R-AC | Status | Evidence |
|---|---|---|
| R-AC-1 (bundled defaults selectable on empty profile) | PASS | tests/gui/test_schema_service.py::test_service_lists_and_loads_bundled_defaults_when_user_dir_empty (P4-T1); pytest-final.2026-06-01T23-31.md |
| R-AC-2 (user override wins, no duplicate) | PASS | tests/test_schema_registry.py::test_list_schemas_user_override_appears_once_and_resolves_to_user (P1-T4); pytest-final.2026-06-01T23-31.md |
| R-AC-3 (dropdown populated at startup; production caller of set_schema_list) | PASS | tests/gui/test_app_wiring_schema_list.py (P3-T4/P3-T5); src/gui/_schema_list_wiring.py + src/gui/app.py call site; app-py-size-postchange.2026-06-01T23-31.md |
| R-AC-4 (matching sees bundled defaults; proceed) | PASS | tests/test_schema_matching_registry.py::test_find_best_match_and_discover_see_bundled_defaults (P2-T1); pytest-final.2026-06-01T23-31.md |
| R-AC-5 (load bundled default by name with no user file) | PASS | tests/gui/test_schema_service.py::test_service_lists_and_loads_bundled_defaults_when_user_dir_empty (P4-T1); pytest-final.2026-06-01T23-31.md |
| R-AC-6 (additive; known-file loaders and user registry unchanged; AC-1..AC-15 still PASS) | PASS | tests/test_schema_registry.py::test_additivity_bundled_default_and_user_round_trip_unchanged (P4-T2); full suite 811 passed (P5-T4) |

## Existing acceptance criteria

AC-1..AC-15 remain checked `[x]` in spec.md; no existing test regressed (801 -> 811
passed, 0 failures).

## File-size compliance (500-line cap)

| File | Lines | Status |
|---|---|---|
| src/gui/app.py | 500 | at cap, compliant |
| src/gui/_schema_list_wiring.py (new) | 62 | compliant |
| src/schema_registry.py | 357 | compliant |

## Source-change scope

Production: src/schema_registry.py (union-aware list_schemas/load + _list_bundled_names
helper); src/gui/_schema_list_wiring.py (new dropdown-population wiring);
src/gui/app.py (one import + one call site). No change to known-file loaders or
user-registry persistence semantics; no bundled schema JSON content changed; no new
suppressions; no new dependencies.
