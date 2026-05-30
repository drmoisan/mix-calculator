# Feature Audit: configurable-schema-subsystem (Epic #40) — Cycle-1 Re-Audit

**Audit Date:** 2026-05-30
**Feature Folder:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40`
**Base Branch:** `main`
**Head Branch:** `epic/configurable-schema-subsystem-40` @ `0ddfc53`
**Work Mode:** `full-feature`
**Audit Type:** Post-remediation acceptance verification (cycle 1)

---

## Scope and Baseline

- **Base branch:** `main` (commit `d14d4e9d13c65864b44b23f83f66e330755feffd`)
- **Head branch/commit:** `epic/configurable-schema-subsystem-40` (commit `0ddfc53f428f5aeaf1818ee4a0454a7af53c2e0e`)
- **Merge base:** `d14d4e9d13c65864b44b23f83f66e330755feffd`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: per-child `evidence/qa-gates/**` and `evidence/regression-testing/**`; epic `evidence/qa-gates/*.2026-05-30T11-10.md`
  - Additional evidence: re-run toolchain output (Black/Ruff/Pyright/Pytest) and regenerated `artifacts/python/lcov.info`
- **Feature folder used:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40` (epic)
- **Requirements source:** `spec.md` and `user-story.md` in each of the four child folders (#41 schema-model-and-registry, #42 schema-matching-and-discovery, #43 configurable-etl-core, #44 gui-schema-builder).
- **Work mode resolution note:** The epic `issue.md` carries `- Work Mode: full-feature` (an earlier `- Work mode: full` line normalizes to the same). Per the work-mode contract, AC sources are the child `spec.md` and `user-story.md` files. The epic `issue.md` Acceptance Criteria are tracked as prose rollups (not the authoritative checkbox source).
- **Scope note:** Full feature-vs-base audit against the entire branch diff `main...HEAD`. No scope narrowing applied. The 37 AC checkboxes across the four child features are the authoritative tracked criteria.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-30-schema-model-and-registry-41/spec.md` + `user-story.md` — child #41 (9 AC)
- `docs/features/active/2026-05-30-schema-matching-and-discovery-42/spec.md` + `user-story.md` — child #42 (8 AC)
- `docs/features/active/2026-05-30-configurable-etl-core-43/spec.md` + `user-story.md` — child #43 (11 AC)
- `docs/features/active/2026-05-30-gui-schema-builder-44/spec.md` + `user-story.md` — child #44 (9 AC)

### Acceptance criteria

#### From child #41 (schema-model-and-registry)
1. AC1: `SchemaDefinition` represents column roles/aliases, key composition, dedup policy, derived columns, fill rules, drop columns, and sentinel-clean columns.
2. AC2: `SchemaDefinition` -> JSON -> `SchemaDefinition` round-trips losslessly and is Pyright-strict clean.
3. AC3: Malformed JSON, missing required fields, or unknown keys raise descriptive errors.
4. AC4: `__post_init__` invariants reject undeclared key/dedup/derived/fill references and require a discriminator when dedup mode is collapse.
5. AC5: The shared registry directory resolves via a settings/path mechanism with an env override, independent of any `.db`; unit-tested without disk.
6. AC6: `SchemaRegistry` can list, load, and save through an injectable file-I/O boundary (tested without real files).
7. AC7: Bundled `default_aop.schema.json` / `default_le.schema.json` exist and structurally match the canonical AOP/LE sets.
8. AC8: Existing suite green; no existing loader/transform/CLI/GUI behavior modified.
9. AC9: New modules pass Black/Ruff/Pyright strict; changed code >= 85% line / >= 75% branch; classified in `quality-tiers.yml`.

#### From child #42 (schema-matching-and-discovery)
10. AC1: `probe_columns` returns matched/unmatched-expected/unmatched-actual without raising; `resolve_columns` keeps its raising contract.
11. AC2: `find_best_match` scores by required-column coverage (alias support) and returns the highest-scoring schema and score.
12. AC3: Ties break deterministically by newer version then name; deterministic results.
13. AC4: A registry-integrated entry point loads candidate schemas from the Feature A registry and applies matching.
14. AC5: Non-matching headers produce a typed `MismatchReport` with unmatched required columns, aliases, closest candidates, and unrecognized actual columns.
15. AC6: `MismatchReport.render()` returns a concise human-readable explanation.
16. AC7: New modules pass Black/Ruff/Pyright strict; >= 85% line / >= 75% branch; Hypothesis property test for scoring determinism.
17. AC8: Existing suite green; no existing behavior modified; new modules classified.

#### From child #43 (configurable-etl-core)
18. AC1: `SchemaLoader(default_le)` reproduces `normalize_le.normalize` exactly (columns, order, values, PPG quirk, derived YTG, dropped YTD/YTG).
19. AC2: `SchemaLoader(default_aop)` reproduces `load_aop`'s validated frame exactly.
20. AC3: Dedup honors additive vs select_from per measure; `mode == none` preserves rows; dimensions from first row.
21. AC4: The column builder constructs a missing column from other columns via a derived expression.
22. AC5: Non-additive measures recomputed post-aggregation from summed dollars/volume with safe-division; zero/negative/null/NaN denominators yield 0.
23. AC6: The formula engine evaluates valid expressions including columns with spaces/special chars, and rejects invalid/disallowed/unknown-column expressions with descriptive `FormulaError`s.
24. AC7: `asteval` is added to `pyproject.toml`; a local `typings/asteval/__init__.pyi` stub makes Pyright strict pass with no suppression.
25. AC8: An integration test feeds `SchemaLoader` output through the existing transforms to a consistent result.
26. AC9: Formula-engine security covered by fuzz/property tests (unsafe-input rejection; safe-division edge cases).
27. AC10: New modules pass Black/Ruff/Pyright strict; changed code >= 85% line / >= 75% branch; formula engine + loader core T1 with a property test per pure function.
28. AC11: Existing suite green; no existing loader/transform/CLI/GUI behavior modified.

#### From child #44 (gui-schema-builder)
29. AC1: On import, the system finds the best-matching schema (Feature B over Feature A registry); a suitable match drives import via `SchemaLoader` with identical results for known AOP/LE files.
30. AC2: When no schema matches, the GUI shows the mismatch explanation and offers the manual column-matching dialog or the schema builder.
31. AC3: The manual column-matching dialog assigns unmatched required columns point-and-click, shows fuzzy suggestions/scores, supports ignoring optional columns, and persists accepted assignments as alias additions.
32. AC4: The schema builder dialog creates/edits/persists a schema across identity, columns, key, dedup policy, derived/formula columns, and a preview tab.
33. AC5: Runtime formula entry validates via `FormulaEvaluator`; invalid/unsafe/unknown-column rejected inline with the descriptive message; valid accepted.
34. AC6: A "Schema Builder..." menu/action opens the builder outside the import flow.
35. AC7: `SchemaBuilderPresenter` and `ColumnMatchingPresenter` are unit-tested without a `QApplication`; dialogs and import-flow wiring tested via `pytest-qt`.
36. AC8: New modules pass Black/Ruff/Pyright strict; presenters/service >= 85% line / >= 75% branch; new modules classified.
37. AC9: Existing suite green; known-file import unchanged; no existing CLI/transform/loader behavior modified.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | #41 AC1 schema model expressiveness | PASS | `src/schema_model.py` frozen dataclasses; `test_schema_model.py` | `poetry run pytest tests/test_schema_model.py` | Unchanged since cycle 0 |
| 2 | #41 AC2 lossless JSON round-trip, strict | PASS | `src/schema_serialization.py`; `test_schema_serialization.py` (incl. Hypothesis) | `poetry run pyright` | 0 strict errors |
| 3 | #41 AC3 descriptive JSON errors | PASS | serialization adapter; negative tests | `poetry run pytest` | |
| 4 | #41 AC4 `__post_init__` invariants | PASS | `schema_model.py::__post_init__`; invariant tests | `poetry run pytest` | |
| 5 | #41 AC5 registry dir via settings/env, no disk | PASS | `src/schema_settings.py`; `test_schema_settings.py` | `poetry run pytest` | injected seams |
| 6 | #41 AC6 registry list/load/save injectable | PASS | `src/schema_registry.py`; `test_schema_registry.py` | `poetry run pytest` | in-memory store |
| 7 | #41 AC7 bundled default schemas parity | PASS | `src/schemas/default_aop.schema.json`, `default_le.schema.json`; `test_default_schemas.py` | `poetry run pytest` | |
| 8 | #41 AC8 no existing behavior modified | PASS | diff scan: no protected loader/transform/CLI/GUI file modified | `git diff --name-only d14d4e9..0ddfc53` | additive |
| 9 | #41 AC9 toolchain + coverage + tiers | PASS | Black/Ruff/Pyright green; model 100% line; classified | `poetry run pytest --cov --cov-branch` | |
| 10 | #42 AC1 non-raising probe; resolver unchanged | PASS | `src/etl_column_probe.py`; `test_etl_column_probe.py` parity + regression | `poetry run pytest tests/test_etl_column_probe.py` | |
| 11 | #42 AC2 best-match coverage scoring | PASS | `src/schema_matching.py`; `test_schema_matching_best.py` | `poetry run pytest` | |
| 12 | #42 AC3 deterministic tie-break | PASS | matching tie-break tests | `poetry run pytest` | version then name |
| 13 | #42 AC4 registry-integrated matching | PASS | `test_schema_matching_registry.py` (in-memory store) | `poetry run pytest` | |
| 14 | #42 AC5 typed `MismatchReport` | PASS | `schema_matching.py`; `test_schema_matching_report.py` | `poetry run pytest` | |
| 15 | #42 AC6 `MismatchReport.render()` | PASS | render test | `poetry run pytest` | |
| 16 | #42 AC7 toolchain + coverage + property | PASS | matching 97% line; `test_schema_matching_property.py` (Hypothesis) | `poetry run pytest --cov --cov-branch` | |
| 17 | #42 AC8 no existing behavior modified; classified | PASS | diff scan; `quality-tiers.yml` entries | `git diff --name-only` | |
| 18 | #43 AC1 LE parity exact | PASS | `test_schema_loader_parity_le.py` (`assert_frame_equal` vs `normalize`) | `poetry run pytest tests/test_schema_loader_parity_le.py` | |
| 19 | #43 AC2 AOP parity exact | PASS | `test_schema_loader_parity_aop.py` (vs `load_aop`) | `poetry run pytest tests/test_schema_loader_parity_aop.py` | |
| 20 | #43 AC3 dedup additive/select_from/none | PASS | `_schema_loader_helpers.py`; `test_schema_loader_core.py` | `poetry run pytest` | |
| 21 | #43 AC4 column builder | PASS | `test_schema_loader_derived.py` | `poetry run pytest` | |
| 22 | #43 AC5 ratio recompute safe-division | PASS | `safe_div`; `test_schema_formula.py` + property tests | `poetry run pytest` | zero/neg/null/NaN -> 0 |
| 23 | #43 AC6 formula eval + rejection | PASS | `src/schema_formula.py`; `test_schema_formula.py` (`SKU #`, `Off Invoice $`) | `poetry run pytest tests/test_schema_formula.py` | |
| 24 | #43 AC7 asteval added + typed stub, no suppression | PASS | `pyproject.toml` `asteval = "^1.0.8"`; `typings/asteval/__init__.pyi` fully annotated | `poetry run pyright` | 0 strict errors, no `# type: ignore` |
| 25 | #43 AC8 integration through transforms | PASS | `test_schema_loader_integration.py` | `poetry run pytest tests/test_schema_loader_integration.py` | |
| 26 | #43 AC9 fuzz/property security tests | PASS | property/fuzz rejection corpus + safe-division properties | `poetry run pytest` | |
| 27 | #43 AC10 toolchain + coverage + T1 property | PASS | formula 100%, loader 100% line; T1 in `quality-tiers.yml` | `poetry run pytest --cov --cov-branch` | |
| 28 | #43 AC11 no existing behavior modified | PASS | diff scan: no protected loader/transform/CLI/GUI modified | `git diff --name-only` | |
| 29 | #44 AC1 import discovery drives `SchemaLoader`; known-file parity | PASS | `tests/gui/integration/test_behavioral_schema_import.py` | `poetry run pytest` (offscreen) | |
| 30 | #44 AC2 no-match shows explanation + offers dialogs | PASS | import-flow wiring + integration test | `poetry run pytest` | |
| 31 | #44 AC3 manual column-matching dialog | PASS | `src/gui/widgets/column_matching_dialog.py` (100% line); presenter tests | `poetry run pytest` | |
| 32 | #44 AC4 schema builder dialog (incl. preview tab) | PASS | `schema_builder_dialog.py` (96%), `_schema_builder_tabs.py` (100%) | `poetry run pytest` | |
| 33 | #44 AC5 runtime formula entry via `FormulaEvaluator` | PASS | presenter formula-validation tests (invalid/unsafe/unknown rejected inline) | `poetry run pytest` | |
| 34 | #44 AC6 "Schema Builder..." action outside import flow | PASS | `_schema_wiring.py` action wiring; composition test | `poetry run pytest` | |
| 35 | #44 AC7 presenters unit-tested w/o QApplication; dialogs via pytest-qt | PASS | presenter unit tests (no QApplication); dialog/wiring pytest-qt offscreen | `poetry run pytest` | |
| 36 | #44 AC8 toolchain + coverage + tiers | PASS | service 100%, dialogs 96–100% line; classified T2/T3/T4 | `poetry run pytest --cov --cov-branch` | |
| 37 | #44 AC9 existing suite green; known-file unchanged | PASS | 717 pass; no protected production file modified | `poetry run pytest`; `git diff --name-only` | |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 37 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. T1 mutation testing for `src/schema_formula.py` and `src/schema_loader.py` runs in the pre-merge/nightly pipeline per `quality-tiers.md`; it is not part of the per-commit loop and does not gate this cycle.
2. Proceed to PR; the orchestrator S9 CI green gate provides the runner-side confirmation of the locally-verified toolchain.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All 37 criteria evaluated **PASS**. They are represented as markdown checkboxes in the child `spec.md`/`user-story.md` files and were already checked off `[x]` during plan execution (confirmed via `artifacts/pr_context.summary.txt` "Acceptance Criteria" rollup, where every item is `[x]`).
- No criterion is PARTIAL/FAIL/UNVERIFIED, so no item needs to remain unchecked.
- No source-file checkbox change was required by this re-audit because all 37 were already checked off by the executors before the cycle-0 audit and remain valid after the test-only remediation.

### AC Status Summary

- Source: child `spec.md` + `user-story.md` for #41, #42, #43, #44
- Total AC items: 37
- Checked off (delivered): 37
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `2026-05-30-schema-model-and-registry-41/spec.md` + `user-story.md` | 9 | 9 | 0 | Checkbox-backed |
| `2026-05-30-schema-matching-and-discovery-42/spec.md` + `user-story.md` | 8 | 8 | 0 | Checkbox-backed |
| `2026-05-30-configurable-etl-core-43/spec.md` + `user-story.md` | 11 | 11 | 0 | Checkbox-backed |
| `2026-05-30-gui-schema-builder-44/spec.md` + `user-story.md` | 9 | 9 | 0 | Checkbox-backed |

No source-file checkbox change was made by this re-audit; all 37 items were already `[x]` before the cycle entered, and all remain PASS after the test-only F1/F2 remediation.
