"""CLI orchestration for the LE-versus-AOP gross-to-net decomposition pipeline.

This module provides the ``mix-pipeline`` CLI entry point. ``main`` orchestrates
only: it reuses the existing loaders (:mod:`src.normalize_le`, :mod:`src.load_aop`,
:mod:`src.load_skulu`) to import the ``LE``, ``aop``, and ``sku_lu`` tables, reads
those tables back through :mod:`src.pandas_io`, runs the pure transform functions
in topological order (evaluation steps 1-19 plus the issue #15 ``nrr_summary``
final summary step), and persists each of the twenty derived tables. It contains
no transform logic; every transform lives in the pure ``src.mix_*`` modules and
every read/write routes through ``src.pandas_io``.

The ``mix_rollup_4`` scalar is persisted as a single-row, single-column table.

Boundaries:
    - Imports reuse the existing loader read/write boundaries.
    - Transform-table reads/writes route through ``src.pandas_io``.
    - ``main`` is the only function here that performs I/O.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from typing import TYPE_CHECKING

from src import load_aop, load_skulu, normalize_le
from src.mix_lookups import (
    build_aop_norm,
    build_aop_vs_le,
    build_customer_lu,
    build_le_norm,
    build_mix_base,
)
from src.mix_pipeline_run import run_transforms
from src.mix_transforms import pivot_aop, pivot_le
from src.pandas_io import read_table, write_table

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["build_parser", "main"]

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the mix-pipeline CLI.

    Returns:
        A configured ``ArgumentParser`` with the required ``--input`` and
        ``--output`` options plus the ``--le-sheet``, ``--aop-sheet``,
        ``--skulu-input``, and ``--skulu-sheet`` options and their defaults.
    """
    parser = argparse.ArgumentParser(
        prog="mix-pipeline",
        description=(
            "Run the LE-vs-AOP gross-to-net decomposition end-to-end from one "
            "workbook into one SQLite database."
        ),
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the source .xlsx workbook (supplies AOP1 and LE-8 + 4).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the SQLite database file to write (required).",
    )
    parser.add_argument(
        "--le-sheet",
        default="LE-8 + 4",
        help='LE source sheet name (default: "LE-8 + 4").',
    )
    parser.add_argument(
        "--aop-sheet",
        default="AOP1",
        help='AOP source sheet name (default: "AOP1").',
    )
    parser.add_argument(
        "--skulu-input",
        default=None,
        help="Path to the SKU_LU workbook (default: same as --input).",
    )
    parser.add_argument(
        "--skulu-sheet",
        default="SKU_LU",
        help='SKU lookup sheet name (default: "SKU_LU").',
    )
    return parser


def _import_sources(args: argparse.Namespace) -> None:
    """Import the LE, AOP, and SKU_LU sources via the reused loaders.

    Args:
        args: The parsed CLI arguments carrying the input/output paths and the
            sheet names.

    Returns:
        ``None``.

    Raises:
        ValueError: Propagated from a reused loader when a column, KEY, or
            validation check fails.

    Side effects:
        Reads the workbook sheets and writes the ``LE``, ``aop``, and ``sku_lu``
        tables into the output database.
    """
    # Reuse normalize_le to import and persist the LE table.
    le_source = normalize_le.load_source(args.input, args.le_sheet)
    le_output = normalize_le.normalize(le_source)
    normalize_le.validate_tieouts(le_source, le_output)
    normalize_le.write_sqlite(le_output, args.output, "LE")

    # Reuse load_aop to import and persist the aop table.
    aop_frame = load_aop.load_aop(args.input, sheet=args.aop_sheet)
    load_aop.persist_aop(aop_frame, args.output, table="aop")

    # Reuse load_skulu to import and persist the sku_lu table; the SKU_LU sheet
    # defaults to the same workbook as the AOP/LE sheets.
    skulu_input = args.skulu_input if args.skulu_input is not None else args.input
    sku_lu = load_skulu.load_skulu(skulu_input, sheet=args.skulu_sheet)
    load_skulu.persist_skulu(sku_lu, args.output, table="sku_lu")


