# Phase 4 — End-to-end test decision

Timestamp: 2026-05-29T13-35

Decision: P0-T9 concluded "no existing canonical-workbook test present." Per P4-T2, an in-memory smoke test was added: `tests/test_mix_pipeline.py::test_mix_pipeline_nrr_summary_check_ok`.

Outcome:
- New test PASSES on the post-change pipeline.
- Assertion: `nrr_summary` contains exactly one `metric == "Check"` row with `check == "CHECK"`.
- The fabricated workbook uses a single customer (`Acme Foods`) with consistent casing, so the case-insensitive join change is exercised end-to-end without changing aggregate values. The synthetic Winco/WINCO unit tests in `tests/test_mix_lookups.py` cover the case/whitespace-collapse behavior at the transform layer.
