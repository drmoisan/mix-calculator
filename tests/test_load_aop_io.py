"""SQLite persistence and CLI tests for :mod:`src.load_aop`.

Covers ``persist_aop`` (round-trip, replace-no-duplication, index creation) and
the ``main`` CLI entry point (success exit 0, missing ``--output`` non-zero,
ValueError exit 1, ``--snake-case`` rename, custom sheet/table name). Pure
transform tests live in ``test_load_aop.py``. SQLite round-trips reuse the
in-memory ``PersistentConnection`` from ``tests.le_fixtures`` and Excel sources
use ``io.BytesIO`` so no temporary files are created on disk.
"""

from __future__ import annotations

import pytest

from src.load_aop import SOURCE_COLUMNS, main, persist_aop
from tests.aop_fixtures import (
    aop_header_without_key,
    build_aop_workbook,
    loaded_aop_frame,
    make_aop_row,
    patch_load_aop,
)
from tests.le_fixtures import patch_connect, read_table

# ---------------------------------------------------------------------------
# persist_aop (in-memory round-trip)
# ---------------------------------------------------------------------------


def test_persist_aop_roundtrip_columns_and_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A persisted frame reads back with matching columns and row count."""
    # Arrange: share one in-memory connection so no file is created.
    frame = loaded_aop_frame(
        [
            make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
            make_aop_row(customer="B", sku=2, type_="T", months=[2.0] * 12),
        ]
    )
    con = patch_connect(monkeypatch)

    # Act
    persist_aop(frame, "ignored.db", table="aop")
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: columns and row count round-trip faithfully.
    assert set(read_back.columns) == set(frame.columns)
    assert len(read_back) == 2


def test_persist_aop_replace_no_duplication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Writing the same frame twice with replace does not duplicate rows."""
    # Arrange
    frame = loaded_aop_frame(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    )
    con = patch_connect(monkeypatch)

    # Act: write twice into the same in-memory table with the default replace.
    persist_aop(frame, "ignored.db", table="aop", if_exists="replace")
    persist_aop(frame, "ignored.db", table="aop", if_exists="replace")
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: only the single source row remains (no duplication).
    assert len(read_back) == 1


def test_persist_aop_creates_safe_lookup_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quoted lowercase lookup indexes are created with SQL-safe names."""
    # Arrange
    frame = loaded_aop_frame(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    )
    con = patch_connect(monkeypatch)

    # Act
    persist_aop(frame, "ignored.db", table="aop")
    # Query the catalog for the index names created on the table.
    cursor = con.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='aop'"
    )
    index_names = {str(row[0]) for row in cursor.fetchall()}
    con.real_close()

    # Assert: each indexable column produced a safe lowercase index name
    # (space -> _, # -> num).
    assert "ix_aop_key" in index_names
    assert "ix_aop_customer" in index_names
    assert "ix_aop_sku_num" in index_names
    assert "ix_aop_type" in index_names


# ---------------------------------------------------------------------------
# main (CLI) end-to-end
# ---------------------------------------------------------------------------


def test_main_success_prints_summary_and_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main loads, persists, prints the summary and confirmation; returns 0."""
    # Arrange
    buffer = build_aop_workbook(
        [
            make_aop_row(customer="CustA", sku=5, type_="GS", months=[1.0] * 12),
            make_aop_row(customer="CustB", sku=9, type_="Lbs", months=[3.0] * 12),
        ]
    )
    patch_load_aop(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    read_back = read_table(con, "aop")
    con.real_close()
    captured = capsys.readouterr()

    # Assert
    assert exit_code == 0
    assert len(read_back) == 2
    assert "Loaded sheet 'AOP1':" in captured.out
    assert "Rows:" in captured.out
    assert "Validation:     OK" in captured.out
    assert "Persisted 2 rows to out.db (table='aop')" in captured.out


def test_main_missing_output_exits_nonzero() -> None:
    """Invoking main without --output raises SystemExit with a non-zero code."""
    # Act / Assert
    with pytest.raises(SystemExit) as exc_info:
        main(["input.xlsx"])
    assert exc_info.value.code != 0


def test_main_validation_error_returns_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A validation ValueError yields a return code of 1 and an error message."""
    # Arrange: a row whose YTD does not tie out fails validation.
    bad_row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    bad_row["YTD"] = 999.0
    buffer = build_aop_workbook([bad_row], header=aop_header_without_key())
    patch_load_aop(monkeypatch, buffer)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert
    assert exit_code == 1
    assert "YTD" in captured.out


def test_main_missing_required_column_returns_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A workbook missing a required column yields return 1 naming the column."""
    # Arrange: drop PPG so resolution raises.
    bad_header = [c for c in aop_header_without_key() if c != "PPG"]
    buffer = build_aop_workbook(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)],
        header=bad_header,
    )
    patch_load_aop(monkeypatch, buffer)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert
    assert exit_code == 1
    assert "PPG" in captured.out


