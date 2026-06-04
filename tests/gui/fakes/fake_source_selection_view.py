"""Fake source-selection view for the GUI presenter test suite.

Implements the source-selection view Protocol, records the calls the presenter
makes, and returns controlled data. The fake holds no logic; it lets presenter
tests run with no ``QApplication`` and assert on what the presenter pushed to
the view.
"""

from __future__ import annotations


class FakeSourceSelectionView:
    """Records calls made to a :class:`SourceSelectionViewProtocol`.

    Attributes:
        tab_lists: Each ``set_tab_list`` argument, in call order.
        previews: Each ``show_preview`` argument, in call order.
        errors: Each ``show_error`` message, in call order.
        schema_lists: Each ``set_schema_list`` argument, in call order (WS2).
        selected_schemas: Each ``set_selected_schema`` name, in call order (WS2).
    """

    def __init__(self) -> None:
        """Initialize empty call records."""
        self.tab_lists: list[list[str]] = []
        self.previews: list[list[list[str]]] = []
        self.errors: list[str] = []
        self.schema_lists: list[list[str]] = []
        self.selected_schemas: list[str] = []

    def set_tab_list(self, tabs: list[str]) -> None:
        """Record the tab list pushed by the presenter.

        Args:
            tabs: The worksheet-tab names.

        Returns:
            ``None``.
        """
        self.tab_lists.append(list(tabs))

    def show_preview(self, rows: list[list[str]]) -> None:
        """Record the preview rows pushed by the presenter.

        Args:
            rows: The preview rows.

        Returns:
            ``None``.
        """
        self.previews.append([list(row) for row in rows])

    def show_error(self, message: str) -> None:
        """Record an error message pushed by the presenter.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)

    def set_schema_list(self, names: list[str]) -> None:
        """Record the schema list pushed by the presenter (WS2).

        Args:
            names: The schema names offered in the dropdown.

        Returns:
            ``None``.
        """
        self.schema_lists.append(list(names))

    def set_selected_schema(self, name: str) -> None:
        """Record an auto-selected schema name pushed by the presenter (WS2).

        Args:
            name: The selected schema name.

        Returns:
            ``None``.
        """
        self.selected_schemas.append(name)
