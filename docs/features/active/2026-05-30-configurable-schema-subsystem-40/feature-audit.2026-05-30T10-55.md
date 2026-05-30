# Feature Audit: configurable-schema-subsystem (Epic #40)

**Audit Date:** 2026-05-30
**Feature Folder:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40`
**Base Branch:** `main`
**Head Branch:** `epic/configurable-schema-subsystem-40`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `d14d4e9d13c65864b44b23f83f66e330755feffd`)
- **Head branch/commit:** `epic/configurable-schema-subsystem-40` (commit `04dba2aec0127a64211846f47e8c3c122637e216`)
- **Merge base:** `d14d4e9d13c65864b44b23f83f66e330755feffd`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: per-child `evidence/qa-gates/` and `evidence/regression-testing/` folders
  - Additional evidence: independent toolchain runs at head; `artifacts/python/lcov.info`
- **Feature folder used:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40`
- **Requirements source:** `user-story.md` + `spec.md` (Definition of Done) for each of the four child features #41-#44.
- **Work mode resolution note:** `issue.md` carries `- Work Mode: full-feature` (an earlier `- Work mode: full` line normalizes to `full-feature`). AC sources are the per-child `user-story.md` and `spec.md` files.
- **Scope note:** Epic #40's own `issue.md` AC list is an early draft and is not the authoritative source; the four child `user-story.md` files (37 AC total) are authoritative per the caller brief. The epic `issue.md` draft criteria remain unchecked by design.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-30-schema-model-and-registry-41/user-story.md` — Feature A (AC1-AC9)
- `docs/features/active/2026-05-30-schema-matching-and-discovery-42/user-story.md` — Feature B (AC1-AC8)
- `docs/features/active/2026-05-30-configurable-etl-core-43/user-story.md` — Feature C (AC1-AC11)
- `docs/features/active/2026-05-30-gui-schema-builder-44/user-story.md` — Feature D (AC1-AC9)
- Corresponding `spec.md` Definition-of-Done lists in each child folder (secondary).

### Acceptance criteria

#### From Feature A (#41) user-story.md
1. A `SchemaDefinition` (and nested frozen dataclasses) can represent column roles/aliases, key composition, dedup policy, derived columns, fill rules, drop columns, and sentinel-clean columns.
2. `SchemaDefinition` -> JSON -> `SchemaDefinition` round-trips losslessly and is Pyright-strict clean.
3. Malformed JSON, missing required fields, or unknown keys raise descriptive, specific errors.
4. `__post_init__` invariants reject schemas whose key/dedup/derived/fill references do not name declared columns, and require a discriminator column when dedup mode is collapse.
5. The shared registry directory resolves via a settings/path mechanism with an environment-variable override, independent of any `.db` path, unit-tested without disk.
6. `SchemaRegistry` can list, load, and save schemas through an injectable file-I/O boundary (tested without real files).
7. Bundled `default_aop.schema.json` and `default_le.schema.json` exist and structurally match the current canonical AOP/LE column sets, key, dedup, and derived definitions.
8. The existing test suite remains green; no existing loader, transform, CLI, or GUI behavior is modified.
9. New modules pass Black, Ruff, and Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; `quality-tiers.yml` classifies the new modules.

#### From Feature B (#42) user-story.md
1. `probe_columns` returns matched mapping, unmatched expected, and unmatched actual without raising; `resolve_columns` retains its raising contract unchanged.
2. `find_best_match` scores each candidate schema by required-column coverage (with alias support) and returns the highest-scoring schema and its score.
3. Ties break deterministically by newer schema version, then name; results are deterministic for a given input.
4. A registry-integrated entry point loads candidate schemas from the Feature A `SchemaRegistry` and applies matching.
5. Non-matching headers produce a typed `MismatchReport` naming each unmatched required column, its aliases, and up to N closest actual candidates with similarity scores, plus the unrecognized actual columns.
6. `MismatchReport.render()` returns a concise, professional, human-readable explanation string.
7. New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; a `hypothesis` property test covers scoring determinism.
8. The existing test suite remains green; no existing loader, transform, CLI, or GUI behavior is modified; `quality-tiers.yml` classifies the new modules.

