"""KEY-resolution seam-forwarding tests for SchemaLoader (issue #58).

Covers the ``resolver``/``is_tty``/``prompt`` injection seam added by #58 and the
backward-compatibility of positional callers, extracted from
``tests.test_schema_loader_core`` to keep both modules under the 500-line
file-size cap. The shared ``_load_default`` helper and the ``_MONTHS_A`` /
``_MONTHS_B`` monthly vectors are imported from the original core module so the
fixtures stay identical. Uses the in-memory AOP fixtures; no temp files, no
network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st

from src.schema_loader import SchemaLoader

# The in-memory fixtures live in the tests package and import as package modules.
from tests import aop_fixtures
from tests._schema_loader_fixtures import _MONTHS_A, _MONTHS_B, _load_default

if TYPE_CHECKING:
    import pandas as pd


def _diverging_key_aop_frame() -> pd.DataFrame:
    """Build a raw AOP frame whose source KEY diverges from the rebuilt pattern.

    The workbook includes an explicit ``KEY`` column whose value does not equal
    ``Customer + coerce_sku(SKU #) + Type``, so loading triggers the divergence
    branch in :func:`src.etl_key.resolve_key`.

    Returns:
        The raw DataFrame read at the AOP header row, carrying a diverging KEY.
    """
    from src.pandas_io import read_excel_sheet

    # An explicit header that includes the optional KEY column so the present-KEY
    # branch is exercised; the row's KEY value is deliberately wrong.
    header = list(aop_fixtures.SOURCE_COLUMNS)
    rows = [
        aop_fixtures.make_aop_row(
            customer="A",
            sku="1",
            type_="Net",
            months=_MONTHS_A,
            key="WRONGKEY",
        ),
    ]
    workbook = aop_fixtures.build_aop_workbook(rows, header=header)
    return read_excel_sheet(workbook, sheet_name="AOP1", header=2)


def test_load_forwards_resolver_seams_to_resolve_key_on_divergence() -> None:
    """The injected resolver is the decision source on a diverging KEY (AC-5).

    Asserts that the ``resolver`` callable passed to ``SchemaLoader.load`` reaches
    :func:`src.etl_key.resolve_key` and governs the KEY outcome on divergence,
    rather than ``decide_key_action`` consulting ``is_tty``/``prompt``.
    """
    # Arrange: a frame whose source KEY diverges, plus spies for the three seams.
    raw_frame = _diverging_key_aop_frame()
    resolver_calls: list[list[tuple[str, str]]] = []
    is_tty_calls: list[bool] = []
    prompt_calls: list[str] = []

    def _resolver(examples: list[tuple[str, str]]) -> str:
        # Record the call and choose "overwrite" so the rebuilt pattern wins.
        resolver_calls.append(examples)
        return "overwrite"

    def _is_tty() -> bool:
        # Record that the TTY seam was consulted (it should not drive the decision).
        is_tty_calls.append(True)
        return False

    def _prompt(message: str) -> str:
        # The prompt seam must never be reached when a resolver is supplied.
        prompt_calls.append(message)
        raise AssertionError("prompt must not be invoked when a resolver is supplied")

    schema = _load_default("default_aop")
    # Act
    out = SchemaLoader(schema).load(
        raw_frame, resolver=_resolver, is_tty=_is_tty, prompt=_prompt
    )
    # Assert: the resolver was the decision source and "overwrite" rebuilt the KEY.
    assert len(resolver_calls) == 1
    assert prompt_calls == []
    assert out.loc[0, "KEY"] == "A1Net"


@given(action=st.sampled_from(["trust", "overwrite"]))
def test_property_resolver_action_governs_key_on_divergence(action: str) -> None:
    """For every diverging frame, the resolver's action governs the KEY (AC-5, T1).

    Property: when the source KEY diverges, the action returned by the injected
    resolver (``"trust"`` keeps the existing KEY; ``"overwrite"`` rebuilds it) is
    the decision source for the resulting ``KEY`` column.
    """
    # Arrange: a diverging-KEY frame and a resolver returning the generated action.
    raw_frame = _diverging_key_aop_frame()

    def _resolver(_examples: list[tuple[str, str]]) -> str:
        return action

    def _prompt(_message: str) -> str:
        raise AssertionError("prompt must not be invoked when a resolver is supplied")

    schema = _load_default("default_aop")
    # Act
    out = SchemaLoader(schema).load(raw_frame, resolver=_resolver, prompt=_prompt)
    # Assert: the resolved action determines the KEY value.
    # "trust" keeps the diverging source value; "overwrite" rebuilds the pattern.
    expected = "WRONGKEY" if action == "trust" else "A1Net"
    assert out.loc[0, "KEY"] == expected


def test_load_backward_compatible_without_seam_arguments() -> None:
    """Existing positional callers are unaffected by the new seams (AC-8).

    Calling ``load(raw)`` and ``load(raw, schema)`` with no seam arguments yields
    the same non-diverging-KEY behavior as before: the KEY is rebuilt from the
    pattern and no prompt path is reached (the default resolver is ``None`` and
    the non-diverging branch never consults ``is_tty``/``prompt``).
    """
    # Arrange: a normal AOP frame with no source KEY column (absent-KEY branch).
    from src.pandas_io import read_excel_sheet

    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer="B", sku="2", type_="Gross", months=_MONTHS_B
        ),
    ]
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )
    schema = _load_default("default_aop")
    # Act: both the one-arg and two-arg positional call forms.
    out_one_arg = SchemaLoader(schema).load(raw_frame)
    out_two_arg = SchemaLoader(schema).load(raw_frame, schema)
    # Assert: KEY rebuilt from the pattern; behavior unchanged across both forms.
    assert list(out_one_arg["KEY"]) == ["A1Net", "B2Gross"]
    assert list(out_two_arg["KEY"]) == ["A1Net", "B2Gross"]