def _persist_all(con: sqlite3.Connection, tables: dict[str, pd.DataFrame]) -> None:
    """Persist every derived table through the pandas_io write boundary.

    Args:
        con: An open SQLite connection.
        tables: A mapping of destination table name to the DataFrame to persist.

    Returns:
        ``None``.

    Side effects:
        Writes each table with ``if_exists="replace"`` semantics.
    """
    # Walk the derived tables in insertion order and replace each on the database.
    for name, frame in tables.items():
        write_table(frame, name, con, if_exists="replace", index=False)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: import the sources, run the transforms, and persist them.

    Orchestrates only. Imports the LE, AOP, and SKU_LU sources via the reused
    loaders, reads the import tables back through ``src.pandas_io``, runs the
    transform pipeline in topological order, and persists each derived table
    (including ``mix_rollup_4`` as a single-row table) into the output database.

    Args:
        argv: Optional argument vector (excluding the program name). When
            ``None``, ``argparse`` reads from ``sys.argv``.

    Returns:
        ``0`` on success; ``1`` when a column-resolution, KEY-resolution, or
        validation ``ValueError`` is raised by a reused loader. A missing
        required ``--input`` or ``--output`` causes ``argparse`` to exit
        non-zero.

    Side effects:
        Configures ``logging`` once, reads the workbook, writes the import and
        derived SQLite tables, and prints a stdout summary of tables written.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging once at the entry point so loader warnings reach stderr.
    logging.basicConfig(level=logging.WARNING)

    # Map loader column/KEY/validation failures to a clean non-zero exit with a
    # one-line operator message; transform logic does not raise ValueError here.
    try:
        _import_sources(args)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 1

    # Read the import tables back and run the transform pipeline, then persist
    # every derived table on a single connection.
    con = sqlite3.connect(args.output)
    try:
        le_raw = read_table(con, "LE")
        aop_raw = read_table(con, "aop")
        sku_lu = read_table(con, "sku_lu")

        # Steps 1-2: long-to-wide source pivots.
        le_wide = pivot_le(le_raw)
        aop_wide = pivot_aop(aop_raw)

        # Steps 3-8: lookups, normalization, comparison, and the mix base.
        customer_lu = build_customer_lu(aop_raw)
        aop_norm = build_aop_norm(aop_wide)
        le_norm = build_le_norm(le_wide)
        aop_vs_le = build_aop_vs_le(aop_norm, le_norm)
        mix_base = build_mix_base(aop_vs_le, sku_lu)

        # Steps 9-19: rate impacts, the rollup chain, the detail, and Q1.
        derived = run_transforms(aop_vs_le, sku_lu, mix_base, le_raw)

        # Assemble the full set of derived tables in evaluation order; the
        # intermediate pivots/lookups are persisted alongside the rollups.
        tables: dict[str, pd.DataFrame] = {
            "le_wide": le_wide,
            "aop_wide": aop_wide,
            "customer_lu": customer_lu,
            "aop_norm": aop_norm,
            "le_norm": le_norm,
            "aop_vs_le": aop_vs_le,
            "mix_base": mix_base,
            **derived,
        }
        _persist_all(con, tables)
        con.commit()

        # The two import tables plus the twenty derived tables are now present.
        _print_summary(con, tables)
    finally:
        con.close()
    return 0


def _print_summary(
    con: sqlite3.Connection,
    derived_tables: dict[str, pd.DataFrame],
) -> None:
    """Print a summary of the persisted tables and their row counts to stdout.

    Args:
        con: The open SQLite connection (unused for the count, retained for a
            consistent boundary signature).
        derived_tables: The derived tables that were written.

    Returns:
        ``None``. Emits the summary to stdout (CLI tool output, not logging).
    """
    print("mix-pipeline complete. Tables written:")
    print("  LE (import)")
    print("  aop (import)")
    # Report each derived table and its row count so the operator can spot-check.
    for name, frame in derived_tables.items():
        print(f"  {name}: {len(frame)} rows")


if __name__ == "__main__":
    raise SystemExit(main())
