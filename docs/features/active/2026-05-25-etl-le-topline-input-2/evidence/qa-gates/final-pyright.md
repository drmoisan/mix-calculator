# Final QA — Pyright

Timestamp: 2026-05-25T21-02
Command: `poetry run pyright` (run as `env -u VIRTUAL_ENV poetry run pyright` per VIRTUAL_ENV quirk)
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. Strict mode unchanged (`typeCheckingMode = "strict"`, `reportMissingTypeArgument = "error"`). No strictness narrowing; no unjustified `# type: ignore`. The two `# pyright: ignore[reportUnknownMemberType]` are narrowly scoped to untyped-library boundary calls and documented inline. `pandas-stubs` was added as a dev dependency to provide pandas typing under strict mode.
