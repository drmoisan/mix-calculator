# Phase 0 — Builder Column-Row Tuple Unpack/Annotation Sites

Timestamp: 2026-06-06T15-01
Command: Grep for `(canonical, role, required, aliases)` unpack sites and
`tuple[str, str, bool, tuple[str, ...]]` annotations across src/ and tests/.
EXIT_CODE: 0

Output Summary (authoritative checklist for Phase 4; 4-tuple -> 5-tuple migration).
Each site adds an `in_output: bool` between `required` and `aliases`.

## Production — src/gui/presenters/_schema_builder_state.py (P4-T1)
- L113: docstring `(canonical_name, role, required, aliases)` -> add in_output
- L144: field annotation `list[tuple[str, str, bool, tuple[str, ...]]]` -> 5-tuple
- L171: comprehension `for canonical, _role, _required, _aliases in state.columns`
- L254: assemble_schema comprehension `for canonical, role, required, aliases in state.columns`

## Production — src/gui/presenters/schema_builder_presenter.py (P4-T2)
- L169: `_spec_to_row` return annotation `tuple[str, str, bool, tuple[str, ...]]`
- L176: docstring `(canonical_name, role, required, aliases)`
- L339: comprehension `for canonical, _role, _required, _aliases in self._state.columns`
- (_spec_to_row body and _state_from_schema row build also emit the tuple)

## Production — src/gui/presenters/_columns_tab_presenter.py (P4-T3)
- L99: `for canonical, _role, _required, _aliases in list(self._state.columns)`
- L292: `for index, (name, role, required, aliases) in enumerate(self._state.columns)`
- L295: reassignment `self._state.columns[index] = (name, role, required, new_aliases)` -> carry in_output
- L313: comprehension `for name, _role, _required, _aliases in self._state.columns`
- L337: `for canonical, _role, _required, _aliases in self._state.columns`

## Production — src/gui/_schema_view_protocols.py (P4-T4)
- L195: `set_columns` param annotation `list[tuple[str, str, bool, tuple[str, ...]]]`
- L199: docstring `(canonical_name, role, required, aliases)`
- L210: `get_columns` return annotation `list[tuple[str, str, bool, tuple[str, ...]]]`
- L214: docstring `(canonical_name, role, required, aliases)`

## Production — src/gui/widgets/schema_builder_dialog.py (P4-T4)
- L159: `set_columns` param annotation
- L163: docstring
- L175: `get_columns` return annotation
- L179: docstring
- L328: `for canonical, _r, _req, _a in self.get_columns()`

## Production — src/gui/widgets/_schema_builder_drag_tabs.py (P4-T4)
- L95: `set_columns` param annotation
- L104: docstring
- L141: `get_columns` return annotation
- L145: docstring
- L267: `[canonical for canonical, _r, _req, _a in self._state.columns]`

## Tests (must also be updated for Pyright-clean + passing)
- tests/gui/fakes/fake_schema_builder_view.py L42, L54, L80, L91: annotations `tuple[str, str, bool, tuple[str, ...]]`
- tests/gui/test_app_wiring_schema.py L280: `for name, _r, _req, _a in presenter.state.columns`
- tests/gui/test_source_selection_presenter.py L128: `for name, _r, _req, _a in presenter.state.columns`
- Plus any test that constructs 4-tuple column rows directly (to be discovered during Phase 4).
