# Final QA — Pytest (coverage)

Timestamp: 2026-06-06T15-55
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 966 passed, 3 warnings in ~24s. 0 failed.
- LE parity (5) and AOP parity (4) tests pass — top invariant preserved.
- TOTAL: Stmts=4725, Miss=44, Branch=872, BrPart=51, combined Cover 98%.
- Line coverage: (4725-44)/4725 = 99.07%.
- Branch coverage: (872-51)/872 = 94.15%.
- Per-module coverage of edited files: _schema_model_specs 100%, schema_serialization 98%,
  _schema_loader_helpers 92%, _schema_view_protocols 100%, schema_builder_presenter 98%,
  _columns_tab_presenter 93%, _schema_builder_state 94%, _schema_builder_drag_tabs 96%,
  schema_builder_dialog 98%, _schema_provider_factory 95%. Missing lines are pre-existing,
  not changed by this feature.
