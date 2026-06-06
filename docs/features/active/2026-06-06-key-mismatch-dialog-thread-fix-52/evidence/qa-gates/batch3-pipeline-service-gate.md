# Batch 3 — PipelineService resolver-forwarding gate (P3-T3)

Timestamp: 2026-06-06T12-35

Note on sequencing: the PipelineService callable-forwarding change requires the
example-aware resolver contract to exist end-to-end. Per the plan's explicit
allowance to interleave Phase 4 (dialog) and Phase 5 (bridge) with Phase 3, the
seam signature (P4-T1), bridge (P5-T1), dialog (P4-T2), and app wiring (P5-T2)
were landed alongside this change so the type chain resolves. This gate's
toolchain run therefore covers the whole interdependent cluster.

Commands (in order; loop restarted once when Black reformatted a docstring line
in test_key_mismatch_dialog.py; final pass clean):

- Command: poetry run black .            EXIT_CODE: 0
- Command: poetry run ruff check .       EXIT_CODE: 0
- Command: poetry run pyright            EXIT_CODE: 0
- Command: poetry run pytest tests/gui/test_pipeline_service_key_seam.py tests/gui/test_pipeline_service.py --cov=src.gui.pipeline_service --cov-branch --cov-report=term-missing   EXIT_CODE: 0

Output Summary:
- Final clean pass: Black all formatted; Ruff all checks passed; Pyright 0
  errors / 0 warnings; Pytest 17 passed for the two named modules.
- src/gui/pipeline_service.py coverage: 95% line, 0 branches in this subset
  (missing 377-381 is `import_sources`, covered by other suites in the full run).
- Reworked seam tests assert the resolver CALLABLE (not its result) is forwarded
  to both LE and AOP loaders as `resolver=`, and that the resolver is NOT invoked
  on the no-divergence path (call count 0), confirming AC-5 and no eager firing.
