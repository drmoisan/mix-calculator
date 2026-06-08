"""Shared loader-patching fixture for the PipelineService test modules (#58).

Holds the ``_patch_loaders`` helper used by both
``tests.gui.test_pipeline_service`` and
``tests.gui.test_pipeline_service_aop_schema``. The module name is
underscore-prefixed so the helper stays test-private while being importable
across the two cohesive test modules without duplication. All Excel inputs are
in-memory ``BytesIO`` buffers; no temporary files are created.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import io

    import pandas as pd
    import pytest

__all__ = ["_patch_loaders"]


def _patch_loaders(monkeypatch: pytest.MonkeyPatch, buffer: io.BytesIO) -> None:
    """Patch the source reads to read a single shared in-memory buffer.

    The LE and SKU_LU loaders are patched at the loader entry point. The AOP
    import now routes through the schema-driven path (issue #58), which reads via
    :func:`src._header_detection.detect_header_row` and
    :func:`src.pandas_io.read_excel_sheet` rather than ``load_aop.load_aop``; so
    those two read boundaries are re-targeted to substitute the shared buffer for
    the AOP path argument. LE and SKU_LU never reach those boundaries because
    they are intercepted at their loader entry points, so re-targeting the shared
    read boundary affects only the AOP path here.
    """
    from src import _header_detection, load_skulu, normalize_le, pandas_io

    real_load_source = normalize_le.load_source
    real_load_skulu = load_skulu.load_skulu
    real_detect_header_row = _header_detection.detect_header_row
    real_read_excel_sheet = pandas_io.read_excel_sheet

    def _fake_load_source(
        _path: str, sheet: str, *, key_mismatch: str = "prompt", **_kwargs: object
    ) -> object:
        # Absorb the WS1a is_tty/prompt seams the service now forwards (issue #48).
        buffer.seek(0)
        return real_load_source(buffer, sheet, key_mismatch=key_mismatch)

    def _fake_detect_header_row(
        _source: object,
        sheet_name: str,
        expected_tokens: frozenset[str],
        *,
        min_match: int,
        max_rows: int = 5,
    ) -> int:
        # Redirect the AOP schema path's header detection to the shared buffer.
        buffer.seek(0)
        return real_detect_header_row(
            buffer,
            sheet_name,
            expected_tokens,
            min_match=min_match,
            max_rows=max_rows,
        )

    def _fake_read_excel_sheet(
        _source: object, *, sheet_name: str, header: int | None = 0
    ) -> pd.DataFrame:
        # Redirect the AOP schema path's frame read to the shared buffer.
        buffer.seek(0)
        return real_read_excel_sheet(buffer, sheet_name=sheet_name, header=header)

    def _fake_load_skulu(_path: str, *, sheet: str = "SKU_LU") -> object:
        buffer.seek(0)
        return real_load_skulu(buffer, sheet=sheet)

    monkeypatch.setattr("src.normalize_le.load_source", _fake_load_source)
    monkeypatch.setattr(
        "src._header_detection.detect_header_row", _fake_detect_header_row
    )
    monkeypatch.setattr("src.pandas_io.read_excel_sheet", _fake_read_excel_sheet)
    monkeypatch.setattr("src.load_skulu.load_skulu", _fake_load_skulu)
