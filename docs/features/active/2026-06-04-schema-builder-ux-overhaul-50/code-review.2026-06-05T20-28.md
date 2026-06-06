# Code Review — schema-builder-ux-overhaul (Issue #50)

- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main` (merge-base `5e659f2`); Head: `d8275d9`
- Reviewer: feature-review agent
- Timestamp: 2026-06-05T20-28
- Scope: full branch diff against `main`

## Executive Summary

Verdict: PARTIAL (blocking). The code is well factored at the unit level:
modules are small and cohesive, pure logic is separated from Qt widgets behind
view-protocol seams, docstrings and intent comments meet the commenting policy,
and the toolchain is green. The model-layer work (expected_dtype field, version
bump, forward migration, structured key parts, aggregate dedup mode) is
correct and integrated.

The blocking issues are integration defects, not local code-quality defects: a
substantial set of new modules (drag-and-drop Columns/Key tabs, the
PowerQuery-style derived-formula dialog, the dtype-check widget) and two
presenter seams (`new_from_template`, `on_partial_match`) and the per-tab
build-spec provider are implemented and unit-tested but never imported or
invoked from the composition root. The dialog the user actually opens still
renders the pre-feature plain-text editors. These are counted as acceptance-
criteria FAILs in `feature-audit.2026-06-05T20-28.md`; this review records the
underlying code observations.

A secondary, non-blocking finding: a no-op `# noqa: N802` pattern and one
test module over the 500-line cap.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocking | src/gui/widgets/_schema_builder_tabs.py | build_columns_tab L160-172, build_key_tab L175-187, build_derived_tab L213-227 | The live Schema Builder still builds plain-text/single-line editors ("One column per line", "Key columns (comma-separated)", "One derived column per line"); the new drag widgets and formula dialog are not used. | Wire `_columns_tab_drag`, `_key_tab_drag`, `_derived_formula_dialog`, `_dtype_check_widget` into `SchemaBuilderDialog` so the redesigned UI is what the user opens. | The drag/dtype/formula redesign (spec Decisions 4,5,7) is unreachable in production; tests pass against isolated widgets only. | `grep` shows zero production importers of the four new widget modules; dialog adds the old build_* tab controls. |
| Blocking | src/gui/presenters/schema_builder_presenter.py | new_from_template L231 | `new_from_template` has no production caller (only two test callers). | Invoke from the new-from-template UI affordance once the partial-match path is wired. | Decision 6 new-from-template flow is unreachable. | `grep ".new_from_template("` matches only `tests/gui/test_schema_builder_presenter.py:365,387`. |
| Blocking | src/gui/app.py | build_application L340-347 | The three `SourceSelectionPresenter` instances are constructed without `on_partial_match`, so partial-match activation silently no-ops (placeholder set, no affordance). | Inject an `on_partial_match` callback that opens the new-from-template builder for the closest schema. | Decision 6 partial-match → new-from-template entry point never fires in production. | `on_partial_match` referenced in production only as the unused `None`-default param; wired only in `tests/gui/test_source_selection_presenter.py:318`. |
| Blocking | src/gui/_schema_discovery_wiring.py | wire_build_schema_buttons call L74 | Per-tab "Build/Edit schema" buttons are wired without a `spec_provider`, so they open a blank builder (no required/optional specs, default key pattern, or masked preview slice). | Construct a `BuildSpecProvider` at the composition root and pass it; supply each source's specs, key pattern, and masked preview slice. | Decision 7 / caller-contract AC unsatisfied in production. | No `BuildSpecProvider` is instantiated anywhere in `src/`; provider seam exercised only by tests. |
| Minor | src/gui/widgets/_columns_tab_drag.py; src/gui/widgets/_key_tab_drag.py | columns L78,207,222; key L76,169,252,267 | `# noqa: N802 - Qt override` suppresses a rule (`N`/pep8-naming) that is not in ruff `select`; the directive is a no-op. | Remove the unnecessary `noqa`, or enable the `N` ruleset if the convention is intended to be enforced. | Dead suppressions obscure which suppressions are load-bearing. | `pyproject.toml` `[tool.ruff.lint] select` omits `"N"`. |
| Minor | tests/test_schema_serialization.py | whole file (669 lines) | Test module exceeds the 500-line file cap; `.py` test modules are not cap-exempt. | Split into focused modules (e.g. serialization round-trip vs. migration). | File-size policy applies to test code. | `awk END{print NR}` = 669. |

## Detailed Observations

### Strengths (validated)

- Module decomposition matches the spec's planned split (`_schema_model_specs`,
  `_columns_tab_drag`, `_key_tab_drag`, `_derived_formula_dialog`,
  `_dtype_check_widget`, `_columns_tab_presenter`, `_key_tab_presenter`,
  `_source_input_button_wiring`). Each file is under the cap and single-purpose.
- View/presenter separation is clean: drag widgets translate a single drop
  gesture into one `on_drop(source, canonical)` / part-add callback
  (`_columns_tab_drag.py:236-238`, `_key_tab_drag.py:267+`), so presenter tests
  never simulate Qt drag events — a sound testability seam.
- Pure logic is isolated: `src/dtype_check.py` (coercion checks) and
  `src/gui/_schema_activation.py` (`classify_activation`) carry no Qt
  dependency and are well covered.
- Forward migration in `schema_serialization.py` is correct: omitted
  `expected_dtype` with `numeric: true` backfills `"float"`; version is always
  re-emitted as `SCHEMA_FORMAT_VERSION`.
- Discovery wiring itself is correct and IS reachable:
  `on_schema_discovery` is connected to `_tab_combo.currentTextChanged` via
  `wire_schema_discovery_and_gating` (called at `app.py:436`), and import
  gating is connected to `schema_selected`. Decisions 2, 8, 9 are wired.

### Root-cause pattern

The blocking findings share one cause: optional collaborator parameters were
added to wiring functions and presenters with `None` defaults, the new widgets
were built behind those seams, comprehensive unit tests were written against the
seams in isolation, but the final composition-root injection was not completed.
Unit-test coverage stays high because the tests construct the seams directly,
which masks the missing production wiring in the coverage figure.

## Code Review Verdict

PARTIAL (blocking). Four blocking integration defects; two minor non-blocking
items. No local code-quality defects (naming, error handling, typing, commenting,
tonality) were found. Blocking findings in this artifact: 4 — these are the same
underlying defects enumerated as AC FAILs in the feature-audit and are counted
once in the consolidated total there to avoid double-counting.