def test_main_diverging_key_prompt_non_tty_returns_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A diverging KEY under default prompt on non-TTY stdin returns 1."""
    # Arrange: a KEY-bearing workbook whose KEY diverges from the rebuilt pattern.
    buffer = build_aop_workbook(
        [
            make_aop_row(
                customer="A", sku=1, type_="T", months=[1.0] * 12, key="DIVERGENT"
            )
        ],
        header=SOURCE_COLUMNS,
    )
    patch_load_aop(monkeypatch, buffer, is_tty=False)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert
    assert exit_code == 1
    assert "--key-mismatch" in captured.out


def test_main_debug_flag_reraises_original_valueerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--debug re-raises the original ValueError instead of swallowing it."""
    # Arrange: a row whose YTD does not tie out so load_aop raises a ValueError.
    bad_row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    bad_row["YTD"] = 999.0
    buffer = build_aop_workbook([bad_row], header=aop_header_without_key())
    patch_load_aop(monkeypatch, buffer)

    # Act / Assert: the original validation message propagates out of main.
    with pytest.raises(ValueError, match="YTD"):
        main(["input.xlsx", "--output", "out.db", "--debug"])


def test_main_debug_env_var_reraises_without_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A truthy LOAD_AOP_DEBUG re-raises even when --debug is absent."""
    # Arrange: a failing workbook and a truthy env var, but no --debug flag.
    bad_row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    bad_row["YTD"] = 999.0
    buffer = build_aop_workbook([bad_row], header=aop_header_without_key())
    patch_load_aop(monkeypatch, buffer)
    monkeypatch.setenv("LOAD_AOP_DEBUG", "1")

    # Act / Assert: the env var alone activates debug-mode re-raise.
    with pytest.raises(ValueError, match="YTD"):
        main(["input.xlsx", "--output", "out.db"])


@pytest.mark.parametrize("falsey", ["0", "false", "FALSE", "no", ""])
def test_main_debug_env_var_falsey_preserves_swallow(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    falsey: str,
) -> None:
    """Falsey LOAD_AOP_DEBUG values keep the swallow-and-return-1 behavior."""
    # Arrange: a failing workbook with a falsey debug env var and no --debug.
    bad_row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    bad_row["YTD"] = 999.0
    buffer = build_aop_workbook([bad_row], header=aop_header_without_key())
    patch_load_aop(monkeypatch, buffer)
    monkeypatch.setenv("LOAD_AOP_DEBUG", falsey)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert: the error is swallowed and mapped to a clean exit 1.
    assert exit_code == 1
    assert "YTD" in captured.out


def test_main_debug_env_var_unset_preserves_swallow(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unset LOAD_AOP_DEBUG keeps the swallow-and-return-1 behavior."""
    # Arrange: a failing workbook with the debug env var explicitly unset.
    bad_row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    bad_row["YTD"] = 999.0
    buffer = build_aop_workbook([bad_row], header=aop_header_without_key())
    patch_load_aop(monkeypatch, buffer)
    monkeypatch.delenv("LOAD_AOP_DEBUG", raising=False)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    captured = capsys.readouterr()

    # Assert: without flag or truthy env var, the failure is swallowed.
    assert exit_code == 1
    assert "YTD" in captured.out


