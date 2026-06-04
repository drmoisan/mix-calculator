# Feature Audit: Pipeline GUI Hardening and Schema Selection (Issue #48, remediation cycle exit)

**Audit Date:** 2026-06-01
**Cycle exit timestamp:** 2026-06-01T23-52
**Feature Folder:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
**Base Branch:** `main` (merge base `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`)
**Head Branch:** `feature/pipeline-gui-hardening-schema-select-48` (working tree, uncommitted remediation edits on top of `c526e4f`)
**Work Mode:** `full-feature`
**Audit Type:** Remediation-cycle exit acceptance review (R-AC-1..R-AC-6 verification + AC-1..AC-15 no-regression)

---

## Scope and Baseline

- **Base branch:** `main` (commit `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`)
- **Head:** `feature/pipeline-gui-hardening-schema-select-48` working tree (remediation edits uncommitted on top of `c526e4f1cf988c02fcfbc2571249148327ad765e`)
- **Merge base:** `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`
- **Requirements source (full-feature):** `spec.md` (AC-1..AC-15 plus R-AC-1..R-AC-6) and `user-story.md`
- **Remediation requirements:** `remediation-inputs.2026-06-01T23-31.md` (defect + R-AC-1..R-AC-6)
- **Baseline AC reference:** `feature-audit.2026-06-01T15-30.md` (AC-1..AC-15 all PASS)
- **Evidence sources:** executor evidence under `evidence/baseline/` and `evidence/qa-gates/`; reviewer-reproduced `black --check`, `ruff check`, `pyright`, `pytest --cov --cov-branch`; `artifacts/python/lcov.info`.
- **Scope note:** Full branch-vs-base audit. No narrowing was requested or applied. The branch touches Python only.

---

## Acceptance Criteria Inventory

**Authoritative AC source files (full-feature work mode):**
- `spec.md` — primary; AC-1..AC-15 (original) and R-AC-1..R-AC-6 (remediation), checkbox-backed.
- `user-story.md` — secondary; user-facing summary mapping to the spec ACs, checkbox-backed.

The remediation cycle adds R-AC-1..R-AC-6 (from `remediation-inputs.2026-06-01T23-31.md`). The
original AC-1..AC-15 remain in scope for no-regression confirmation against the
`feature-audit.2026-06-01T15-30.md` baseline.

## Acceptance Criteria Evaluation

### Remediation criteria (R-AC-1..R-AC-6)

| # | Criterion | Status | Evidence | Verification command |
|---|-----------|--------|----------|----------------------|
| R-AC-1 | Empty user registry + no override: selectable names include `default_aop` and `default_le`. | PASS | `SchemaService.list_schema_names()` over the union-aware registry returns `["default_aop", "default_le"]` with an empty user dir; asserted at the service seam. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_service.py::test_service_lists_and_loads_bundled_defaults_when_user_dir_empty` |
| R-AC-2 | User-saved name colliding with a bundled name wins; appears once. | PASS | `list_schemas()` returns `["default_aop"]` (count == 1) and `load("default_aop")` returns the user schema, not the bundled one. | `poetry run pytest tests/test_schema_registry.py::test_list_schemas_user_override_appears_once_and_resolves_to_user` |
| R-AC-3 | Each tab's dropdown populated at startup; `set_schema_list` has a production caller incl. bundled defaults. | PASS | `build_application` calls `populate_schema_lists([le_widget, aop_widget, skulu_widget], svc)`; all three combos carry the bundled-default names; focused test confirms one `set_schema_list` call per view. | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_app_wiring_schema_list.py` |
| R-AC-4 | Matching considers bundled defaults; matching headers yield `action="proceed"` and auto-select. | PASS | `find_best_match_in_registry(["Customer"], registry)` returns the bundled `default_aop` at score 1.0; `discover_schema` returns `action="proceed"` over the union seam. | `poetry run pytest tests/test_schema_matching_registry.py::test_find_best_match_and_discover_see_bundled_defaults` |
| R-AC-5 | Load a bundled-default name by name with no user file present. | PASS | `SchemaService.load_schema("default_aop")` returns the bundled schema when the user dir is empty (registry `load` bundled fallback). | `QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_service.py::test_service_lists_and_loads_bundled_defaults_when_user_dir_empty` |
| R-AC-6 | Additive: known-file loaders and user-registry persistence unchanged; AC-1..AC-15 still PASS. | PASS | `load_bundled_default` unchanged; user `save`/`load` round-trips through the user dir; full suite 811 passed; AC-supporting suites re-run green. | `poetry run pytest tests/test_schema_registry.py::test_additivity_bundled_default_and_user_round_trip_unchanged` |

