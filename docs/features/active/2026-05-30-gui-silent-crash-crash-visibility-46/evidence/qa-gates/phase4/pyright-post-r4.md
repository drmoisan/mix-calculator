# Phase 4 — Pyright (Post-R4)

- Timestamp: 2026-05-31T02-43
- Command: `poetry run pyright`
- EXIT_CODE: 0
- Output Summary: 0 errors, 0 warnings, 0 informations.

Iteration notes:
- First pyright run after writing the three R4 tests reported one error: `_FakeHandle` returned from `_FakePath.open` did not satisfy `IO[Any]`. Resolved by widening the return type annotation to `Any` (with a docstring explaining why the wrapper doesn't implement the full `IO[Any]` protocol — production code only uses `write` and context-manager `__enter__/__exit__`).
- After the widening, pyright is clean. No new `# pyright: ignore` suppressions added.
