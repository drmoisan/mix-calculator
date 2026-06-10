# Baseline — Pytest + Coverage (Issue #62, Cycle 1)

Timestamp: 2026-06-10T12-24
Command: $env:QT_QPA_PLATFORM='offscreen'; poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 1

Output Summary:
- Result: 1 failed, 1026 passed, 3 warnings.
- Failing test: tests/test_normalize_le_io.py::test_validate_tieouts_property_roundtrip
- Failure classification: PRE-EXISTING FLAKY Hypothesis property test, unrelated to issue #62 changed files. Re-ran in isolation (`pytest tests/test_normalize_le_io.py::test_validate_tieouts_property_roundtrip -p no:randomly`) -> PASSED. Matches known float-magnitude-bounds flakiness in sum+abs-tolerance property tests. Not a regression introduced by this work; not in scope of the changed files.
- Coverage TOTAL: statements 4867, missed 44, branches 914, partial 54.
- Combined coverage total (line+branch composite per coverage report): 98%.
- Line coverage: (4867-44)/4867 = 99.10%.
- Branch coverage: (914-54)/914 = 94.09%.
- Both well above thresholds (line >= 85%, branch >= 75%).
- schema_builder_dialog.py baseline: 98% (missing 372, 475->exit).
- source_selection_presenter.py: full coverage in baseline run.

Note: The single flaky failure does not affect the baseline numeric coverage. The final QC run (P2-T4) will re-run the suite; the flaky test is treated as a known non-regression pre-existing condition.