---

## AC-1..AC-15 No-Regression Confirmation

All fifteen original criteria were PASS in `feature-audit.2026-06-01T15-30.md`. The remediation
diff touches only `src/schema_registry.py` (additive union/fallback), the new
`src/gui/_schema_list_wiring.py`, and one call site in `src/gui/app.py`; it changes no known-file
loader, no validation identity, no error surface, and no run gate. The reviewer re-ran the
AC-supporting suites and the full suite:

| AC group | Supporting suite | Result |
|---|---|---|
| AC-1, AC-2, AC-3 (KEY-mismatch via Qt modal, no stdin) | `tests/gui/test_pipeline_service_key_seam.py` | PASS (no regression) |
| AC-5, AC-6 (run gate; no cascading KeyError) | `tests/gui/test_pipeline_presenter_run_gate.py` | PASS (no regression) |
| AC-7 (modal + status-bar error surface) | `tests/gui/test_main_window_view.py` | PASS (no regression) |
| AC-8, AC-9, AC-10 (validate_aop 8+4 identity) | `tests/test_load_aop_helpers.py` | PASS (no regression) |
| AC-11, AC-12 (auto-select / placeholder) | `tests/gui/test_source_selection_presenter.py` | PASS (no regression); R-AC-4 restores AC-11 for shipped defaults |
| AC-1..AC-15 (whole-suite) | full `pytest --cov --cov-branch` | 811 passed, 0 failed |

AC-4 (no-console packaged build) and AC-13/AC-14/AC-15 are unaffected by the remediation diff and
remain PASS by inspection; the remediation introduces no confidential figures (diff scan returned
none) so AC-15 holds.

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 15 original (AC-1..AC-15) + 6 remediation (R-AC-1..R-AC-6) = 21
- **PARTIAL:** 0
- **UNVERIFIED:** 0
- **FAIL:** 0

**Top gaps preventing PASS:** None.

**Recommended follow-up:** After PR update, confirm the CI run against the head SHA is green
(standard gate; the diff touches no CI-gate paths, so `modified-workflow-needs-green-run` does not
require a pre-merge run — see policy audit Section 8).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria-tracking skill:

- AC-1..AC-15 remain `[x]` in `spec.md` (unchanged; verified still PASS this cycle).
- R-AC-1..R-AC-6 were appended to the `## Acceptance Criteria` section of `spec.md` by the executor
  (P5-T6) and are `[x]`; each is verified PASS above, so no checkbox change was required this review.
- `user-story.md` summary checkboxes map to the spec ACs and remain checked.

### Acceptance Criteria Status

- Source: `spec.md` (AC-1..AC-15, R-AC-1..R-AC-6) and `user-story.md` (summary)
- Total AC items: 15 + 6 = 21 (spec) + 7 (user-story summary)
- Checked off (delivered): 21 (spec) + 7 (user-story)
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 21 | 21 | 0 | AC-1..AC-15 + R-AC-1..R-AC-6; all `[x]`, all verified PASS. |
| `user-story.md` | 7 | 7 | 0 | Summary mapping to spec ACs; remains checked. |
