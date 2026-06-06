# Fail-Before — Integration Gap (Remediation Cycle 1)

Timestamp: 2026-06-05T20-28

This artifact establishes the fail-before signal for the integrated tests added in
Phases 1-5. At cycle entry, the orphaned widget/presenter/provider modules exist
and are unit-tested in isolation but have no production caller reachable from the
opened `SchemaBuilderDialog` or `build_application`.

SearchScope: src/ (production source tree only; tests/ excluded)

SearchPatterns:
- `ColumnsTabWidget` (R1 production usage)
- `KeyTabWidget` (R2 production usage)
- `DerivedFormulaDialog` (R3 production usage)
- `BuildSpecProvider` (R4 production instantiation)
- `on_partial_match=` (R6 production call site)
- `\.new_from_template\(` (R5 production call site)

SearchResult (production callers at cycle entry):
- `ColumnsTabWidget`: only its own definition in `src/gui/widgets/_columns_tab_drag.py`. No import/construction by `_schema_builder_tabs.py` or `schema_builder_dialog.py`. ZERO production callers.
- `KeyTabWidget`: only its own definition in `src/gui/widgets/_key_tab_drag.py`. ZERO production callers.
- `DerivedFormulaDialog`: only its own `__all__` entry and class def in `src/gui/widgets/_derived_formula_dialog.py`. No button or open path wires it. ZERO production callers.
- `BuildSpecProvider`: only the Protocol definition in `src/gui/_schema_build_specs.py` and a `None`-default typed parameter in `src/gui/_schema_wiring.py` (L336). No concrete provider is instantiated anywhere in `src/`. ZERO production instantiations.
- `on_partial_match=`: ZERO matches in `src/`. The three `SourceSelectionPresenter(...)` constructions do not pass the callback.
- `.new_from_template(`: ZERO matches in `src/`. The presenter method exists but has no production caller.

Conclusion: the integration seams are absent from the live composition root and
dialog at cycle entry. The integrated tests in Phases 1-5 (P1-T6, P2-T5, P3-T4,
P4-T5, P5-T3, P5-T6) would fail against the current head, satisfying the
fail-before requirement.
