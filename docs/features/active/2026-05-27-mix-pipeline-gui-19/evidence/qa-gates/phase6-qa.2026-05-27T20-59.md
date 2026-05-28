# Phase 6 QA Gate

Phase 6 — Presenter Fakes and SourceSelectionPresenter. Single clean pass of the toolchain loop.

## Black
Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 63 files left unchanged (after a reformat restart).

## Ruff
Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors. ARG002 mock-signature suppressions on the
fake-service Protocol methods use the pre-authorized format (`# noqa: ARG002 - match ... API`).

## Pyright
Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new Any.

## Pytest (coverage)
Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 226 passed (217 prior + 9 new), 0 failed. Determinism confirmed across 2 runs.
- `src/gui/presenters/source_selection_presenter.py`: 100% line, 100% branch.
- `src/gui/protocols.py`: now 100% (a runtime-checkable isinstance test imports the module at runtime,
  executing the Protocol class/method definitions).
- Repository TOTAL: 100% line, 100% branch. Gate satisfied (>= 85% line, >= 75% branch).
- No regression on changed lines.

## Notes
- `quality-tiers.yml`: added `src/gui/presenters/__init__.py: T4`,
  `src/gui/presenters/source_selection_presenter.py: T2`.
- Presenter has no Qt import and runs with no QApplication; uses standard `logging` (info/error).
- Reader `ValueError` routes to `view.show_error`; other exceptions propagate.
- T2 property test (hypothesis): the tab list pushed to the view equals the reader output for any
  list of names.
- ARG002 suppressions limited to fake mock signatures per the pre-authorized pattern.
- Confidentiality: fabricated values only.
