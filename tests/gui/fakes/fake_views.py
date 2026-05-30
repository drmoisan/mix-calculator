"""Re-export aggregator for the GUI view fakes used by presenter tests.

This module preserves the historical import surface
``from tests.gui.fakes.fake_views import ...`` after the view fakes were split
into per-protocol modules to stay within the file-size ceiling. Each fake now
lives in its own module; this module re-exports them so existing consumers do
not need to change their imports.
"""

from __future__ import annotations

from tests.gui.fakes.fake_column_matching_view import FakeColumnMatchingView
from tests.gui.fakes.fake_pipeline_view import FakeExportView, FakePipelineView
from tests.gui.fakes.fake_schema_builder_view import FakeSchemaBuilderView
from tests.gui.fakes.fake_source_selection_view import FakeSourceSelectionView

__all__ = [
    "FakeColumnMatchingView",
    "FakeExportView",
    "FakePipelineView",
    "FakeSchemaBuilderView",
    "FakeSourceSelectionView",
]
