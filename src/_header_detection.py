"""Detect the header row of an ETL source sheet by token matching.

The LE and AOP loaders historically read their source sheet with a hardcoded
``header=2`` (Excel row 3). That assumption holds for the standard pipeline
sheets but fails for flat sheets whose header sits on a different row (for
example ``LE84Data`` with its header on row index 0): reading such a sheet with
``header=2`` lands on a data row and column resolution fails. This module
locates the header row by detection so both loaders read with the correct index
regardless of how many leading rows a particular sheet carries.

Detection strategy (shared by both loaders):

    - Probe the sheet once with ``header=None`` so every row, including the
      label row, is returned as data under a positional integer column index.
    - Score each of the first ``max_rows`` rows by how many of the expected
      canonical tokens (normalized via :func:`src.etl_columns.normalize_name`)
      appear among that row's non-blank cells.
    - Select the topmost (smallest-index) row whose score is the highest, and
      accept it only when that score is at least ``min_match``. A label row
      scores far higher than any data row, and the ``min_match`` floor rejects a
      data row that coincidentally contains a few expected tokens (for example
      the twelve month tokens), so detection does not silently pick a data row.
    - Raise a clear :class:`ValueError` naming the sheet and expected columns
      when no row qualifies, rather than falling back silently.

This module performs the probe read through the typed :mod:`src.pandas_io`
boundary; it owns no other I/O and emits no logging. Detection is deterministic:
the same source and arguments always yield the same index. BytesIO sources are
rewound before the probe read so a buffer that a caller already consumed (or
will read again afterward) is positioned at offset 0.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from src.etl_columns import normalize_name
from src.pandas_io import read_excel_sheet

if TYPE_CHECKING:
    from src.pandas_io import ExcelSource

# Default number of leading rows scanned for the header. The standard sheets
# place the header on row index 2 and flat sheets on row index 0, so scanning
# the first five rows covers every observed layout with margin.
DEFAULT_MAX_ROWS: int = 5


def _rewind_if_seekable(source: ExcelSource) -> None:
    """Rewind a binary buffer source to offset 0 before a probe read.

    A filesystem path is opened fresh by pandas on each read and needs no
    rewind, but an in-memory ``BytesIO`` buffer keeps a shared read position: if
    a previous read advanced it, a subsequent ``read_excel`` would see no bytes.
    Rewinding only seekable buffers keeps repeated reads of the same buffer
    deterministic without affecting path-based callers.

    Args:
        source: The Excel source passed to detection (a path or a binary
            buffer).

    Returns:
        ``None``. Mutates the buffer's read position as a side effect when the
        source is a seekable :class:`io.IOBase` (for example ``BytesIO``).
    """
    # Only seekable in-memory buffers need rewinding; paths are reopened by
    # pandas on every read and have no shared position to reset.
    if isinstance(source, io.IOBase) and source.seekable():
        source.seek(0)


def detect_header_row(
    source: ExcelSource,
    sheet_name: str,
    expected_tokens: frozenset[str],
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    min_match: int,
) -> int:
    """Detect the zero-based header-row index of an ETL source sheet.

    Probes the sheet with no header so the label row is returned as data, scores
    each of the first ``max_rows`` rows by the count of expected (normalized)
    tokens present among that row's non-blank cells, and returns the topmost row
    whose score is the highest, provided that score meets ``min_match``.

    Args:
        source: Filesystem path or binary file-like buffer accepted by
            :func:`src.pandas_io.read_excel_sheet`. A seekable buffer is rewound
            to offset 0 before the probe read so repeated calls are
            deterministic.
        sheet_name: Name of the worksheet to scan.
        expected_tokens: The normalized expected canonical column tokens for the
            sheet (each produced via :func:`src.etl_columns.normalize_name`).
            The match score for a row is the size of the intersection between
            this set and the row's normalized non-blank cell tokens.
        max_rows: Maximum number of leading rows to scan (default
            :data:`DEFAULT_MAX_ROWS`). Bounded by the actual probe-frame length.
        min_match: Minimum number of expected tokens a row must contain to be
            accepted as the header. The selected row's score must be at least
            this value; otherwise no row qualifies and a ``ValueError`` is
            raised. This floor rejects data rows that coincidentally contain a
            few expected tokens.

    Returns:
        The zero-based index of the detected header row within the sheet.

    Raises:
        ValueError: When no scanned row's match score reaches ``min_match``. The
            message names the sheet, the scan window (``max_rows``), the
            ``min_match`` floor, and the expected columns so the operator can
            correct the source.

    Side effects:
        Reads the sheet once via openpyxl through the typed pandas boundary and
        rewinds a seekable buffer source to offset 0 before that read.
    """
    # Rewind a seekable buffer so the probe read starts at offset 0 even if a
    # prior read advanced the shared position.
    _rewind_if_seekable(source)

    # Probe with no header so every row (including the label row) is returned as
    # data under a positional integer column index, ready for token scoring.
    probe_frame = read_excel_sheet(source, sheet_name=sheet_name, header=None)

    # Score the leading rows; track the topmost row holding the highest score so
    # ties resolve to the smallest index (strict ">" only replaces on a higher
    # score, never on an equal one).
    best_index = 0
    best_score = -1
    scan_count = min(max_rows, len(probe_frame))
    # Walk each candidate header row and count how many expected tokens it
    # contains among its non-blank cells; the label row scores far above any
    # data row.
    for row_index in range(scan_count):
        row_tokens = frozenset(
            normalize_name(str(value))
            for value in probe_frame.iloc[row_index]
            if str(value).strip()
        )
        score = len(expected_tokens & row_tokens)
        if score > best_score:
            best_score = score
            best_index = row_index

    # Accept the best row only when it clears the min_match floor; a score below
    # the floor means even the best-matching row is a data row (or a sparse
    # label row), so detection fails loudly rather than guessing.
    if best_score < min_match:
        raise ValueError(
            "Could not locate the header row for sheet "
            f"'{sheet_name}': no row within the first {max_rows} rows matched "
            f"at least {min_match} expected column(s). Expected columns: "
            f"{sorted(expected_tokens)}."
        )

    return best_index
