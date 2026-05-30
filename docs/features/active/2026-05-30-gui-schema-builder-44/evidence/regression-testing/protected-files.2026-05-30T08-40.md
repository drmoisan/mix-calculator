# THIS-feature Protected-Files Regression Check

Timestamp: 2026-05-30T08-40
Command: git status --porcelain ; git diff --name-only HEAD -- src/normalize_le.py src/load_aop.py src/load_skulu.py "src/mix_*.py" "src/etl_*.py" src/calculator.py "src/mix_pipeline*.py" "src/schema_*.py" "src/_schema_*.py" "src/_load_aop_helpers.py"
EXIT_CODE: 0

## Output Summary

Protected-path diff is EMPTY. No CLI/transform/loader module and no Feature
A/B/C `src/schema_*.py` / `src/_schema_*.py` / `src/_load_aop_helpers.py` module
was modified by Feature D. This satisfies the THIS-feature behavior-preservation
check; a non-empty protected-path diff would have been a Blocking finding.

## Allowed additive edits to existing GUI files (expected, listed separately)

- src/gui/app.py — additive: optional `schema_service` keyword on
  `build_application`, default service build, `wire_schema_builder` call, new
  `WiredApplication.schema_service` field. No existing wiring/default changed.
- src/gui/main_window.py — additive: Tools menu + "Schema Builder..." action,
  `schema_builder_requested` signal, `schema_builder_presenter` holder. No
  existing widget/signal/control-row changed.
- src/gui/pipeline_service.py — additive: `import_with_schema` on the Protocol
  and the class. `import_le`/`import_aop`/`import_skulu`/`import_sources`/
  `run_pipeline`/`save_to_db`/`open_db` signatures and behavior unchanged.
- src/gui/protocols.py — additive: two new view-protocol names re-exported from
  the new sibling module `src/gui/_schema_view_protocols.py`; the existing four
  protocols are unchanged and unmoved (the re-export keeps protocols.py under the
  500-line cap — see the executor note in the completion report).
- quality-tiers.yml — additive: tier entries for the nine new Feature D modules.
- tests/gui/fakes/fake_services.py, tests/gui/fakes/fake_views.py — additive:
  new fakes (`FakeSchemaService`, `FakeColumnMatchingView`, `FakeSchemaBuilderView`)
  plus `import_with_schema` on `FakePipelineService`. Existing fakes unchanged.

## New files created (untracked)

src/gui/_schema_view_protocols.py, src/gui/_schema_wiring.py,
src/gui/presenters/_schema_builder_state.py,
src/gui/presenters/column_matching_presenter.py,
src/gui/presenters/schema_builder_presenter.py,
src/gui/services/schema_service.py,
src/gui/widgets/_schema_builder_tabs.py,
src/gui/widgets/column_matching_dialog.py,
src/gui/widgets/schema_builder_dialog.py, plus seven new test files and the
evidence directory.

## Outcome

PASS. Protected paths unchanged; existing-GUI edits are additive and all 278
GUI tests (and the full 717-test suite) stay green.
