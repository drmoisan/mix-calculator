# Final Pyright

Timestamp: 2026-06-08T17-58
Command: env -u VIRTUAL_ENV poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations (strict mode).

Note: initial runs reported reportPrivateUsage errors for cross-module imports of
the relocated private helpers (`_patch_loaders`, `_load_default`, `_MONTHS_A`,
`_MONTHS_B`). Resolved at the root cause by relocating those helpers into dedicated
underscore-prefixed shared fixture modules (tests/gui/_pipeline_service_fixtures.py
and tests/_schema_loader_fixtures.py) that declare `__all__` exporting the private
names. This mirrors the existing repo pattern in tests/_mix_rollups_fixtures.py and
introduces no suppression comments. A non-blocking notice about a newer pyright
version was emitted; it does not affect the exit code.
