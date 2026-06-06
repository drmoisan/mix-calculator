# Batch 4 — example-aware dialog & seam gate (P4-T4)

Timestamp: 2026-06-06T12-45

Commands (in order; single clean pass after the Phase 3/4/5 cluster settled):

- Command: poetry run black .            EXIT_CODE: 0
- Command: poetry run ruff check .       EXIT_CODE: 0
- Command: poetry run pyright            EXIT_CODE: 0
- Command: poetry run pytest tests/gui/test_key_mismatch_dialog.py --cov=src.gui._key_mismatch_dialog --cov=src.gui._key_mismatch_seam --cov-branch --cov-report=term-missing   EXIT_CODE: 0

Output Summary:
- Final clean pass: Black 193 files unchanged; Ruff all checks passed; Pyright
  0 errors / 0 warnings; Pytest 8 passed.
- src/gui/_key_mismatch_dialog.py coverage: 100% line, 100% branch.
- src/gui/_key_mismatch_seam.py coverage: 62% in this subset (lines 50/63/82 are
  never_tty / no_stdin_prompt / the trust-return, all covered by
  tests/gui/test_pipeline_service_key_seam.py in the full run).
- Tests assert: example pairs rendered in the dialog body (AC-2); empty-examples
  branch omits the examples block; "Keep existing" is the default button (AC-4);
  trust/overwrite mapping (AC-4); composition root injects the resolver CALLABLE
  into the production service (AC-5).
