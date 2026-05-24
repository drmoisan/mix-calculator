"""Core calculations for the mix calculator."""


def mix_ratio(part: float, total: float) -> float:
    """Compute the fraction of a mix occupied by one component.

    Args:
        part: Quantity of the component.
        total: Total quantity of the mix. Must be greater than zero.

    Returns:
        The fraction of the mix occupied by ``part``.

    Raises:
        ValueError: If ``total`` is not greater than zero.
    """
    if total <= 0:
        raise ValueError("total must be greater than zero")
    return part / total
