"""Unit tests for :class:`ColumnsTabPresenter` (Decision 4/6).

These tests exercise the Columns-tab presenter with a fake view and a shared
:class:`SchemaBuilderState`, with no ``QApplication`` and no I/O. They verify
fuzzy pre-population, alias persistence, consumed-column exclusion, the re-match
guard, manual reassignment/clearing, and the dtype-check orchestration against the
masked preview slice. Every fixture value is synthetic/masked.
"""

from __future__ import annotations

from src.gui.presenters._columns_tab_presenter import ColumnsTabPresenter
from src.gui.presenters._schema_builder_state import PreviewSlice, SchemaBuilderState


class FakeColumnsTabView:
    """Records the calls the Columns-tab presenter makes.

    Attributes:
        pools: Each ``set_source_pool`` argument, in order.
        rows: Each ``set_rows`` argument, in order.
        assignments: Each ``set_assignment`` call as ``(canonical, source)``.
        dtype_indicators: Each ``set_dtype_indicator`` call as
            ``(canonical, coercible, failing_example)``.
        value_displays: Each ``set_value_display`` call as ``(canonical, value)``.
    """

    def __init__(self) -> None:
        """Initialize empty call records."""
        self.pools: list[list[str]] = []
        self.rows: list[list[tuple[str, str, str | None]]] = []
        self.assignments: list[tuple[str, str | None]] = []
        self.dtype_indicators: list[tuple[str, bool, str | None]] = []
        self.value_displays: list[tuple[str, str]] = []

    def assign_column(self, source_column: str, target_canonical: str) -> None:
        """No-op assignment seam (the widget calls this; the presenter routes it)."""
        del source_column, target_canonical

    def set_source_pool(self, columns: list[str]) -> None:
        """Record a source-pool render call."""
        self.pools.append(list(columns))

    def set_rows(self, rows: list[tuple[str, str, str | None]]) -> None:
        """Record a rows render call."""
        self.rows.append(list(rows))

    def set_assignment(self, target_canonical: str, source_column: str | None) -> None:
        """Record an assignment render call."""
        self.assignments.append((target_canonical, source_column))

    def set_dtype_indicator(
        self, target_canonical: str, coercible: bool, failing_example: str | None
    ) -> None:
        """Record a dtype-indicator render call."""
        self.dtype_indicators.append((target_canonical, coercible, failing_example))

    def set_value_display(self, target_canonical: str, value: str) -> None:
        """Record a value-display render call (AC-6)."""
        self.value_displays.append((target_canonical, value))


def _state_with_pool() -> SchemaBuilderState:
    """Return a state with two canonical columns and a fuzzy-matchable pool.

    Returns:
        A :class:`SchemaBuilderState` whose source pool contains near-matches of
        the canonical column names plus an extra unmatched column.
    """
    return SchemaBuilderState(
        columns=[
            ("Customer", "dimension", True, True, ()),
            ("Sales", "measure", True, True, ()),
        ],
        column_dtypes={"Customer": "string", "Sales": "float"},
        source_columns=["customer", "sales", "extra_col"],
    )


def test_prepopulate_binds_best_fuzzy_match() -> None:
    """prepopulate matches each row to its closest source column."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_pool()
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: each canonical bound to its near-name source.
    assert state.consumed_columns == {"Customer": "customer", "Sales": "sales"}


def test_prepopulate_persists_alias() -> None:
    """A matched source column is persisted onto the column's aliases."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_pool()
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: the Customer row's aliases now include its matched source.
    customer_row = next(row for row in state.columns if row[0] == "Customer")
    assert "customer" in customer_row[4]


