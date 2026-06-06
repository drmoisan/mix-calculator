# Final QA — Pyright type check (P6-T3)

Timestamp: 2026-06-06T13-06

Command: poetry run pyright

EXIT_CODE: 0

Output Summary: 0 errors, 0 warnings, 0 informations. The example-aware resolver
contract (`Callable[[list[tuple[str, str]]], str]`) is type-clean across
etl_key, both loaders, pipeline_service, the seam, the dialog, the bridge, and
app.py. No typing strictness was weakened.