#### From Feature C (#43) user-story.md
1. `SchemaLoader(default_le)` reproduces `normalize_le.normalize` output exactly on the existing LE fixtures.
2. `SchemaLoader(default_aop)` reproduces `load_aop`'s validated frame exactly on the existing AOP fixtures.
3. Dedup honors `additive` vs `select_from` per measure; `mode == none` preserves rows; dimensions taken from the first row.
4. The column builder constructs a missing column from other columns via a derived-column expression.
5. Non-additive (ratio/per-unit/%GS) measures are recomputed post-aggregation from summed dollars/volume with safe-division; zero/negative/null/NaN denominators yield 0.
6. The formula engine evaluates valid expressions including columns with spaces/special characters, and rejects syntactically invalid, disallowed-construct, or unknown-column expressions with descriptive `FormulaError`s.
7. `asteval` is added to `pyproject.toml`; a local `typings/asteval/__init__.pyi` stub makes Pyright strict pass with no suppression.
8. An integration test feeds `SchemaLoader` output through the existing pipeline transforms to a consistent result.
9. Formula-engine security is covered by fuzz/property tests (rejection of unsafe input; safe-division edge cases).
10. New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; modules classified in `quality-tiers.yml` (formula engine + loader core T1, with a property test per pure function).
11. Existing test suite remains green; no existing loader, transform, CLI, or GUI behavior is modified.

