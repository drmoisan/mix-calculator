"""Load and validate the ``AOP1`` planning sheet into a SQLite table.

This module is the AOP sibling of :mod:`src.normalize_le`. It reads the
``AOP1`` sheet into a pandas DataFrame, resolves the documented schema
position-independently, establishes the business ``KEY`` via the shared
reconcile policy, validates per-row total identities, optionally applies a
caller-supplied transform, and persists the result to SQLite with lookup
indexes.

Unlike the LE normalizer, AOP does not collapse rows by ``KEY`` and does not
apply the LE ``Super Category <- PPG`` quirk; every source data row is preserved
and the original headers (including the intentional ``SKU Descripiton`` typo)
are kept unless ``--snake-case`` is requested.

All transform logic reuses the neutral ETL leaf modules and the ``src.pandas_io``
read/write boundary; no shared helper is re-implemented here. The AOP schema
constants and the pure transform/validation/summary helpers live in
:mod:`src._load_aop_helpers` so this module stays under the 500-line file limit;
they are re-exported here so callers and tests can import them from
``src.load_aop``.

Boundaries:
    - ``load_aop`` reads via ``src.pandas_io.read_excel_sheet`` (openpyxl).
    - ``persist_aop`` writes via ``src.pandas_io.write_table`` (SQLite).
    - Validation and sentinel cleaning are pure transforms with no I/O.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import sys
from typing import IO, TYPE_CHECKING

from src._load_aop_helpers import (
    EXPECTED_COLUMNS,
    INDEX_COLUMNS,
    LABEL_COLUMNS,
    MONTHS,
    NUMERIC_COLS,
    QUARTER_COLUMNS,
    QUARTER_TO_MONTHS,
    SNAKE_CASE_RENAMES,
    SOURCE_COLUMNS,
    TARGET_COLUMNS,
    TIEOUT_TOL,
    YTG_MONTHS,
    build_parser,
    build_per_row_checks,
    clean_label_sentinels,
    coerce_numeric,
    print_summary,
    safe_index_name,
    validate_aop,
)
from src.etl_columns import normalize_name, resolve_columns
from src.etl_key import resolve_key
from src.etl_totals import fill_blank_totals
from src.pandas_io import read_excel_sheet, write_table

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

# Re-export the AOP schema constants and pure helpers so callers and tests can
# import them from this module as well as from ``src._load_aop_helpers``. The
# constants and pure helpers live in the helper module so this file stays under
# the 500-line limit.
__all__ = [
    "EXPECTED_COLUMNS",
    "INDEX_COLUMNS",
    "LABEL_COLUMNS",
    "MONTHS",
    "NUMERIC_COLS",
    "QUARTER_COLUMNS",
    "QUARTER_TO_MONTHS",
    "SNAKE_CASE_RENAMES",
    "SOURCE_COLUMNS",
    "TARGET_COLUMNS",
    "TIEOUT_TOL",
    "YTG_MONTHS",
    "clean_label_sentinels",
    "coerce_numeric",
    "load_aop",
    "main",
    "persist_aop",
    "print_summary",
    "validate_aop",
]

logger = logging.getLogger(__name__)

# Accepted inputs for the Excel read boundary: a filesystem path or a binary
# file-like buffer (the in-memory test fixtures pass a BytesIO).
ExcelSource = str | IO[bytes]

# Values that disable debug mode when set in ``LOAD_AOP_DEBUG``. An unset
# variable is also treated as falsey; anything not in this set is truthy.
_FALSEY_DEBUG_VALUES = frozenset({"", "0", "false", "no"})


def _debug_env_is_truthy(raw: str | None) -> bool:
    """Return whether a ``LOAD_AOP_DEBUG`` value requests debug mode.

    Args:
        raw: The raw environment-variable value as returned by
            ``os.environ.get`` (``None`` when the variable is unset).

    Returns:
        ``False`` when ``raw`` is ``None`` or, after stripping and
        case-folding, equals one of ``""``, ``"0"``, ``"false"``, or
        ``"no"``; ``True`` for any other value.
    """
    # Treat an unset variable as falsey; otherwise compare case-insensitively
    # against the explicit falsey set so only intentional values enable debug.
    if raw is None:
        return False
    return raw.strip().casefold() not in _FALSEY_DEBUG_VALUES


def load_aop(
    source: ExcelSource,
    *,
    sheet: str = "AOP1",
    transform: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
    key_mismatch: str = "prompt",
    is_tty: Callable[[], bool] = sys.stdin.isatty,
    prompt: Callable[[str], str] = input,
    resolver: Callable[[list[tuple[str, str]]], str] | None = None,
) -> pd.DataFrame:
    """Load, clean, validate, and return the ``AOP1`` sheet as a DataFrame.

    Reads the workbook treating Excel row 3 as the header (``header=2``),
    resolves the source columns to canonical names position-independently,
    establishes the ``KEY`` column per the shared reconcile policy, validates
    per-row total identities, and finally applies the optional ``transform``.

    Both ``KEY`` and ``YTG`` are optional columns resolved by name. ``YTG`` is
    used when present (carried through, coerced, blank-filled, and validated as
    ``YTG == sum(May..Dec)``) and is neither derived nor added when absent; older
    AOP sheets predate it. Unlike :mod:`src.normalize_le`, this loader never
    derives a ``YTG`` column.

    Args:
        source: Filesystem path or binary file-like buffer accepted by
            ``read_excel_sheet`` (see :data:`ExcelSource`).
        sheet: Name of the worksheet to read (default ``"AOP1"``).
        transform: Optional callable applied to the validated frame after
            validation and before return. When ``None`` the frame is returned
            as validated.
        key_mismatch: The ``--key-mismatch`` policy applied when a present
            ``KEY`` column diverges from the rebuilt pattern.
        is_tty: Zero-arg callable returning whether stdin is interactive
            (injectable for tests; defaults to ``sys.stdin.isatty``). Passed
            through to :func:`src.etl_key.resolve_key`.
        prompt: Callable used to ask the user on the interactive prompt path
            (injectable for tests; defaults to the built-in ``input``).
        resolver: Optional example-aware KEY-mismatch resolver forwarded to
            :func:`resolve_key`. When supplied (the GUI path) it is invoked only
            on a genuine divergence with up to three ``(existing, rebuilt)``
            example pairs and returns ``"trust"`` or ``"overwrite"``. When
            ``None`` (the default and the CLI path), divergence is resolved via
            ``key_mismatch``/``is_tty``/``prompt`` exactly as before (issue #52,
            AC-5/AC-6).

    Returns:
        A validated DataFrame with canonical column names and an established
        ``KEY`` column, with blank-``Customer`` rows removed and the optional
        ``transform`` applied.

    Raises:
        ValueError: When a required column cannot be resolved (from
            :func:`resolve_columns`), when a diverging ``KEY`` cannot be resolved
            (from :func:`resolve_key`), or when per-row validation fails.

    Side effects:
        Reads from the filesystem (or buffer) via openpyxl and emits ``logging``
        warnings for extra source columns, KEY resolution, and duplicate KEYs.
    """
    # Route the read through the typed pandas_io boundary, which contains the
    # openpyxl-driven unknown member type so it does not surface here.
    frame: pd.DataFrame = read_excel_sheet(source, sheet_name=sheet, header=2)
    actual_columns = list(frame.columns.astype(str))

    # Locate an optional KEY column by normalized name only (no fuzzy match) so
    # it is neither a required expected column nor reported as an extra.
    key_actual: str | None = None
    for column in actual_columns:
        if normalize_name(column) == "key":
            key_actual = column
            break

    # Locate an optional YTG column by normalized name only, mirroring the KEY
    # lookup. Older AOP sheets predate the YTG column; when it is absent it is
    # neither required nor reported as an extra, and it is not derived later.
    ytg_actual: str | None = None
    for column in actual_columns:
        if normalize_name(column) == "ytg":
            ytg_actual = column
            break

    # Resolve every required expected column; resolve_columns raises naming any
    # unmatched required column. Extras exclude both the located KEY and YTG
    # columns below so neither is treated as required or reported as extra.
    resolvable = [c for c in actual_columns if c not in (key_actual, ytg_actual)]
    mapping, extras = resolve_columns(resolvable, EXPECTED_COLUMNS)

    # Surface extra source columns as a warning and continue (they are dropped
    # from the working frame by the canonical selection below).
    if extras:
        logger.warning("Ignoring extra source column(s): %s.", extras)

    # Select and rename to canonical expected names so all downstream logic uses
    # canonical names regardless of source order. Carry the optional KEY and YTG
    # columns through under their canonical names when present; when absent they
    # are simply not selected (YTG is never derived).
    selection = {mapping[expected]: expected for expected in EXPECTED_COLUMNS}
    columns_to_keep = [mapping[expected] for expected in EXPECTED_COLUMNS]
    if key_actual is not None:
        columns_to_keep.append(key_actual)
        selection[key_actual] = "KEY"
    if ytg_actual is not None:
        columns_to_keep.append(ytg_actual)
        selection[ytg_actual] = "YTG"
    frame = frame[columns_to_keep].rename(columns=selection).copy()

    # Drop trailing/interspersed rows with no Customer; these are blank padding
    # rows and the trailing "#N/A" spill region that carry no business data.
    customer_blank = frame["Customer"].isna() | (
        frame["Customer"].astype(str).str.strip() == ""
    )
    frame = frame.loc[~customer_blank].copy()

    # Fill only the blank YTD/quarter totals (and YTG when present) from their
    # monthly components: the source omits these totals on some rows even though
    # they are definitionally the sum of their months. The fill map is the same
    # corrected per-row identity map used by validation (build_per_row_checks):
    # when YTG is present YTD fills from the non-YTG months (Jan..Apr) and YTG
    # from May..Dec; when YTG is absent YTD fills from the full year. Using the
    # shared map keeps a blank-filled total consistent with what validate_aop
    # then checks (issue #48 / WS5).
    totals_to_months = build_per_row_checks(list(frame.columns))
    frame = fill_blank_totals(frame, totals_to_months)

    # Establish KEY per the documented branches (create/trust/resolve), wired
    # exactly as normalize_le.load_source so AOP reuses the shared policy.
    frame = resolve_key(
        frame,
        key_mismatch,
        has_key_column=key_actual is not None,
        is_tty=is_tty,
        prompt=prompt,
        resolver=resolver,
    )

    # Coerce numeric columns to float BEFORE validation so the identity checks
    # operate on numbers rather than text or blanks.
    frame = coerce_numeric(frame)

    # Clean label sentinels after coercion; this does not affect the numeric
    # identity checks and gives validation a consistent label representation.
    frame = clean_label_sentinels(frame, LABEL_COLUMNS)

    # Validate per-row totals; a failure raises before any transform is applied.
    validate_aop(frame)

    # Apply the caller-supplied transform only after validation passes, so a
    # transform never masks an invalid source.
    if transform is not None:
        frame = transform(frame)

    return frame


def persist_aop(
    df: pd.DataFrame,
    db_path: str,
    table: str = "aop",
    if_exists: str = "replace",
) -> None:
    """Persist the AOP DataFrame to SQLite with lookup indexes.

    Writes the frame through the typed ``write_table`` boundary and creates a
    quoted lowercase lookup index on each of ``KEY``, ``Customer``, ``SKU #``,
    and ``Type`` (when that column is present in the frame). Index names are made
    SQL-safe by replacing space with ``_`` and ``#`` with ``num`` and
    lowercasing.

    Args:
        df: The validated AOP DataFrame to persist.
        db_path: Path to the SQLite database file.
        table: Destination table name (default ``"aop"``).
        if_exists: Behavior when the table exists (``"replace"``, ``"append"``,
            or ``"fail"``); forwarded unchanged to the write boundary.

    Returns:
        ``None``.

    Side effects:
        Opens a SQLite connection at ``db_path``, writes ``table``, creates
        lookup indexes, commits, and closes the connection.
    """
    con = sqlite3.connect(db_path)
    try:
        # Route the write through the typed pandas_io boundary so the
        # SQLAlchemy-connectable unknown member type does not surface here.
        write_table(df, table, con, if_exists=if_exists, index=False)

        # Create a quoted lookup index for each indexable column present in the
        # frame; identifiers are quoted because they cannot be parameterized and
        # the table/column names are trusted internal values.
        present_columns = set(df.columns.astype(str))
        for column in INDEX_COLUMNS:
            if column not in present_columns:
                continue
            index_name = safe_index_name(table, column)
            quoted_index = '"' + index_name.replace('"', '""') + '"'
            quoted_table = '"' + table.replace('"', '""') + '"'
            quoted_column = '"' + column.replace('"', '""') + '"'
            con.execute(
                f"CREATE INDEX IF NOT EXISTS {quoted_index} "
                f"ON {quoted_table} ({quoted_column})"
            )
        con.commit()
    finally:
        con.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: load, validate, persist, and summarize the AOP sheet.

    Args:
        argv: Optional argument vector (excluding the program name). When
            ``None``, ``argparse`` reads from ``sys.argv``.

    Returns:
        ``0`` on success; ``1`` when a column-resolution, KEY-resolution, or
        validation ``ValueError`` is raised in normal operation. A missing
        required ``--output`` causes ``argparse`` to exit with a non-zero code.
        When debug mode is active (``--debug`` or a truthy ``LOAD_AOP_DEBUG``
        environment variable), the original ``ValueError`` is re-raised with its
        full traceback instead of being mapped to exit code 1.

    Raises:
        ValueError: Re-raised with its original traceback when debug mode is
            active and ``load_aop`` raises a column-resolution, KEY-resolution,
            or validation ``ValueError``.

    Side effects:
        Configures the stdlib ``logging`` module once to emit WARNING-level
        messages, reads the workbook, writes the SQLite table, and prints the
        summary to stdout.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging once at the entry point so warnings (extra columns, KEY
    # resolution, duplicate KEYs) reach stderr without library code touching
    # global config.
    logging.basicConfig(level=logging.WARNING)

    # Map column-resolution, KEY-resolution, and validation failures to a
    # non-zero exit while letting the descriptive message reach the operator.
    try:
        df = load_aop(
            args.input, sheet=args.source_sheet, key_mismatch=args.key_mismatch
        )
    except ValueError as error:
        # Decide how to surface the validation failure. Debug mode (the
        # --debug flag or a truthy LOAD_AOP_DEBUG env var) re-raises the
        # original exception so a debugger keeps the traceback and frame for
        # diagnosis; normal operation maps the failure to a clean exit 1 with a
        # one-line message for the operator.
        debug = args.debug or _debug_env_is_truthy(os.environ.get("LOAD_AOP_DEBUG"))
        if debug:
            raise
        print(f"ERROR: {error}")
        return 1

    # Apply the snake_case rename before writing when requested; the default
    # path preserves the original headers (including the "SKU Descripiton" typo).
    # The summary is computed from the validated frame under its canonical names,
    # so the rename only affects the frame that is persisted.
    to_persist = df.rename(columns=SNAKE_CASE_RENAMES) if args.snake_case else df

    persist_aop(
        to_persist, args.output, table=args.table_name, if_exists=args.if_exists
    )
    print_summary(df, args.output, args.table_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
