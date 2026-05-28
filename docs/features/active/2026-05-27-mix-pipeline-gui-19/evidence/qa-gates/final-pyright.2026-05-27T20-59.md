# Final QA — Pyright

Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new `Any`
introduced and no strictness reduction. Loose pytest-qt and pandas types were
contained behind typed Protocol views plus `typing.cast` (the same containment
pattern used in `src/pandas_io.py`) — no per-call `# type: ignore` suppressions.
