# Batch 5 — cross-thread bridge & app wiring gate (P5-T5)

Timestamp: 2026-06-06T12-52

Commands (in order; single clean pass):

- Command: poetry run black .            EXIT_CODE: 0
- Command: poetry run ruff check .       EXIT_CODE: 0
- Command: poetry run pyright            EXIT_CODE: 0
- Command: poetry run pytest tests/gui/test_key_mismatch_bridge.py --cov=src.gui._key_mismatch_bridge --cov=src.gui.app --cov-branch --cov-report=term-missing   EXIT_CODE: 0

Output Summary:
- Final clean pass: Black all formatted; Ruff all checks passed; Pyright 0
  errors / 0 warnings; Pytest 4 passed.
- src/gui/_key_mismatch_bridge.py coverage: 100% line, 100% branch.
- src/gui/app.py: no rows in this subset (no app.py code executes in the bridge
  test module); app.py wiring (build_key_mismatch_resolver(window=window)) is
  exercised by tests/gui/test_key_mismatch_dialog.py's build_application test and
  confirmed in the Phase 6 full-suite run.
- Tests assert: the same-thread guard calls ask directly on the GUI thread with
  no threading.Event/block (AC-1); the cross-thread path marshals ask onto the
  GUI thread and unblocks the worker with the correct result for both True/False
  (AC-1); a GUI-thread ask exception is re-raised on the worker side and not
  swallowed.
