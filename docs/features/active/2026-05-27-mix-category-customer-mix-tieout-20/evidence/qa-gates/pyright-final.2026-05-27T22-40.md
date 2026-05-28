# Pyright Final QA

Timestamp: 2026-05-27T22-40

Command: `env -u VIRTUAL_ENV poetry run pyright tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py`

EXIT_CODE: 0

Output Summary:
- "0 errors, 0 warnings, 0 informations"
- Notes on mechanical adjustment required by the split: when the six fixture helpers moved into `tests/_mix_rollups_fixtures.py` and were imported by both test modules, Pyright (strict mode) initially raised `reportPrivateUsage` for the leading-underscore imports and `reportUnusedFunction` for the helpers that the new home module no longer used locally. Both diagnostics were resolved by adding an `__all__` list to `tests/_mix_rollups_fixtures.py` that declares the helpers as the module's intended public surface. No `# type: ignore` suppressions were added; no helper was renamed; no helper body was modified.
- After the `__all__` addition, the toolchain loop was restarted from Black; all four steps (Black, Ruff, Pyright, Pytest) completed clean in a single pass.
