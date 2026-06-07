"""Phase helpers for :class:`src.schema_loader.SchemaLoader` (Issue #43).

Purpose:
    House the schema-driven ETL phase functions so :mod:`src.schema_loader` stays
    well under the 500-line file limit. Each function is a pure DataFrame-in/
    DataFrame-out transform reproducing one step of the protected loaders'
    behavior, driven entirely by a :class:`~src.schema_model.SchemaDefinition`.

Responsibilities:
    - :func:`resolve_and_rename`: resolve the raw header to canonical names,
      rename, warn-and-drop extras, and drop blank-key padding rows.
    - :func:`collapse_by_key`: collapse duplicate-key rows per the dedup policy.
    - :func:`apply_derived_columns`: populate ``copy_from`` and ``expression``
      derived columns.
    - :func:`emit_output_columns`: emit the canonical output column set in schema
      order, determined by each column's ``in_output`` flag (inclusion), not by a
      ``drop_columns`` by-name list.

Key invariants:
    First-appearance ordering is preserved exactly like the protected loaders
    (``groupby(..., sort=False)`` and ``drop_duplicates(keep="first")``). The
    reused ETL leaf helpers are never re-implemented here.

Side effects:
    None. These functions copy before mutating and never perform I/O.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import pandas as pd

from src.etl_columns import normalize_name, resolve_columns

if TYPE_CHECKING:
    from src.schema_formula import FormulaEvaluator
    from src.schema_model import DedupPolicy, SchemaDefinition

logger = logging.getLogger(__name__)


def _output_column_order(schema: SchemaDefinition) -> list[str]:
    """Return the canonical output column order for ``schema``.

    Output membership is determined by inclusion: a declared column appears in the
    output only when its ``in_output`` flag is ``True`` (plus the ``KEY`` and any
    derived columns, below). This replaces the former ``drop_columns`` by-name
    exclusion. The schema's declared ``columns`` order is preserved, and any
    ``derived_columns`` whose name is not already an output column is inserted in
    its declared position relative to the columns. Derived columns that share a
    name with a declared column (the LE ``Super Category`` copy_from quirk) keep
    the declared column's position.

    Args:
        schema: The active schema.

    Returns:
        The ordered list of canonical output column names.
    """
    # Start from declared columns marked for output (in_output=True), preserving
    # schema order. Columns with in_output=False (the LE YTD/YTG discriminator)
    # are carried through processing but excluded here by omission.
    order = [c.canonical_name for c in schema.columns if c.in_output]

    # Insert each derived column that is not already an output column. The LE
    # YTG derived column is not a declared source column, so it is appended in
    # its derived-list position relative to the surviving columns; copy_from
    # quirks (Super Category) reuse an existing declared position.
    existing = set(order)
    for derived in schema.derived_columns:
        if derived.name in existing:
            continue
        order = _insert_derived(order, derived.name, schema)
        existing.add(derived.name)
    return order


def _insert_derived(
    order: list[str],
    name: str,
    schema: SchemaDefinition,
) -> list[str]:
    """Insert a derived column ``name`` into ``order`` at its schema position.

    The LE derived ``YTG`` is declared (in the bundled schema's ``columns`` the
    surviving order places it after ``Q4`` and before ``Super Category``). The
    bundled LE schema also lists ``YTG`` among its derived columns; its intended
    output position is immediately after the last summed quarter total. This
    helper places a not-yet-present derived column directly before the first
    declared derived-or-copy target so the emitted order matches
    ``normalize_le.TARGET_COLUMNS`` exactly.

    Args:
        order: The current output order (declared columns minus drops).
        name: The derived column name to insert.
        schema: The active schema (used to locate the anchor position).

    Returns:
        A new list with ``name`` inserted at its intended position.
    """
    # Anchor the derived column before the first copy_from derived target that is
    # already in the order (LE: "Super Category"); if none, append at the end.
    anchor_names = [
        d.copy_from
        for d in schema.derived_columns
        if d.copy_from is not None and d.copy_from in order
    ]
    # Prefer the position of the copy_from target's output slot; LE places YTG
    # right before "Super Category".
    copy_targets_in_order = [
        d.name for d in schema.derived_columns if d.copy_from is not None
    ]
    insert_before = None
    for candidate in copy_targets_in_order:
        if candidate in order:
            insert_before = candidate
            break
    if insert_before is None and anchor_names:
        insert_before = anchor_names[0]
    new_order = list(order)
    if insert_before is not None and insert_before in new_order:
        new_order.insert(new_order.index(insert_before), name)
    else:
        new_order.append(name)
    return new_order


def resolve_and_rename(raw: pd.DataFrame, schema: SchemaDefinition) -> pd.DataFrame:
    """Resolve the raw header to canonical names and drop blank-key rows.

    Reproduces the protected loaders' read-time cleanup: an optional ``KEY`` and
    optional discriminator/``YTG`` columns are located by normalized name (no
    fuzzy match); the required columns are resolved via :func:`resolve_columns`;
    extras are warned and dropped; the frame is renamed to canonical names; and
    rows whose key dimension (``Customer``) is blank are dropped.

    Args:
        raw: The raw source DataFrame read at the schema's header row.
        schema: The active schema describing the canonical columns.

    Returns:
        A copy of the relevant columns renamed to canonical names with blank-key
        padding rows removed. The surviving rows keep their original index, so a
        ``dedup`` mode of ``none`` preserves the same index as the protected AOP
        loader.

    Raises:
        ValueError: When a required column cannot be resolved (propagated from
            :func:`resolve_columns`).
    """
    actual_columns = list(raw.columns.astype(str))

    # Columns resolved by name only (not fuzzy) and not treated as required:
    # KEY plus any optional column (the AOP optional YTG; and the LE discriminator
    # YTD/YTG, which is now required=false and located by name, carried through for
    # the dedup collapse, and excluded from output by in_output=false).
    by_name_optional = _by_name_optional_columns(schema)

    # Map each by-name-optional canonical name to its actual source column (if
    # present) so it can be carried through and renamed without being required.
    located: dict[str, str] = {}
    for canonical in by_name_optional:
        target_norm = normalize_name(canonical)
        for column in actual_columns:
            if normalize_name(column) == target_norm:
                located[canonical] = column
                break

    by_name_set = set(by_name_optional)
    # The required expected columns are the declared columns that are required
    # and not handled by name above.
    required_expected = [
        c.canonical_name
        for c in schema.columns
        if c.required and c.canonical_name not in by_name_set
    ]

    # Resolve required columns against the actual columns, excluding the located
    # by-name columns so they are neither required nor reported as extras.
    located_actuals = set(located.values())
    resolvable = [c for c in actual_columns if c not in located_actuals]
    mapping, extras = resolve_columns(resolvable, required_expected)

    # Surface extra source columns as a warning and continue; they are dropped by
    # the canonical selection below.
    if extras:
        logger.warning("Ignoring extra source column(s): %s.", extras)

    # Build the select+rename plan: required columns first (schema order), then
    # the located by-name optional columns under their canonical names.
    selection = {mapping[expected]: expected for expected in required_expected}
    columns_to_keep = [mapping[expected] for expected in required_expected]
    for canonical, actual in located.items():
        columns_to_keep.append(actual)
        selection[actual] = canonical

    frame = raw[columns_to_keep].rename(columns=selection).copy()

    # Drop trailing/interspersed rows with no Customer; these are blank padding
    # rows that carry no business data. Customer is the leading key dimension in
    # both bundled schemas.
    customer_blank = frame["Customer"].isna() | (
        frame["Customer"].astype(str).str.strip() == ""
    )
    return frame.loc[~customer_blank].copy()


def _by_name_optional_columns(schema: SchemaDefinition) -> list[str]:
    """Return canonical names resolved by name only, KEY first then optionals.

    These are ``KEY`` (always optional/by-name) followed by any declared column
    marked ``required=False`` in schema order. This includes the AOP optional
    ``YTG`` and, after the bundled-schema change, the LE discriminator
    ``YTD/YTG`` (now ``required=false, in_output=false``): it is located by name
    (no fuzzy, no raise on absence), carried through ``resolve_and_rename`` and
    ``collapse_by_key`` as the dedup discriminator, and excluded from the output
    only at emit by its ``in_output=false`` flag. The order is deterministic
    (KEY first), matching the protected loaders' ``if key ... if ytg ...`` append
    sequence.

    Args:
        schema: The active schema.

    Returns:
        The ordered list of canonical names to locate by normalized name only.
    """
    by_name: list[str] = ["KEY"]
    # Optional declared columns are located by name so an absent optional column
    # (older AOP sheets predate YTG) is neither required nor reported as extra.
    for column in schema.columns:
        if not column.required and column.canonical_name not in by_name:
            by_name.append(column.canonical_name)
    return by_name


def collapse_by_key(frame: pd.DataFrame, schema: SchemaDefinition) -> pd.DataFrame:
    """Collapse duplicate-key rows per the schema's dedup policy.

    For ``mode == "none"`` the frame is returned unchanged (rows preserved in
    first-appearance order with their original index, matching the AOP loader).
    For ``mode == "collapse"`` rows sharing ``KEY`` are merged: dimension and
    non-aggregated columns are taken from the first row per key
    (``drop_duplicates(keep="first")``); ``additive`` measures are summed with
    ``groupby(..., sort=False).sum()`` (NaN treated as 0 via ``min_count=0``);
    ``select_from`` measures take the value from the row whose discriminator is
    in ``select_values``. The output index is reset to a default RangeIndex,
    matching ``normalize_le.normalize``.

    Args:
        frame: The keyed working frame.
        schema: The active schema describing the dedup policy and measures.

    Returns:
        The collapsed (or unchanged) frame. For ``collapse`` the result has one
        row per unique KEY in first-appearance order with a fresh RangeIndex.
    """
    policy = schema.dedup
    # mode "none" preserves every row and its original index (AOP).
    if policy.mode == "none":
        return frame

    # First row per KEY supplies all non-aggregated columns (dimensions, the
    # discriminator, and any copy_from source); sort is not needed because
    # drop_duplicates(keep="first") preserves first-appearance order.
    first_rows = frame.drop_duplicates(subset="KEY", keep="first").set_index("KEY")

    # Partition measures into additive (summed) and select_from (picked) per the
    # declared aggregation rules.
    aggregations = {agg.measure: agg for agg in policy.measure_aggregations}
    additive = [m for m, a in aggregations.items() if a.mode == "additive"]

    # Sum additive measures across rows sharing a KEY; sort=False preserves
    # first-appearance order and the default min_count=0 fills all-NaN as 0.
    sums = frame.groupby("KEY", sort=False)[additive].sum() if additive else None

    output = pd.DataFrame(index=first_rows.index)
    output.index.name = "KEY"

    # Carry every non-aggregated, non-derived column from the first row per key.
    # Derived columns are populated in a later phase, so they are skipped here.
    derived_names = {d.name for d in schema.derived_columns}
    aggregated_names = set(aggregations)
    # Walk declared columns in schema order so the intermediate frame keeps a
    # stable column order before the final emit reorders it.
    for column in schema.columns:
        name = column.canonical_name
        if name == "KEY" or name in aggregated_names or name in derived_names:
            continue
        output[name] = first_rows[name]

    # Carry summed additive measures.
    if sums is not None:
        for measure in additive:
            output[measure] = sums[measure]

    # Carry select_from measures: pick the value from the row whose discriminator
    # matches one of the declared select_values.
    _apply_select_from(output, frame, policy, first_rows.index)

    return output.reset_index()


def _apply_select_from(
    output: pd.DataFrame,
    frame: pd.DataFrame,
    policy: DedupPolicy,
    key_index: pd.Index,
) -> None:
    """Populate ``select_from`` measures into ``output`` keyed by KEY.

    Args:
        output: The collapsing output frame indexed by KEY (mutated in place).
        frame: The full keyed working frame.
        policy: The dedup policy (carries discriminator column and aggregations).
        key_index: The KEY index of ``output`` (first-appearance order).

    Returns:
        ``None``. ``output`` is mutated in place.
    """
    select_measures = [
        agg for agg in policy.measure_aggregations if agg.mode == "select_from"
    ]
    if not select_measures:
        return

    discriminator = policy.discriminator_column
    # A select_from policy always declares a discriminator (enforced by
    # DedupPolicy.__post_init__); guard for the type-checker and fail fast if not.
    if discriminator is None:
        raise ValueError("select_from dedup requires a discriminator column")

    # For each select_from measure, choose, per KEY, the value from the first row
    # whose discriminator is one of the declared select_values.
    for agg in select_measures:
        selected = frame[frame[discriminator].isin(agg.select_values)]
        chosen = selected.drop_duplicates(subset="KEY", keep="first").set_index("KEY")
        output[agg.measure] = chosen[agg.measure].reindex(key_index)


def apply_derived_columns(
    frame: pd.DataFrame,
    schema: SchemaDefinition,
    evaluator: FormulaEvaluator,
) -> pd.DataFrame:
    """Populate derived columns via ``copy_from`` or formula ``expression``.

    For each :class:`~src.schema_model.DerivedColumnSpec`: a ``copy_from`` spec
    copies the named source column's values directly (the LE
    ``Super Category <- PPG`` quirk); an ``expression`` spec evaluates the formula
    vectorized against the frame's column Series via the :class:`FormulaEvaluator`,
    including ratio recompute via ``safe_div``. Vectorized evaluation lets pandas'
    native dtype propagation produce results identical to the protected loaders'
    derived columns (for example an integer ``YTG`` from integer month columns).

    Args:
        frame: The aggregated (or row-preserved) working frame.
        schema: The active schema describing the derived columns.
        evaluator: The formula evaluator used for ``expression`` specs.

    Returns:
        The frame with every derived column populated.

    Raises:
        FormulaError: When an expression is invalid or fails to evaluate
            (propagated from the evaluator).
    """
    known_columns = list(frame.columns.astype(str))
    # Populate each derived column in declared order so a later derived column may
    # reference an earlier one if a schema declares that dependency.
    for derived in schema.derived_columns:
        if derived.copy_from is not None:
            # copy_from quirk: take the named column's values verbatim.
            frame[derived.name] = frame[derived.copy_from]
            continue
        # expression: validate against the current known columns, then evaluate
        # vectorized so the result Series matches pandas' native dtype exactly.
        evaluator.validate(derived.expression, known_columns)
        frame[derived.name] = _evaluate_vectorized(frame, derived.expression, evaluator)
    return frame


def _evaluate_vectorized(
    frame: pd.DataFrame,
    expression: str,
    evaluator: FormulaEvaluator,
) -> pd.Series[float]:
    """Evaluate ``expression`` once against the frame's column Series.

    Builds a context mapping each exact column name to that column's Series and
    evaluates the expression a single time. The whitelisted helpers (``sum``,
    ``safe_div``) are Series-aware, so the result is an element-wise Series whose
    dtype follows pandas' native arithmetic, matching the protected loaders. A
    scalar result (for example a constant expression) is broadcast to a Series
    aligned to the frame's index so the derived column has one value per row.

    Args:
        frame: The frame whose column Series supply the evaluation context.
        expression: The validated formula expression.
        evaluator: The formula evaluator.

    Returns:
        A ``pd.Series`` aligned to ``frame``'s index. Deterministic: no
        wall-clock or randomness is involved.
    """
    # Map each exact column name to its Series so the expression evaluates
    # element-wise across all rows in one pass (deterministic, vectorized).
    context: dict[str, object] = {str(name): frame[name] for name in frame.columns}
    result = evaluator.evaluate(expression, context)
    # A Series result is returned as-is (preserving its native dtype); a scalar
    # result is broadcast across the frame's index so the column is well-formed.
    # Both branches are cast to a float Series: asteval hands back untyped values,
    # and the derived columns this loader produces are numeric.
    if isinstance(result, pd.Series):
        return cast("pd.Series[float]", result)
    return pd.Series(cast("float", result), index=frame.index)


def emit_output_columns(
    frame: pd.DataFrame,
    schema: SchemaDefinition,
) -> pd.DataFrame:
    """Emit the canonical output columns determined by ``in_output`` inclusion.

    Output membership is determined by each column's ``in_output`` flag, not by a
    ``drop_columns`` by-name list. The output column order is mode-dependent to
    match the protected loaders exactly. A collapsing schema (LE, ``collapse`` or
    ``aggregate`` mode) rebuilds the canonical declared order from the
    ``in_output`` columns with the derived ``YTG`` inserted in its declared
    position (matching ``normalize_le.TARGET_COLUMNS``). A ``none`` schema (AOP)
    preserves the working frame's natural column order (resolution order with the
    created ``KEY`` appended last), excluding any frame column whose declared spec
    has ``in_output=False``, because ``load_aop`` returns the validated frame
    without reordering.

    Args:
        frame: The fully transformed working frame.
        schema: The active schema describing column output-membership, dedup mode,
            and order.

    Returns:
        A DataFrame containing exactly the canonical output columns. The row index
        is preserved from ``frame`` (the collapse phase reset it for LE; the AOP
        path keeps its filtered index).
    """
    # Decide the output column order by dedup mode: the collapsing modes
    # (collapse/aggregate) rebuild the canonical declared order; the none path
    # preserves the frame's natural order. Aggregate is the renamed collapse mode
    # (Decision 1) and shares the same canonical-ordering behavior.
    if schema.dedup.mode in {"collapse", "aggregate"}:
        order = _output_column_order(schema)
    else:
        # Build the set of declared columns excluded from output (in_output=False)
        # so the none path filters by inclusion like the collapsing path. A column
        # not declared in the schema (none today) is kept by default.
        excluded = {c.canonical_name for c in schema.columns if not c.in_output}
        # Preserve the frame's existing column order, omitting only the excluded
        # columns, so the AOP output matches load_aop's un-reordered validated
        # frame.
        order = [str(name) for name in frame.columns if str(name) not in excluded]
    # Select exactly the output columns; any non-output column is removed by
    # omission.
    return frame[order]
