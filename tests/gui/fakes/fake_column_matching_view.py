"""Fake column-matching view for the GUI presenter test suite.

Implements the column-matching view Protocol, records the calls the presenter
makes, and returns a controlled assignment map. The fake holds no logic; it lets
presenter tests run with no ``QApplication`` and assert on what the presenter
pushed to the view.
"""

from __future__ import annotations


class FakeColumnMatchingView:
    """Records calls made to a :class:`ColumnMatchingViewProtocol`.

    Purpose:
        Let column-matching presenter tests assert on what the presenter pushed
        and return a controlled assignment map, with no Qt and no logic.

    Attributes:
        unmatched_required: Each ``set_unmatched_required`` argument, in order.
        source_columns: Each ``set_source_columns`` argument, in order.
        fuzzy_suggestions: Each ``set_fuzzy_suggestions`` argument, in order.
        assignments_set: Each ``set_assignment`` call as ``(required, source)``.
        ignored: Each ``mark_ignored`` argument, in order.
        errors: Each ``show_error`` message, in order.
        assignments: The controlled map ``get_assignments`` returns.
    """

    def __init__(self, assignments: dict[str, str] | None = None) -> None:
        """Initialize records and the controlled assignment map.

        Args:
            assignments: The map ``get_assignments`` returns (default empty).
        """
        self.unmatched_required: list[list[tuple[str, tuple[str, ...]]]] = []
        self.source_columns: list[list[str]] = []
        self.fuzzy_suggestions: list[dict[str, list[tuple[str, float]]]] = []
        self.assignments_set: list[tuple[str, str]] = []
        self.ignored: list[str] = []
        self.errors: list[str] = []
        self.assignments: dict[str, str] = dict(assignments) if assignments else {}

    def set_unmatched_required(self, items: list[tuple[str, tuple[str, ...]]]) -> None:
        """Record the unmatched-required items pushed by the presenter.

        Args:
            items: The ``(canonical_name, aliases)`` pairs.

        Returns:
            ``None``.
        """
        self.unmatched_required.append(list(items))

    def set_source_columns(self, names: list[str]) -> None:
        """Record the source columns pushed by the presenter.

        Args:
            names: The source column names.

        Returns:
            ``None``.
        """
        self.source_columns.append(list(names))

    def set_fuzzy_suggestions(self, items: dict[str, list[tuple[str, float]]]) -> None:
        """Record the fuzzy suggestions pushed by the presenter.

        Args:
            items: The per-column candidate suggestions.

        Returns:
            ``None``.
        """
        self.fuzzy_suggestions.append(dict(items))

    def set_assignment(self, required: str, source: str) -> None:
        """Record an assignment pushed by the presenter.

        Args:
            required: The required canonical name.
            source: The assigned source column.

        Returns:
            ``None``.
        """
        self.assignments_set.append((required, source))

    def mark_ignored(self, required: str) -> None:
        """Record an ignore mark pushed by the presenter.

        Args:
            required: The ignored canonical name.

        Returns:
            ``None``.
        """
        self.ignored.append(required)

    def show_error(self, message: str) -> None:
        """Record an error message pushed by the presenter.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)

    def get_assignments(self) -> dict[str, str]:
        """Return the controlled assignment map.

        Returns:
            The configured required-to-source assignment map.
        """
        return dict(self.assignments)