def test_consumed_column_excluded_from_pool() -> None:
    """A consumed source column is removed from the pool."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_pool()
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: only the unmatched extra column remains in the pool.
    assert state.source_columns == ["extra_col"]


def test_consumed_column_cannot_match_second_row() -> None:
    """A source already consumed by one row is unavailable to another."""
    # Arrange: two canonical rows that both fuzzily prefer the same source.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[
            ("Amount", "measure", True, True, ()),
            ("Amount Total", "measure", True, True, ()),
        ],
        column_dtypes={"Amount": "float", "Amount Total": "float"},
        source_columns=["amount"],
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: only the first row claimed the single source; the second is unbound.
    assert state.consumed_columns.get("Amount") == "amount"
    assert "Amount Total" not in state.consumed_columns


def test_manual_assign_releases_prior_target_source() -> None:
    """Reassigning a row returns its previous source to the pool."""
    # Arrange: pre-populate, then reassign Customer to a different source.
    view = FakeColumnsTabView()
    state = _state_with_pool()
    presenter = ColumnsTabPresenter(view, state)
    presenter.prepopulate()

    # Act: drop the leftover 'extra_col' onto Customer.
    presenter.assign_column("extra_col", "Customer")

    # Assert: Customer now holds extra_col and the old 'customer' is back in pool.
    assert state.consumed_columns["Customer"] == "extra_col"
    assert "customer" in state.source_columns


def test_clear_row_returns_source_to_pool() -> None:
    """Clearing a row returns its source column to the pool."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_pool()
    presenter = ColumnsTabPresenter(view, state)
    presenter.prepopulate()

    # Act
    presenter.clear_row("Sales")

    # Assert: the Sales source returned and its consumed entry is gone.
    assert "sales" in state.source_columns
    assert "Sales" not in state.consumed_columns


def test_dtype_indicator_pushed_for_coercible_match() -> None:
    """A matched column with coercible values yields a green (coercible) indicator."""
    # Arrange: a float column whose source values all coerce.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[("Sales", "measure", True, True, ())],
        column_dtypes={"Sales": "float"},
        source_columns=["sales"],
        preview_slice=PreviewSlice(header=("sales",), rows=(("1.5",), ("2.0",))),
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: the Sales indicator is coercible with no failing example.
    assert ("Sales", True, None) in view.dtype_indicators


def test_derived_column_appears_as_selectable_row() -> None:
    """Decision 7: a derived column appears as a selectable row on the Columns tab."""
    # Arrange: a state with a declared column and one derived column.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[("Customer", "dimension", True, True, ())],
        column_dtypes={"Customer": "string"},
        source_columns=["customer"],
        derived=[("Revenue", "Sales * Units")],
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: the derived column is rendered as a selectable row.
    row_names = [row[0] for row in view.rows[-1]]
    assert "Revenue" in row_names


def test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool() -> None:
    """AC-1: edit path with an empty pool renders persisted aliases as assigned.

    Reproduces the edit-from-button path: a schema is loaded with persisted
    aliases on its rows but no live ``source_columns`` pool (no preview slice).
    Each aliased row must render assigned to its persisted alias, not ``None``.
    """
    # Arrange: two canonical rows each carrying a persisted alias, empty pool.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[
            ("Customer", "dimension", True, True, ("cust_col",)),
            ("Sales", "measure", True, True, ("sales_amt",)),
        ],
        column_dtypes={"Customer": "string", "Sales": "float"},
        source_columns=[],
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: each aliased row renders assigned to its persisted alias.
    assert ("Customer", "cust_col") in view.assignments
    assert ("Sales", "sales_amt") in view.assignments
    assert state.consumed_columns == {"Customer": "cust_col", "Sales": "sales_amt"}


def test_prepopulate_leaves_alias_free_row_unassigned_empty_pool() -> None:
    """AC-2: an edit-path row with no persisted alias renders unassigned.

    With an empty pool, an aliased row is seeded but an alias-free row stays
    unassigned, so the view receives ``(canonical, None)`` for that row.
    """
    # Arrange: one aliased row and one alias-free row, empty pool.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[
            ("Customer", "dimension", True, True, ("cust_col",)),
            ("Sales", "measure", True, True, ()),
        ],
        column_dtypes={"Customer": "string", "Sales": "float"},
        source_columns=[],
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: the alias-free row renders unassigned; the aliased row is seeded.
    assert ("Sales", None) in view.assignments
    assert "Sales" not in state.consumed_columns
    assert state.consumed_columns == {"Customer": "cust_col"}


def test_live_fuzzy_match_wins_over_persisted_alias() -> None:
    """AC-3: a live preview-slice fuzzy match wins over a persisted alias.

    A row carries a persisted alias that differs from the source the live pool
    fuzzy-matches. The live match must win, the persisted alias must not
    override it, and no source may be duplicated across rows.
    """
    # Arrange: 'Customer' fuzzy-matches the live 'customer' source but also
    # carries a different persisted alias ('legacy_cust'); 'Sales' matches live.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[
            ("Customer", "dimension", True, True, ("legacy_cust",)),
            ("Sales", "measure", True, True, ()),
        ],
        column_dtypes={"Customer": "string", "Sales": "float"},
        source_columns=["customer", "sales", "extra_col"],
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: the live fuzzy match wins; the persisted alias does not override it.
    assert state.consumed_columns["Customer"] == "customer"
    assert state.consumed_columns["Sales"] == "sales"
    # One-source-per-row: each consumed source is distinct.
    consumed_sources = list(state.consumed_columns.values())
    assert len(consumed_sources) == len(set(consumed_sources))


