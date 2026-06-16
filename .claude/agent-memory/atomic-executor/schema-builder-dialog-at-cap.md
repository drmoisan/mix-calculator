---
name: schema-builder-dialog-at-cap
description: schema_builder_dialog.py rides the 500-line cap; adding any view method forces extracting an accessor pair to a helper module and using namespace imports
metadata:
  type: project
---

`src/gui/widgets/schema_builder_dialog.py` is a passive view implementing
`SchemaBuilderViewProtocol` with ~27 thin, fully-docstring'd accessor methods. It
sits within a few lines of the 500-line cap, so almost any change that adds a view
method pushes it over.

**Why:** Every protocol method needs a mandatory class/function docstring
(commenting policy), so methods cost ~12-18 lines each. The file cannot absorb new
methods without offsetting extraction.

**How to apply:** When adding to this dialog, extract the relevant accessor pair to
a per-concern helper module that carries the docstrings as free functions, and have
the dialog delegate. Existing helper modules: `_schema_builder_tabs.py`
(identity build + `set/read_identity_controls`), `_key_multiselect_widget.py`
(`set/read_key_controls`, `set_key_parts_controls`, `toggle_column`),
`_schema_dedup_discriminator.py` (`select_dedup_discriminator`, `read_dedup_controls`),
`_schema_builder_derived_format.py` (`render/read_derived_editor` + bracket strip/add),
`_schema_preview_table.py` (`render_preview`, `read_table_text`),
`_schema_dialog_surfaces.py` (error/preview message surfaces).

The single biggest lever is **namespace imports**: importing each helper as
`import _module as alias` collapses a multi-name `from ... import (...)` block (often
8-10 lines) to one line. The dialog already does this (`tabs_mod`, `keys`, `dedup`,
`derived_fmt`, `preview`, `surfaces`). Prefer adding to an existing helper over a new
import group.

Related: `[[powershell-bom-required]]` is unrelated; see issue #72
(schema-builder-ux-overhaul) for the full extraction history.
