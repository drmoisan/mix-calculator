# Phase 1 QA Gate

Phase 1 — Dev Dependency, Tier Scaffolding, View Protocols.
Single clean pass of the full toolchain loop (Black -> Ruff -> Pyright -> Pytest).

## Black

Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 41 files left unchanged; 0 reformatted.

## Ruff

Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors. (Resolved an initial TC003 by moving
`collections.abc.Iterator` into a `TYPE_CHECKING` block in `tests/gui/conftest.py`.)

## Pyright

Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). (Resolved an initial
`reportUnusedFunction` on the autouse fixture by exporting it via `__all__`; no suppression,
no strictness reduction.)

## Pytest (coverage)

Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 185 passed, 0 failed. Determinism confirmed across 3 consecutive clean runs.
- Repository line coverage: 98% (TOTAL 899 stmts, 18 missed); branch coverage: 100%.
- `src/gui/protocols.py` shows 0% (interface-only Protocols not yet imported by any test); it
  is exercised in later phases via `runtime_checkable` isinstance checks and fake implementations.
- No regression on changed lines: all pre-existing `src/` modules remain at 100%.
- Coverage gate satisfied repository-wide: line 98% >= 85%, branch 100% >= 75%.

## Notes

- Added `pytest-qt = ">=4.4"` (installed 4.5.0) to the dev group — the single approved new dependency.
- Added `mix-pipeline-gui = "src.gui.app:main"` to `[tool.poetry.scripts]`.
- Added two narrow coverage exclusions in `[tool.coverage.report]` for stub bodies:
  `@(typing\.)?overload` and bare-ellipsis lines `^\s*\.\.\.\s*$`. These exclude only
  non-executable interface stub bodies (Protocol/overload), mirroring how `src/pandas_io.py`
  Protocol stubs are excluded under `TYPE_CHECKING`. They do not mask any executable logic.
- `quality-tiers.yml`: added `src/gui/__init__.py: T4` and `src/gui/protocols.py: T2`.