def test_dtype_indicator_reports_failing_example_for_non_coercible() -> None:
    """A matched column with a non-coercible value yields a red indicator + example."""
    # Arrange: a float column whose source values include a non-numeric token.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[("Sales", "measure", True, True, ())],
        column_dtypes={"Sales": "float"},
        source_columns=["sales"],
        preview_slice=PreviewSlice(header=("sales",), rows=(("1.5",), ("bad",))),
    )
    presenter = ColumnsTabPresenter(view, state)

    # Act
    presenter.prepopulate()

    # Assert: the indicator is non-coercible and names the masked failing example.
    assert ("Sales", False, "bad") in view.dtype_indicators


def _state_with_masked_slice() -> SchemaBuilderState:
    """Return a state whose matched rows have a 3-row masked preview slice.

    Returns:
        A :class:`SchemaBuilderState` with two canonical columns, near-name source
        matches, and a masked preview slice of three synthetic rows.
    """
    return SchemaBuilderState(
        columns=[
            ("Customer", "dimension", True, True, ()),
            ("Sales", "measure", True, True, ()),
        ],
        column_dtypes={"Customer": "string", "Sales": "float"},
        source_columns=["customer", "sales"],
        preview_slice=PreviewSlice(
            header=("customer", "sales"),
            rows=(("CUST_AAA", "10.0"), ("CUST_BBB", "20.0"), ("CUST_CCC", "30.0")),
        ),
    )


def test_set_preview_row_shows_chosen_row_zero_masked_value() -> None:
    """AC-6: choosing row 0 shows each matched row's masked value for that row."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_masked_slice()
    presenter = ColumnsTabPresenter(view, state)
    presenter.prepopulate()

    # Act: choose preview row 0.
    presenter.set_preview_row(0)

    # Assert: each matched row shows row 0's masked value, not the dtype glyph.
    assert ("Customer", "CUST_AAA") in view.value_displays
    assert ("Sales", "10.0") in view.value_displays


def test_set_preview_row_shows_non_zero_row_masked_value() -> None:
    """AC-6: choosing a non-zero row shows that row's masked value per column."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_masked_slice()
    presenter = ColumnsTabPresenter(view, state)
    presenter.prepopulate()

    # Act: choose preview row 2 (the third row).
    presenter.set_preview_row(2)

    # Assert: each matched row shows row 2's masked value.
    assert ("Customer", "CUST_CCC") in view.value_displays
    assert ("Sales", "30.0") in view.value_displays


def test_set_preview_row_none_restores_dtype_glyph_path() -> None:
    """AC-6: clearing the chosen row (None) restores the dtype-indicator path."""
    # Arrange
    view = FakeColumnsTabView()
    state = _state_with_masked_slice()
    presenter = ColumnsTabPresenter(view, state)
    presenter.prepopulate()
    presenter.set_preview_row(1)
    view.value_displays.clear()
    view.dtype_indicators.clear()

    # Act: clear the chosen row.
    presenter.set_preview_row(None)

    # Assert: no value displays are pushed; the dtype indicators render instead.
    assert view.value_displays == []
    assert any(canonical == "Sales" for canonical, _c, _e in view.dtype_indicators)


def test_set_preview_row_skips_value_display_for_unassigned_row() -> None:
    """AC-6: an unassigned canonical row shows no value for the chosen row."""
    # Arrange: "Sales" has no matching source, so it stays unassigned.
    view = FakeColumnsTabView()
    state = SchemaBuilderState(
        columns=[
            ("Customer", "dimension", True, True, ()),
            ("Sales", "measure", True, True, ()),
        ],
        source_columns=["customer"],
        preview_slice=PreviewSlice(
            header=("customer",), rows=(("CUST_AAA",), ("CUST_BBB",))
        ),
    )
    presenter = ColumnsTabPresenter(view, state)
    presenter.prepopulate()

    # Act: choose row 1.
    presenter.set_preview_row(1)

    # Assert: only the assigned "Customer" row shows a value; "Sales" shows none.
    shown = {canonical for canonical, _v in view.value_displays}
    assert "Customer" in shown
    assert "Sales" not in shown
    # Assert: the value shown is the chosen row's masked value (no real data).
    assert ("Customer", "CUST_BBB") in view.value_displays