#### From Feature D (#44) user-story.md
1. On import, the system finds the best-matching schema via Feature B over the Feature A registry; a suitable match drives import via the Feature C `SchemaLoader`, with identical results for known AOP/LE files.
2. When no schema is a suitable match, the GUI shows the Feature B mismatch explanation and offers to open the manual column-matching dialog or the schema builder.
3. The manual column-matching dialog lets the user assign unmatched required columns point-and-click, shows fuzzy suggestions with similarity scores, supports ignoring optional columns, and can persist accepted assignments as schema alias additions via the registry.
4. The schema builder dialog creates/edits and persists a schema point-and-click across identity, columns, key, dedup policy, derived/formula columns, and a preview tab.
5. Runtime formula entry validates via the Feature C `FormulaEvaluator`; invalid/unsafe/unknown-column expressions are rejected inline with the descriptive `FormulaError`; valid expressions are accepted.
6. A "Schema Builder..." menu/action opens the builder outside the import flow.
7. The `SchemaBuilderPresenter` and `ColumnMatchingPresenter` are unit-tested without a `QApplication`; the dialogs and import-flow wiring are tested via `pytest-qt`.
8. New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage on presenters/service; `quality-tiers.yml` classifies new modules.
9. The existing test suite remains green; existing import for known files yields identical results; no existing CLI, transform, or loader module behavior is modified.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| A1 | SchemaDefinition models all schema aspects | PASS | `src/schema_model.py` (487 lines) frozen dataclasses; `tests/test_schema_model.py` | `poetry run pytest tests/test_schema_model.py` | Covers roles/aliases/key/dedup/derived/fill/drop/sentinel. |
| A2 | Lossless JSON round-trip, Pyright-strict | PASS | `src/schema_serialization.py`, `src/_schema_json_helpers.py`; `tests/test_schema_serialization.py` (incl. Hypothesis) | `poetry run pyright`; `poetry run pytest tests/test_schema_serialization.py` | Pyright strict 0 errors. |
| A3 | Descriptive errors on malformed/missing/unknown | PASS | `tests/test_schema_serialization.py` negative cases | `poetry run pytest tests/test_schema_serialization.py` | |
| A4 | `__post_init__` reference + discriminator invariants | PASS | `src/schema_model.py`; `tests/test_schema_model.py` invariant cases | `poetry run pytest tests/test_schema_model.py` | |
| A5 | Registry dir resolves via settings + env override, no disk | PASS | `src/schema_settings.py`; `tests/test_schema_settings.py` injected seams | `poetry run pytest tests/test_schema_settings.py` | |
| A6 | Registry list/load/save via injectable file boundary | PASS | `src/schema_registry.py`; `tests/test_schema_registry.py` in-memory store | `poetry run pytest tests/test_schema_registry.py` | |
| A7 | Bundled default AOP/LE schemas match canonical | PASS | `src/schemas/default_aop.schema.json`, `default_le.schema.json`; `tests/test_default_schemas.py` | `poetry run pytest tests/test_default_schemas.py` | |
| A8 | Existing suite green; no protected-file behavior change | PASS | `evidence/regression-testing/no-existing-files-modified.2026-05-30T07-25.md`; 717 pass | `poetry run pytest -q` | Protected-file diff scan empty. |
| A9 | Black/Ruff/Pyright; coverage; tier classification | PASS | Toolchain green; coverage >= 85/75; `quality-tiers.yml` T2 entries | `poetry run black --check .`; `ruff check .`; `pyright` | |
| B1 | `probe_columns` non-raising; resolver contract intact | PASS | `src/etl_column_probe.py` (100% cov); `tests/test_etl_column_probe.py` parity + resolver-unchanged | `poetry run pytest tests/test_etl_column_probe.py` | |
| B2 | `find_best_match` coverage scoring | PASS | `src/schema_matching.py`; `tests/test_schema_matching_best.py` | `poetry run pytest tests/test_schema_matching_best.py` | |
| B3 | Deterministic tie-break by version then name | PASS | `tests/test_schema_matching_best.py`; `tests/test_schema_matching_property.py` | `poetry run pytest tests/test_schema_matching_property.py` | Hypothesis determinism. |
| B4 | Registry-integrated match entry point | PASS | `tests/test_schema_matching_registry.py` (in-memory store) | `poetry run pytest tests/test_schema_matching_registry.py` | |
| B5 | Typed `MismatchReport` with candidates/scores | PASS | `src/schema_matching.py`; `tests/test_schema_matching_report.py` | `poetry run pytest tests/test_schema_matching_report.py` | |
| B6 | `MismatchReport.render()` human-readable | PASS | `tests/test_schema_matching_report.py` render assertions | `poetry run pytest tests/test_schema_matching_report.py` | |
| B7 | Toolchain + coverage + Hypothesis property | PASS | `evidence/qa-gates/newcode-coverage.2026-05-30T07-59.md`; `schema_matching.py` 98.91% line | `poetry run pytest --cov` | |
| B8 | Suite green; protected files unchanged; tiers classified | PASS | `evidence/regression-testing/protected-files-diff.2026-05-30T07-59.md` | `poetry run pytest -q` | |
| C1 | `SchemaLoader(default_le)` == `normalize` | PASS | `tests/test_schema_loader_parity_le.py` (`assert_frame_equal`) | `poetry run pytest tests/test_schema_loader_parity_le.py` | |
| C2 | `SchemaLoader(default_aop)` == `load_aop` | PASS | `tests/test_schema_loader_parity_aop.py` | `poetry run pytest tests/test_schema_loader_parity_aop.py` | |
| C3 | Dedup additive/select_from/none; first-row dims | PASS | `src/_schema_loader_helpers.py` partition logic; `tests/test_schema_loader_core.py` | `poetry run pytest tests/test_schema_loader_core.py` | |
| C4 | Column builder constructs missing column | PASS | `tests/test_schema_loader_derived.py` | `poetry run pytest tests/test_schema_loader_derived.py` | |
| C5 | Ratio recompute via safe-division; 0 on bad denom | PASS | `src/_schema_formula_helpers.py::safe_div`; `tests/test_schema_loader_derived.py` + property tests | `poetry run pytest tests/test_schema_formula.py` | None/NaN/<=0 -> 0.0. |
| C6 | Formula engine valid eval + special chars + rejection | PASS | `src/schema_formula.py` (100% cov); `tests/test_schema_formula.py` (8 properties) | `poetry run pytest tests/test_schema_formula.py` | `SKU #`, `Off Invoice $` via `col`/alias. |
| C7 | `asteval` added; local stub; no suppression | PASS | `pyproject.toml` `asteval = "^1.0.8"`; `typings/asteval/__init__.pyi`; Pyright strict 0 errors | `poetry run pyright`; `grep -rn 'type: ignore' src typings` | No suppression at the boundary. |
| C8 | Integration through transforms | PASS | `tests/test_schema_loader_integration.py` | `poetry run pytest tests/test_schema_loader_integration.py` | |
| C9 | Security fuzz/property tests | PASS | `tests/test_schema_formula.py` unsafe-expression corpus + safe-div properties | `poetry run pytest tests/test_schema_formula.py` | |
| C10 | Toolchain; coverage; T1 classification + property/fn | PASS | `quality-tiers.yml` T1 for `schema_formula`/`schema_loader`; 8 `@given` | `poetry run pytest --cov` | Mutation (T1 >=75%) deferred to pre-merge/nightly per quality-tiers.md. |
| C11 | Suite green; protected behavior unchanged | PASS | `evidence/regression-testing/protected-files-diff.2026-05-30T09-25.md`; 717 pass | `poetry run pytest -q` | |
| D1 | Import discovery -> SchemaLoader; identical known-file result | PASS | `tests/gui/integration/test_behavioral_schema_import.py` AC1 parity; `src/gui/_schema_wiring.py` | `poetry run pytest tests/gui/integration/test_behavioral_schema_import.py` | |
| D2 | No-match shows explanation + offers dialog/builder | PASS | `tests/gui/integration/test_behavioral_schema_import.py` AC2 no-match path | `poetry run pytest tests/gui/integration` | |
| D3 | Manual column-matching dialog with fuzzy/ignore/persist | PASS | `src/gui/widgets/column_matching_dialog.py`, `presenters/column_matching_presenter.py`; `tests/gui/test_column_matching_*` | `poetry run pytest tests/gui/test_column_matching_presenter.py tests/gui/test_column_matching_dialog.py` | |
| D4 | Schema builder create/edit/persist across tabs | PASS | `src/gui/widgets/schema_builder_dialog.py`, `_schema_builder_tabs.py`, `presenters/schema_builder_presenter.py`; `tests/gui/test_schema_builder_*` | `poetry run pytest tests/gui/test_schema_builder_presenter.py tests/gui/test_schema_builder_dialog.py` | |
| D5 | Runtime formula entry validates via FormulaEvaluator | PASS | `presenters/schema_builder_presenter.py` + `_schema_builder_state.py`; presenter tests cover invalid/unsafe/unknown rejection | `poetry run pytest tests/gui/test_schema_builder_presenter.py` | |
| D6 | "Schema Builder..." action outside import flow | PASS | `src/gui/main_window.py` Tools menu + `schema_builder_requested`; `src/gui/app.py` `wire_schema_builder`; `tests/gui/test_app_wiring_schema.py` | `poetry run pytest tests/gui/test_app_wiring_schema.py` | |
| D7 | Presenters tested without QApplication; dialogs via pytest-qt | PASS | Presenter tests import no `QApplication`; dialog tests use pytest-qt offscreen | `poetry run pytest tests/gui` | |
| D8 | Toolchain; coverage on presenters/service; tiers | PASS | `evidence/qa-gates/final-pyright.2026-05-30T08-40.md`; presenters/service 100% cov | `poetry run pytest --cov` | |
| D9 | Suite green; identical known-file import; protected unchanged | PASS | `evidence/regression-testing/protected-files.2026-05-30T08-40.md`; 717 pass | `poetry run pytest -q` | |

