# Phase 6 — Pytest Cross-Check (Phase 4 vs Phase 8)

- Timestamp: 2026-05-31T03-25
- Command: manual diff of `evidence/qa-gates/phase4/pytest.md` and `evidence/qa-gates/phase8/pytest.md`
- EXIT_CODE: 0
- Output Summary:
  - Both artifacts cite the same `Command: poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  - Both report `EXIT_CODE: 0`.
  - Headline pass count matches: 737 passed in both.
  - Total line coverage matches: 99% in both.
  - Total branch coverage matches: 96.5% in both.
  - `src/gui/_crash_handler.py` per-file coverage matches: 100% line / 100% branch in both.
  - `src/gui/_crash_handler_bootstrap.py` matches: 100% in both.
  - Both artifacts confirm the three closure-invocation tests run from `tests/gui/test_crash_handler_closures.py`.
  - The two pytest artifacts agree on every checked value.
