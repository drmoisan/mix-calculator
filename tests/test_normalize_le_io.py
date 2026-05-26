"""I/O, persistence, and CLI tests for :mod:`src.normalize_le`.

Covers ``validate_tieouts``, ``write_sqlite``, ``print_summary``, and the
``main`` CLI entry point. Pure-transform tests live in
``test_normalize_le.py``. Shared in-memory fixtures live in ``le_fixtures.py``;
SQLite round-trips use ``sqlite3.connect(":memory:")`` and Excel sources use
``io.BytesIO`` so no temporary files are created on disk.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.normalize_le import (
    SOURCE_COLUMNS,
    TARGET_COLUMNS,
    main,
    normalize,
    print_summary,
    validate_tieouts,
    write_sqlite,
)
from tests.le_fixtures import (
    as_float,
    build_workbook,
    loaded_frame,
    make_row,
    normalized_sample,
    patch_connect,
    patch_load_source,
    read_table,
)

# ---------------------------------------------------------------------------
# validate_tieouts
# ---------------------------------------------------------------------------


def test_validate_tieouts_pass_path() -> None:
    """A faithful source/output transform passes validation without raising."""
    # Arrange
    frame = loaded_frame(
        [
            make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12),
            make_row(customer="A", sku=1, type_="T", ppg="P", months=[2.0] * 12),
        ]
    )
    out = normalize(frame)

    # Act / Assert
    assert validate_tieouts(frame, out) is None


def test_validate_tieouts_row_count_mismatch_raises() -> None:
    """A row-count mismatch raises ValueError."""
    # Arrange
    frame = loaded_frame(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12)]
    )
    out = normalize(frame)
    # Duplicate the single output row to force a count mismatch.
    out_doubled = pd.concat([out, out], ignore_index=True)

    # Act / Assert
    with pytest.raises(ValueError, match="row count"):
        validate_tieouts(frame, out_doubled)


def test_validate_tieouts_column_total_perturbation_raises() -> None:
    """A column total perturbed beyond 1e-6 raises ValueError."""
    # Arrange
    frame = loaded_frame(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12)]
    )
    out = normalize(frame)
    out.loc[0, "Jan"] = as_float(out.loc[0, "Jan"]) + 1.0

    # Act / Assert
    with pytest.raises(ValueError, match="Jan"):
        validate_tieouts(frame, out)


def test_validate_tieouts_fy_mismatch_raises() -> None:
    """An output row where FY != sum(months) raises ValueError."""
    # Arrange: perturb FY only, then realign the source FY so column totals match
    # but the per-row FY == sum(months) invariant is violated.
    frame = loaded_frame(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12)]
    )
    out = normalize(frame)
    out.loc[0, "FY"] = as_float(out.loc[0, "FY"]) + 5.0
    frame.loc[frame.index[0], "FY"] = as_float(frame.loc[frame.index[0], "FY"]) + 5.0

    # Act / Assert
    with pytest.raises(ValueError, match="FY"):
        validate_tieouts(frame, out)


@given(
    specs=st.lists(
        st.lists(
            st.floats(
                allow_nan=False,
                allow_infinity=False,
                min_value=-1e5,
                max_value=1e5,
                width=32,
            ),
            min_size=12,
            max_size=12,
        ),
        min_size=1,
        max_size=6,
    )
)
def test_validate_tieouts_property_roundtrip(specs: list[list[float]]) -> None:
    """normalize output always passes validate_tieouts (round-trip consistency)."""
    # Arrange: all rows share one KEY so FY/quarter source values stay coherent.
    rows = [
        make_row(customer="A", sku=1, type_="T", ppg="P", months=vector)
        for vector in specs
    ]
    frame = loaded_frame(rows)

    # Act
    out = normalize(frame)

    # Assert
    assert validate_tieouts(frame, out) is None


# ---------------------------------------------------------------------------
# write_sqlite (in-memory round-trip)
# ---------------------------------------------------------------------------


def test_write_sqlite_roundtrip_columns_and_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A persisted frame reads back with the 26 columns in order and row count."""
    # Arrange: share one in-memory connection so no file is created.
    out = normalized_sample()
    con = patch_connect(monkeypatch)

    # Act
    write_sqlite(out, "ignored.db", "LE")
    read_back = read_table(con, "LE")
    con.real_close()

    # Assert
    assert list(read_back.columns) == TARGET_COLUMNS
    assert len(read_back) == 2