---

## Summary

**Overall Feature Readiness:** PASS

All 37 acceptance criteria across the four child features evaluate to PASS on inspected evidence. The independent toolchain run at head confirms Black/Ruff/Pyright-strict/Pytest all green with 717 passing tests and coverage above the uniform 85%/75% gate. The two procedural policy findings recorded in the policy audit (unauthorized E402 suppressions; one over-ceiling test file) do not invalidate any acceptance criterion — they are code-hygiene items, not behavior gaps — but they do hold the overall policy verdict at PARTIALLY COMPLIANT and warrant a minor remediation pass before merge.

**Criteria summary:**
- **PASS:** 37 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None at the acceptance-criteria level. (Procedural policy items E402 authorization and `fake_views.py` size are tracked in the policy audit and remediation inputs.)

**Recommended follow-up verification steps:**

1. After E402 remediation, re-run `poetry run ruff check .` to confirm no new lint findings and that any added pre-authorized pattern is honored.
2. After splitting `tests/gui/fakes/fake_views.py`, re-run `poetry run pytest -q` to confirm the GUI suite stays green.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, all 37 criteria evaluated PASS and were already checked off `[x]` in the four child `user-story.md` source files by the executors (confirmed in `artifacts/pr_context.summary.txt`, which lists every AC as `- [x]`). No checkbox state change was required by this reviewer; the existing checkmarks are consistent with the PASS evaluations. The epic `issue.md` early-draft AC list is intentionally left unchecked because it is not the authoritative source for `full-feature` mode.

### AC Status Summary

- Source: four child `user-story.md` files (#41 AC1-9, #42 AC1-8, #43 AC1-11, #44 AC1-9)
- Total AC items: 37
- Checked off (delivered): 37
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-30-schema-model-and-registry-41/user-story.md` | 9 | 9 | 0 | Checkbox-backed; already checked by executor |
| `docs/features/active/2026-05-30-schema-matching-and-discovery-42/user-story.md` | 8 | 8 | 0 | Checkbox-backed; already checked by executor |
| `docs/features/active/2026-05-30-configurable-etl-core-43/user-story.md` | 11 | 11 | 0 | Checkbox-backed; already checked by executor |
| `docs/features/active/2026-05-30-gui-schema-builder-44/user-story.md` | 9 | 9 | 0 | Checkbox-backed; already checked by executor |
