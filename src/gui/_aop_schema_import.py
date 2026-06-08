"""Schema-driven AOP import helper for the GUI pipeline service (issue #58).

Purpose:
    Provide the AOP-specific schema-load, header-detection, raw-read, and
    schema-transform sequence that ``PipelineService.import_aop`` delegates to.
    This logic was extracted from :mod:`src.gui.pipeline_service` so that module
    stays within the repository 500-line file cap; the behavior is unchanged.

Responsibilities:
    - Load the bundled ``default_aop`` schema.
    - Derive the expected header tokens from the schema's required columns.
    - Resolve the header row via :func:`src._header_detection.detect_header_row`
      (issue #55) rather than a hardcoded row.
    - Read the raw frame at the detected header and transform it via
      :class:`src.schema_loader.SchemaLoader`, forwarding the KEY-mismatch
      resolver and the no-stdin seams.

    It does NOT own the resolver or any service state; the service passes its
    injected resolver in.

Boundaries:
    Excel reads route through :func:`src._header_detection.detect_header_row`
    and :func:`src.pandas_io.read_excel_sheet` (both built on ``src.pandas_io``).
    No SQLite or network access occurs here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._key_mismatch_seam import never_tty, no_stdin_prompt

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from src.pandas_io import ExcelSource

# The optional AOP columns excluded from the required header-token set so the
# derived expected tokens match the legacy load_aop required-token set (KEY and
# YTG are resolved by name only and are not required for header detection).
_OPTIONAL_AOP_COLUMNS = frozenset({"KEY", "YTG"})

# Minimum number of expected tokens a row must contain to be accepted as the AOP
# header. Reproduces load_aop's detection floor (17 of the 24 required tokens)
# for behavioral parity with the legacy AOP header detection.
_AOP_HEADER_MIN_MATCH = 17


def import_aop_via_schema(
    source: ExcelSource,
    sheet: str,
    resolver: Callable[[list[tuple[str, str]]], str],
) -> pd.DataFrame:
    """Import an AOP source through the schema-driven loader (issue #58).

    Routes the AOP import through ``SchemaLoader(default_aop)`` instead of the
    legacy arithmetic-validating ``load_aop``: load the bundled ``default_aop``
    schema, derive the expected header tokens from its required columns, resolve
    the header row via :func:`src._header_detection.detect_header_row`, read the
    raw frame at the detected header, and transform it via ``SchemaLoader.load``.
    The schema has empty ``fill_rules`` (issue #58 Decision 2), so blank totals
    coerce to ``0`` and no per-row arithmetic identity is validated; a source
    whose totals violate ``YTD == sum(months)`` imports without error.

    Args:
        source: Filesystem path to the AOP workbook (or, in tests, a seekable
            in-memory buffer accepted by ``detect_header_row``/
            ``read_excel_sheet``).
        sheet: AOP worksheet name.
        resolver: Example-aware KEY-mismatch resolver forwarded to
            ``SchemaLoader.load`` as the divergence-only ``resolver`` (the
            callable, not its result). It is invoked only on a genuine KEY
            divergence and returns ``"trust"`` or ``"overwrite"``.

    Returns:
        The schema-driven AOP DataFrame with canonical column names and an
        established ``KEY`` column.

    Raises:
        ValueError: Propagated from header detection (no row meets the token
            floor) or from the schema loader on a column-resolution or
            KEY-resolution failure.
    """
    # Import the schema-path collaborators locally so this module's top-level
    # import surface stays minimal and so tests can patch the read boundary and
    # SchemaLoader.load at their source modules. detect_header_row and
    # read_excel_sheet are the shared header-aware read boundary used by the
    # protected loaders.
    from pathlib import Path

    from src._header_detection import detect_header_row
    from src.etl_columns import normalize_name
    from src.pandas_io import read_excel_sheet
    from src.schema_loader import SchemaLoader
    from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

    # Load the bundled default AOP schema. load_bundled_default ignores the
    # registry_dir argument and resolves the schema from the packaged bundled_dir
    # via the disk store, exactly as the parity tests construct it.
    schema = SchemaRegistry(Path("."), DiskSchemaFileStore()).load_bundled_default(
        "default_aop"
    )

    # Derive the expected header tokens from the schema's required columns,
    # excluding the optional KEY and YTG columns to match the legacy load_aop
    # required-token set.
    expected_tokens = frozenset(
        normalize_name(column.canonical_name)
        for column in schema.columns
        if column.canonical_name not in _OPTIONAL_AOP_COLUMNS
    )
    detected = detect_header_row(
        source, sheet, expected_tokens, min_match=_AOP_HEADER_MIN_MATCH
    )

    # Read the raw frame at the detected header through the typed pandas_io
    # boundary. detect_header_row already rewinds a seekable buffer before its own
    # probe; read_excel_sheet reopens a path or reads the rewound buffer.
    raw = read_excel_sheet(source, sheet_name=sheet, header=detected)

    # Transform via the schema loader. Forward the resolver CALLABLE (not its
    # result) plus the no-stdin seams so a diverging AOP KEY resolves through the
    # injected resolver (a Qt modal dispatched on the GUI thread via the
    # composition-root bridge) only on a genuine divergence, never eagerly and
    # never via stdin (issue #52).
    return SchemaLoader(schema).load(
        raw,
        resolver=resolver,
        is_tty=never_tty,
        prompt=no_stdin_prompt,
    )