def test_write_sqlite_replace_if_exists_no_duplication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Writing the same frame twice replaces the table without duplicating rows."""
    # Arrange
    out = normalized_sample()
    con = patch_connect(monkeypatch)

    # Act: write twice into the same in-memory table.
    write_sqlite(out, "ignored.db", "LE")
    write_sqlite(out, "ignored.db", "LE")
    read_back = read_table(con, "LE")
    con.real_close()

    # Assert
    assert len(read_back) == 2


# ---------------------------------------------------------------------------
# main (CLI) end-to-end
# ---------------------------------------------------------------------------


def test_main_end_to_end_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main loads, normalizes, persists, and prints a summary; returns 0."""
    # Arrange
    buffer = build_workbook(
        [
            make_row(customer="CustB", sku=5, type_="GS", ppg="PX", months=[1.0] * 12),
            make_row(customer="CustB", sku=5, type_="GS", ppg="PX", months=[2.0] * 12),
            make_row(customer="CustA", sku=9, type_="Lbs", ppg="PY", months=[3.0] * 12),
        ]
    )
    patch_load_source(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db", "--table-name", "LE"])
    read_back = read_table(con, "LE")
    con.real_close()
    captured = capsys.readouterr()

    # Assert
    assert exit_code == 0
    assert list(read_back.columns) == TARGET_COLUMNS
    assert len(read_back) == 2
    assert "Source rows:" in captured.out
    assert "Unique keys:" in captured.out
    assert "Output rows:" in captured.out
    assert "Tie-outs" in captured.out
    assert "First output row:" in captured.out
    assert "Middle output row:" in captured.out
    assert "Last output row:" in captured.out


def test_main_missing_output_exits_nonzero() -> None:
    """Invoking main without --output raises SystemExit with a non-zero code."""
    # Act / Assert
    with pytest.raises(SystemExit) as exc_info:
        main(["input.xlsx"])
    assert exc_info.value.code != 0


def test_main_unmatched_required_column_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A workbook missing a required column yields a non-zero return naming it."""
    # Arrange: drop the PPG column from the header so resolution cannot bind it.
    bad_header = [c for c in SOURCE_COLUMNS if c != "PPG"]
    buffer = build_workbook(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12)],
        header=bad_header,
    )
    patch_load_source(monkeypatch, buffer)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert
    assert exit_code != 0
    assert "PPG" in captured.out


def test_main_diverging_key_prompt_non_tty_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A diverging KEY under default 'prompt' on non-TTY stdin exits non-zero."""
    # Arrange: a KEY-bearing workbook whose KEY diverges from the rebuilt pattern.
    buffer = build_workbook(
        [
            make_row(
                customer="A",
                sku=1,
                type_="T",
                ppg="P",
                months=[1.0] * 12,
                key="DIVERGENT_KEY",
            )
        ],
        header=SOURCE_COLUMNS,
    )
    patch_load_source(monkeypatch, buffer, is_tty=False)

    # Act: default --key-mismatch is prompt; non-TTY must fail fast.
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert
    assert exit_code != 0
    assert "--key-mismatch" in captured.out


def test_main_diverging_key_overwrite_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A diverging KEY under --key-mismatch overwrite persists the rebuilt key."""
    # Arrange
    buffer = build_workbook(
        [
            make_row(
                customer="A",
                sku=1,
                type_="T",
                ppg="P",
                months=[1.0] * 12,
                key="DIVERGENT_KEY",
            )
        ],
        header=SOURCE_COLUMNS,
    )
    patch_load_source(monkeypatch, buffer, is_tty=False)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(
        ["input.xlsx", "--output", "out.db", "--key-mismatch", "overwrite"]
    )
    read_back = read_table(con, "LE")
    con.real_close()

    # Assert: the persisted KEY is the rebuilt pattern, not the divergent value.
    assert exit_code == 0
    assert read_back.iloc[0]["KEY"] == "A1T"


def test_main_custom_sheet_and_table_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main honors custom --source-sheet and --table-name and persists correctly."""
    # Arrange: build the workbook on a non-default sheet name.
    buffer = build_workbook(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12)],
        sheet_name="CustomSheet",
    )
    patch_load_source(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(
        [
            "input.xlsx",
            "--output",
            "out.db",
            "--source-sheet",
            "CustomSheet",
            "--table-name",
            "CustomTable",
        ]
    )
    read_back = read_table(con, "CustomTable")
    con.real_close()

    # Assert
    assert exit_code == 0
    assert list(read_back.columns) == TARGET_COLUMNS
    assert len(read_back) == 1


# ---------------------------------------------------------------------------
# print_summary
# ---------------------------------------------------------------------------


def test_print_summary_empty_output_omits_row_samples(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With zero output rows, the header lines print but row samples are omitted."""
    # Arrange: an empty source/output frame exercises the zero-rows branch.
    empty_source = pd.DataFrame({column: [] for column in SOURCE_COLUMNS})
    empty_output = pd.DataFrame({column: [] for column in TARGET_COLUMNS})

    # Act
    print_summary(empty_source, empty_output)
    captured = capsys.readouterr()

    # Assert
    assert "Source rows: 0" in captured.out
    assert "Output rows: 0" in captured.out
    assert "First output row:" not in captured.out
