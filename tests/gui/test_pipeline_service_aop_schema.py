"""Schema-driven AOP import tests for :mod:`src.gui.pipeline_service` (issue #58).

Covers the five #58 AOP schema-path import behaviors extracted from
``tests.gui.test_pipeline_service`` to keep both modules under the 500-line
file-size cap: full-year-YTD import, partial-year-YTD (8+4) import,
broken-total pass-through, header-detection-driven read, and output-parity
against the prior loader. All Excel inputs are in-memory workbooks built by the
shared ``tests.aop_fixtures`` builders; no temporary files are created. The
shared ``_patch_loaders`` helper is imported from the original module so the
schema read boundaries are patched identically. Fabricated data only; no
confidential ``SKU Description`` or ``Category`` values appear.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.pipeline_service import PipelineService
from tests.aop_fixtures import make_aop_row
from tests.gui._pipeline_service_fixtures import _patch_loaders

if TYPE_CHECKING:
    import pytest


def _single_aop_row() -> dict[str, object]:
    """Build one fabricated AOP row with a partial-year (8+4) total profile."""
    months = [0.0, 0.0, 0.0, 0.0, *([10.0] * 8)]
    return make_aop_row(
        customer="Acme Foods",
        sku="SKU-001",
        type_="Gross Sales",
        months=months,
        customer_master="Master Group",
        description="Widget",
        ppg="PPG-1",
    )


def test_import_aop_imports_full_year_ytd_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_aop imports a full-year-YTD source (regression for #58) (AC-2).

    The full-year layout (no YTG column; YTD = full Jan..Dec sum) previously
    failed the legacy arithmetic-validating loader's 8+4 identity. The
    schema-driven path imports it successfully.
    """
    # Arrange: a full-year-YTD AOP workbook routed through the schema path.
    from tests.aop_fixtures import build_full_year_ytd_workbook

    workbook = build_full_year_ytd_workbook([_single_aop_row()])
    _patch_loaders(monkeypatch, workbook)
    service = PipelineService()

    # Act
    frame = service.import_aop("ignored.xlsx", "AOP1")

    # Assert: the source imported and the KEY column was established.
    assert "KEY" in frame.columns
    assert len(frame) == 1


def test_import_aop_imports_partial_year_ytd_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_aop imports a partial-year-YTD (8+4) source successfully (AC-3)."""
    # Arrange: a partial-year-YTD (YTG-bearing) AOP workbook via the default shape.
    from tests.aop_fixtures import build_aop_workbook

    workbook = build_aop_workbook([_single_aop_row()])
    _patch_loaders(monkeypatch, workbook)
    service = PipelineService()

    # Act
    frame = service.import_aop("ignored.xlsx", "AOP1")

    # Assert
    assert "KEY" in frame.columns
    assert len(frame) == 1


def test_import_aop_imports_source_with_broken_totals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_aop imports a source whose totals violate YTD == sum(months) (AC-1).

    The schema-driven AOP path applies no arithmetic identity validation, so a
    row whose YTD is inconsistent with its months imports without raising.
    """
    # Arrange: a row whose YTD is deliberately inconsistent with its month cells.
    from tests.aop_fixtures import build_aop_workbook

    row = _single_aop_row()
    row["YTD"] = 999999.0  # Violates any YTD == sum(...) identity.
    workbook = build_aop_workbook([row])
    _patch_loaders(monkeypatch, workbook)
    service = PipelineService()

    # Act: the broken-total source imports without raising.
    frame = service.import_aop("ignored.xlsx", "AOP1")

    # Assert: the violating total passes through (no validation, no fill).
    assert frame.loc[0, "YTD"] == 999999.0


def test_import_aop_header_detection_drives_the_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_aop resolves a non-default header offset via detect_header_row (AC-7).

    The fixture places the header at index 0 (a flat sheet). A hardcoded
    ``header=2`` would misread the sheet; detection succeeds, so the import
    yields the expected row.
    """
    # Arrange: a flat (header-at-index-0) AOP workbook.
    from tests.aop_fixtures import build_offset_header_workbook

    workbook = build_offset_header_workbook([_single_aop_row()], leading_rows=0)
    _patch_loaders(monkeypatch, workbook)
    service = PipelineService()

    # Act
    frame = service.import_aop("ignored.xlsx", "AOP1")

    # Assert: the header was detected at the non-default offset and the row loaded.
    assert "KEY" in frame.columns
    assert len(frame) == 1
    assert frame.loc[0, "Customer"] == "Acme Foods"


def test_import_aop_output_columns_and_key_match_prior_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_aop output column set/order and KEY composition match prior (AC-6).

    Asserts the natural source column order and the rebuilt KEY
    (``Customer + coerce_sku(SKU #) + Type``) for a populated source row.
    """
    # Arrange: a single populated AOP row. Build two identical workbooks so the
    # schema path and the prior loader read the same source independently.
    from src import load_aop
    from src.etl_key import coerce_sku
    from tests.aop_fixtures import build_aop_workbook

    row = _single_aop_row()
    workbook = build_aop_workbook([row])
    _patch_loaders(monkeypatch, workbook)
    service = PipelineService()

    # Act: the schema-driven import and the prior loader on an equivalent source.
    frame = service.import_aop("ignored.xlsx", "AOP1")
    prior = load_aop.load_aop(
        build_aop_workbook([row]), sheet="AOP1", key_mismatch="overwrite"
    )

    # Assert: the column set and order match the prior loader exactly, and the
    # rebuilt KEY (Customer + coerce_sku(SKU #) + Type) matches.
    assert list(frame.columns) == list(prior.columns)
    expected_key = f"{row['Customer']}{coerce_sku(row['SKU #'])}{row['Type']}"
    assert frame.loc[0, "KEY"] == expected_key
    assert prior.loc[0, "KEY"] == expected_key
