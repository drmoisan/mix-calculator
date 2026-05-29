"""PySide6 desktop GUI package for the mix-decomposition pipeline.

This package hosts the GUI composition root, the ``PipelineService`` seam over
the existing loaders and transforms, view Protocols, services, widgets,
presenters, exporters, and the off-UI-thread worker. The existing
``mix-pipeline`` CLI (:mod:`src.mix_pipeline`) is unchanged; this package calls
the reused loader and transform APIs directly through the service seam.
"""
