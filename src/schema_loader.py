"""Configurable, schema-driven ETL loader (Issue #43, Feature C).

Purpose:
    Provide :class:`SchemaLoader`, a parallel additive load path that reproduces
    the as-built behavior of the protected loaders (:mod:`src.normalize_le` and
    :mod:`src.load_aop`) entirely from a :class:`~src.schema_model.SchemaDefinition`
    rather than from hand-written, source-specific code. Feature D wires this
    loader into the pipeline later; this feature delivers the loader and proves
    byte-for-equivalent parity with the protected loaders.

Responsibilities:
    - Resolve a raw header to the schema's canonical column names, rename, and
      drop blank-key padding rows.
    - Establish the business key, fill blank totals, coerce numeric measures, and
      clean label sentinels, reusing the shared ETL leaf helpers so parity is
      exact.
    - Collapse duplicate-key rows per the schema's dedup policy (or preserve
      rows when the policy is ``none``).
    - Compute derived columns (``copy_from`` quirks and formula expressions),
      drop the declared drop-columns, and emit the canonical output columns in
      schema order.

    It does NOT read or write any file, touch the network, or apply any caller
    transform; it is a pure DataFrame-in/DataFrame-out transform.

Usage:
    Construct with a :class:`SchemaDefinition` (optionally injecting a
    :class:`~src.schema_formula.FormulaEvaluator`), then call :meth:`load` with a
    raw DataFrame read at the schema's header row. The same schema may be passed
    again to :meth:`load` to override the construction-time schema.

High-level flow:
    ``load`` runs, in order: resolve -> blank-drop -> fill -> key -> coerce ->
    sentinel-clean -> dedup -> derived -> drop -> emit.

Key invariants:
    - First-appearance ordering is preserved exactly like the protected loaders
      (``groupby(..., sort=False)`` and ``drop_duplicates(keep="first")``).
    - The reused helpers (``resolve_columns``, ``resolve_key``,
      ``fill_blank_totals``, ``coerce_numeric``, ``clean_label_sentinels``) are
      never re-implemented, so the configurable path and the protected path
      compute identical results.

Side effects:
    None. The loader performs no I/O and does not mutate its input frame (it
    copies before mutating).
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from src._load_aop_helpers import clean_label_sentinels, coerce_numeric
from src._schema_loader_helpers import (
    apply_derived_columns,
    collapse_by_key,
    emit_output_columns,
    resolve_and_rename,
)
from src.etl_key import resolve_key
from src.etl_totals import fill_blank_totals
from src.schema_formula import FormulaEvaluator

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from src.schema_model import SchemaDefinition


class SchemaLoader:
    """Schema-driven ETL loader reproducing the protected loaders' behavior.

    Purpose:
        Transform a raw source DataFrame into the canonical output frame defined
        by a :class:`~src.schema_model.SchemaDefinition`, reproducing the as-built
        LE and AOP loaders exactly while being driven entirely by schema data.

    Responsibilities:
        Run the resolve -> key -> fill -> coerce -> dedup -> derive -> drop ->
        emit pipeline. It does not read/write files, touch the network, or apply
        any caller-supplied transform.

    Usage:
        ``loader = SchemaLoader(schema)`` then ``out = loader.load(raw_frame)``.
        A per-call ``schema`` argument overrides the construction-time schema.

    High-level flow:
        See the module docstring; each phase is a private method or a helper in
        :mod:`src._schema_loader_helpers`.

    Key invariants:
        - First-appearance ordering is preserved exactly like the protected
          loaders.
        - The input frame is never mutated; the loader copies before mutating.

    Side effects:
        None.

    Attributes:
        schema: The default :class:`SchemaDefinition` used when :meth:`load` is
            called without an explicit schema.
        formula_evaluator: The :class:`FormulaEvaluator` used to evaluate derived
            column expressions.
    """

    def __init__(
        self,
        schema: SchemaDefinition,
        *,
        formula_evaluator: FormulaEvaluator | None = None,
    ) -> None:
        """Initialize the loader with a default schema and a formula evaluator.

        Args:
            schema: The default schema to apply when :meth:`load` is called
                without an explicit ``schema`` argument.
            formula_evaluator: The evaluator for derived-column expressions.
                When ``None``, a default :class:`FormulaEvaluator` is created.
        """
        self.schema = schema
        self.formula_evaluator = formula_evaluator or FormulaEvaluator()

    def load(
        self,
        raw: pd.DataFrame,
        schema: SchemaDefinition | None = None,
        *,
        resolver: Callable[[list[tuple[str, str]]], str] | None = None,
        is_tty: Callable[[], bool] = sys.stdin.isatty,
        prompt: Callable[[str], str] = input,
    ) -> pd.DataFrame:
        """Transform a raw source frame into the schema's canonical output frame.

        Args:
            raw: The raw source DataFrame as read at the schema's header row
                (for example via ``read_excel_sheet(buffer, sheet, header=2)``).
                The input is not mutated.
            schema: An optional schema overriding the construction-time schema for
                this call.
            resolver: Optional example-aware KEY-mismatch resolver forwarded to
                :func:`src.etl_key.resolve_key`. It is invoked ONLY on a genuine
                ``KEY`` divergence (an existing source ``KEY`` column whose values
                differ from the rebuilt pattern), receiving up to three
                ``(existing, rebuilt)`` example pairs and returning the resolved
                action (``"trust"`` or ``"overwrite"``). When ``None`` (the
                default), divergence is resolved via the ``"prompt"`` policy using
                ``is_tty``/``prompt`` exactly as before; the GUI path supplies a
                resolver so no stdin prompt is reached.
            is_tty: Zero-arg callable returning whether stdin is interactive,
                forwarded to :func:`resolve_key`. Defaults to ``sys.stdin.isatty``.
                Injectable so non-interactive callers (the GUI) can report a
                non-TTY environment.
            prompt: Callable used to ask the user on the interactive prompt path,
                forwarded to :func:`resolve_key`. Defaults to the built-in
                ``input``. Injectable so non-interactive callers can supply a
                stdin-free prompt that never blocks.

        Returns:
            A DataFrame with exactly the schema's canonical output columns in
            schema order, with rows collapsed/preserved per the dedup policy,
            derived columns populated, and drop-columns removed.

        Raises:
            ValueError: When a required column cannot be resolved, or when key
                resolution fails (propagated from the reused ETL helpers).
            FormulaError: When a derived-column expression is invalid or fails to
                evaluate (propagated from the formula evaluator).
        """
        active = schema or self.schema

        # Resolve the raw header to canonical names, rename, and drop blank-key
        # padding rows; this reproduces the protected loaders' read-time cleanup.
        frame = resolve_and_rename(raw, active)

        # Fill blank totals from the schema's fill rules before key resolution,
        # mirroring the protected loaders' ordering. A fill rule whose total
        # column is absent from the frame is skipped, matching load_aop's
        # conditional inclusion of the optional YTG fill (older AOP sheets predate
        # the YTG column, so it is neither present nor filled).
        totals_to_months = {
            rule.total: list(rule.components)
            for rule in active.fill_rules
            if rule.total in frame.columns
        }
        if totals_to_months:
            frame = fill_blank_totals(frame, totals_to_months)

        # Establish the business KEY. The fixtures and bundled schemas drive a
        # source without a pre-existing KEY column, so the loader creates it from
        # the rebuilt pattern; a present KEY is reconciled per the default policy.
        has_key = "KEY" in frame.columns
        frame = resolve_key(
            frame,
            "prompt",
            has_key_column=has_key,
            is_tty=is_tty,
            prompt=prompt,
            resolver=resolver,
        )

        # Coerce numeric measures and clean label sentinels only when the schema
        # marks columns for it (the AOP path); the LE path marks none, so these
        # are no-ops there, preserving each loader's distinct behavior.
        frame = self._coerce_and_clean(frame, active)

        # Collapse duplicate-key rows (AOP: none -> preserve; LE: collapse).
        frame = collapse_by_key(frame, active)

        # Populate derived columns (LE: copy_from quirk + YTG expression).
        frame = apply_derived_columns(frame, active, self.formula_evaluator)

        # Drop declared drop-columns and emit the canonical output columns.
        return emit_output_columns(frame, active)

    def _coerce_and_clean(
        self,
        frame: pd.DataFrame,
        schema: SchemaDefinition,
    ) -> pd.DataFrame:
        """Coerce numeric measures and clean label sentinels per the schema.

        Reuses the AOP helpers ``coerce_numeric`` and ``clean_label_sentinels``
        so the configurable path matches the protected AOP loader exactly. The
        coercion runs when any column is marked ``numeric``; sentinel cleaning
        runs for the columns marked ``sentinel_clean``. The LE schema marks no
        column for either, so for LE this method returns the frame unchanged.

        Args:
            frame: The keyed, fill-completed working frame.
            schema: The active schema describing numeric/sentinel-clean columns.

        Returns:
            The frame with numeric coercion and sentinel cleaning applied as the
            schema directs.
        """
        # coerce_numeric uses the AOP NUMERIC_COLS internally and only touches
        # columns present in the frame, so it is safe to call whenever the schema
        # declares numeric columns; for LE (no numeric flags) it is skipped.
        numeric_columns = [c.canonical_name for c in schema.columns if c.numeric]
        if numeric_columns:
            frame = coerce_numeric(frame)

        # Clean sentinels in exactly the columns the schema flags (AOP label
        # columns); LE flags none, so this is skipped there.
        sentinel_columns = [
            c.canonical_name for c in schema.columns if c.sentinel_clean
        ]
        if sentinel_columns:
            frame = clean_label_sentinels(frame, sentinel_columns)

        return frame
