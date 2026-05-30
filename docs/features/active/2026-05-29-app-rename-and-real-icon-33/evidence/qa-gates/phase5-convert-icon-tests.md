# Phase 5 — convert_icon tests (AC6)

Timestamp: 2026-05-29T20-25
Command: env -u VIRTUAL_ENV poetry run pytest tests/test_convert_icon.py -q
EXIT_CODE: 0
Output Summary: 3 passed in 0.26s. AC6 verified: synthetic SVG converts to multi-size ICO with the documented magic header and frame sizes {(16,16),(32,32),(48,48),(256,256)}; CLI path round-trips through the read/write seams; invalid SVG raises ValueError.

Toolchain confirmation:
- black --check packaging/velopack/convert_icon.py tests/test_convert_icon.py: EXIT 0
- ruff check packaging/velopack/convert_icon.py tests/test_convert_icon.py: EXIT 0
- pyright packaging/velopack/convert_icon.py tests/test_convert_icon.py: 0 errors, 0 warnings, 0 informations

Plan deviations (recorded for transparency):
- The plan called for `from packaging.velopack.convert_icon import ...` in the test file. Adding `packaging/__init__.py` to make that work shadowed the PyPI `packaging` package that pytest itself imports (pytest aborts with `ModuleNotFoundError: No module named 'packaging.version'`). The test file was therefore rewritten to load the converter via `importlib.util.spec_from_file_location` from its file path. The script's documented invocation `poetry run python packaging/velopack/convert_icon.py --input ... --output ...` is unchanged and is exercised in Phase 6 against the real source SVG.
- The plan's P5-T5/T6/T7 implementation guidance used a QBuffer-mediated PNG round-trip for QImage->PIL. PySide6 12.x rejects `QImage.save(QBuffer, b"PNG")` at runtime with `ValueError: wrong argument values`. The implementation uses direct pixel-buffer access via `QImage.convertToFormat(Format_RGBA8888)` + `constBits()` + `Image.frombytes("RGBA", ...)` with explicit stride correction when `bytesPerLine != width * 4`. This is the documented PySide6 alternative and matches the rest of the docstring contract.
- The `# type: ignore[import-untyped]` line referenced by P5-T9 is NOT added because Pillow 12.2.0 ships `py.typed` (phase4-pil-typed-probe.md).

File size cap (P5-T11):
- packaging/velopack/convert_icon.py: 358 lines (under 500 cap)
- tests/test_convert_icon.py: 151 lines (under 500 cap)
