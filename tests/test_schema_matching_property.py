"""Property-based determinism tests for schema matching (AC7, T2 requirement).

Verifies that :func:`src.schema_matching.find_best_match` is deterministic: for
any generated header list and schema set, two calls on the same inputs return
identical ``(schema, score)``. Determinism is required by the repository's
determinism-infrastructure policy; ``hypothesis`` prints the failing example and
its seed automatically on failure, satisfying the reproducibility requirement.

No wall-clock, RNG (beyond hypothesis's own seeded generation), filesystem, or
network is used in the code under test.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from src.schema_matching import find_best_match
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref

# A small fixed vocabulary keeps generated names realistic and bounds the search
# space so the property runs quickly while still exercising matches and misses.
_NAME_VOCAB = ["sku", "region", "net sales", "gross sales", "quarter", "ppg", "x", "y"]

# Strategy for a non-empty column name drawn from the shared vocabulary.
_column_name = st.sampled_from(_NAME_VOCAB)

# Strategy for a header label; reuses the vocabulary plus a couple of variants so
# both exact and near/non matches are generated.
_header = st.sampled_from([*_NAME_VOCAB, "regiom", "net_sales", "unrelated"])


@st.composite
def _schemas(draw: st.DrawFn) -> SchemaDefinition:
    """Generate a valid schema with a small set of uniquely-named columns.

    Args:
        draw: The hypothesis draw function supplied by the composite strategy.

    Returns:
        A constructed :class:`SchemaDefinition` whose key references its first
        column, satisfying the model's structural invariants.
    """
    # Draw a unique, ordered set of column names so the schema has no duplicate
    # canonical_name (which the model would otherwise allow but which would make
    # coverage ambiguous to read).
    names = draw(st.lists(_column_name, min_size=1, max_size=4, unique=True))
    columns = tuple(ColumnSpec(canonical_name=name, role="dimension") for name in names)
    version = draw(st.sampled_from(["1", "2", "3"]))
    schema_name = draw(st.sampled_from(["alpha", "beta", "gamma"]))
    return SchemaDefinition(
        name=schema_name,
        version=version,
        columns=columns,
        key=KeySpec(parts=tuple(column_ref(_n) for _n in (names[0],))),
    )


@given(
    headers=st.lists(_header, min_size=0, max_size=5),
    schemas=st.lists(_schemas(), min_size=0, max_size=4),
)
def test_find_best_match_is_deterministic(
    headers: list[str],
    schemas: list[SchemaDefinition],
) -> None:
    """find_best_match returns identical (schema, score) on repeated calls."""
    # Act: call twice on the same inputs.
    first = find_best_match(headers, schemas)
    second = find_best_match(headers, schemas)

    # Assert: the selected schema identity and the score are identical, so the
    # selection is fully determined by the inputs.
    assert first.schema is second.schema
    assert first.score == second.score
