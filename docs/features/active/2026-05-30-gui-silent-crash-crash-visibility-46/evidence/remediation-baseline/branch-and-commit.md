# Remediation Baseline — Branch and Commit (Cycle 2)

- Timestamp: 2026-05-31T03-25
- Command:
  - `git rev-parse --abbrev-ref HEAD`
  - `git rev-parse HEAD`
- EXIT_CODE: 0
- Output Summary:
  - Branch: `bug/gui-silent-crash-crash-visibility-46`
  - HEAD: `e17da56195d576de38faf47cfbfca2382ca702f1` (matches the cycle-2 entry HEAD `e17da56` cited in the remediation inputs)

## In-scope file list (cycle 2)

- `tests/gui/test_crash_handler.py`
- `tests/gui/test_crash_handler_closures.py` (NEW)
- `tests/gui/test_app_composition.py`
- `tests/gui/test_runners_threaded.py`
- `tests/gui/test_pipeline_worker.py`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pytest.md`