def test_main_snake_case_renames_before_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--snake-case renames columns to snake_case before persisting."""
    # Arrange
    buffer = build_aop_workbook(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    )
    patch_load_aop(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db", "--snake-case"])
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: persisted headers are the snake_case forms (typo column renamed).
    assert exit_code == 0
    assert "sku_description" in read_back.columns
    assert "sku_num" in read_back.columns
    assert "customer_master" in read_back.columns
    assert "super_category" in read_back.columns
    assert "ytd" in read_back.columns
    assert "SKU Descripiton" not in read_back.columns


def test_persist_aop_roundtrip_without_ytg_has_no_ytg_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A no-YTG frame persists and reads back without a YTG column."""
    # Arrange: load the older no-YTG layout and share one in-memory connection.
    frame = loaded_aop_frame(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)],
        include_ytg=False,
    )
    con = patch_connect(monkeypatch)

    # Act
    persist_aop(frame, "ignored.db", table="aop")
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: neither the canonical nor the snake_case YTG name is present.
    assert "YTG" not in read_back.columns
    assert "ytg" not in read_back.columns
    assert len(read_back) == 1


def test_main_without_ytg_succeeds_and_table_has_no_ytg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end main on a no-YTG source persists a table without YTG."""
    # Arrange: a no-YTG workbook routed through the patched load path.
    buffer = build_aop_workbook(
        [
            make_aop_row(customer="CustA", sku=5, type_="GS", months=[1.0] * 12),
            make_aop_row(customer="CustB", sku=9, type_="Lbs", months=[3.0] * 12),
        ],
        include_ytg=False,
    )
    patch_load_aop(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: success, both rows persisted, and no YTG column on the table.
    assert exit_code == 0
    assert len(read_back) == 2
    assert "YTG" not in read_back.columns
    assert "ytg" not in read_back.columns


def test_main_snake_case_without_ytg_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--snake-case works on a no-YTG source and produces no ytg column."""
    # Arrange: a no-YTG workbook; --snake-case must not error on the absent YTG.
    buffer = build_aop_workbook(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)],
        include_ytg=False,
    )
    patch_load_aop(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db", "--snake-case"])
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: the rename succeeds (pandas ignores the absent YTG key) and the
    # other snake_case headers are present while no ytg column appears.
    assert exit_code == 0
    assert "ytd" in read_back.columns
    assert "sku_description" in read_back.columns
    assert "ytg" not in read_back.columns


def test_main_with_ytg_persists_ytg_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end main on a YTG-bearing source persists the YTG column."""
    # Arrange: the default workbook keeps the optional YTG column.
    buffer = build_aop_workbook(
        [make_aop_row(customer="A", sku=1, type_="T", months=[2.0] * 12)]
    )
    patch_load_aop(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(["input.xlsx", "--output", "out.db"])
    read_back = read_table(con, "aop")
    con.real_close()

    # Assert: the YTG column survives the round-trip under its canonical name.
    assert exit_code == 0
    assert "YTG" in read_back.columns


def test_main_custom_sheet_and_table_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main honors a custom --source-sheet and --table-name."""
    # Arrange: build the workbook on a non-default sheet name.
    buffer = build_aop_workbook(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)],
        sheet_name="CustomAOP",
    )
    patch_load_aop(monkeypatch, buffer)
    con = patch_connect(monkeypatch)

    # Act
    exit_code = main(
        [
            "input.xlsx",
            "--output",
            "out.db",
            "--source-sheet",
            "CustomAOP",
            "--table-name",
            "custom_table",
        ]
    )
    read_back = read_table(con, "custom_table")
    con.real_close()

    # Assert
    assert exit_code == 0
    assert len(read_back) == 1
