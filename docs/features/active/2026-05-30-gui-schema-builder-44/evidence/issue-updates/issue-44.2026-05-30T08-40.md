# Issue Update Mirror — Issue #44 (gui-schema-builder)

Timestamp: 2026-05-30T08-40

POSTING BLOCKED

Reason: The execution directive explicitly instructs "No commit/push/PR — leave
changes in the working tree." No GitHub issue update was posted; this mirror
records the intended status text for audit only.

PostedAs: unknown (not posted)

## Intended update text

Feature D (GUI schema builder, epic #40) implementation is complete in the working
tree. Summary:

- New modules: `SchemaService` + `SchemaServiceProtocol` (T2), two view protocols
  (`ColumnMatchingViewProtocol`, `SchemaBuilderViewProtocol`), two pure presenters
  (`ColumnMatchingPresenter`, `SchemaBuilderPresenter`) + `_schema_builder_state`,
  two passive Qt dialogs (`ColumnMatchingDialog`, `SchemaBuilderDialog`) +
  `_schema_builder_tabs`, and the composition wiring `_schema_wiring`.
- Additive, behavior-preserving edits to `app.py`, `main_window.py`,
  `pipeline_service.py` (new `import_with_schema`), and `protocols.py`.
- AC1 known-file parity asserted with `assert_frame_equal` for AOP and LE bundled
  default schemas against the default loaders (the known-file path is unchanged).
- AC1–AC9 satisfied; full toolchain clean in a single pass (Black, Ruff, Pyright
  strict, Pytest); 717 tests pass; total coverage 99% line / 96% branch; new
  presenter/service modules at 100%.
- Protected CLI/transform/loader and Feature A/B/C paths unchanged
  (empty protected-path diff).

Note: `src/gui/protocols.py` would have exceeded the 500-line cap if both new
protocols were added inline, so the two new protocols live in the additive
sibling module `src/gui/_schema_view_protocols.py` and are re-exported from
`protocols.py`; the existing four protocols are unchanged and unmoved.
