# Coverage Comparison vs Baseline (P15-T6)

Timestamp: 2026-06-05T13-51

## Figures

| Metric | Baseline (P0-T5) | Post-change (P15-T4) | Threshold | Status |
|---|---|---|---|---|
| Line coverage | 99.5% | 97.63% | >= 85% | PASS |
| Branch coverage | 96.6% | 93.63% | >= 75% | PASS |
| Tests | 842 passed | 922 passed | — | +80 |

## Changed-code coverage

The new/changed modules are well covered:

- `src/dtype_check.py` — 95% line.
- `src/gui/_schema_activation.py` — 100%.
- `src/gui/_schema_build_specs.py` — 100%.
- `src/gui/_schema_discovery_wiring.py` — 100%.
- `src/gui/presenters/_columns_tab_presenter.py` — 93% line.
- `src/gui/presenters/_key_tab_presenter.py` — 100%.
- `src/gui/presenters/_schema_builder_state.py` — 94% line.
- `src/gui/presenters/schema_builder_presenter.py` — 98% line.
- `src/gui/presenters/source_selection_presenter.py` — 99% line.
- `src/_schema_model_specs.py` — 100%.
- `src/gui/widgets/_dtype_check_widget.py` — 100%.
- `src/gui/widgets/_source_input_button_wiring.py` — 100%.
- `src/gui/widgets/_columns_tab_drag.py` / `_key_tab_drag.py` — drag widgets;
  the Qt mouse-move/drag-enter event handlers are exercised by added tests, with
  residual uncovered lines limited to defensive Qt-event guard branches.
- `src/gui/_columns_tab_protocol.py` / `_key_tab_protocol.py` — pure
  ``typing.Protocol`` declarations whose method bodies are ``...`` stubs; they
  carry no executable logic.

## Verdict

PASS. Both absolute thresholds (line >= 85%, branch >= 75%) hold. The small
decrease from the baseline percentages is attributable to newly-added Qt
drag-and-drop widget code (event-handler and protocol-stub lines that carry no
business logic), not to any regression in existing, previously-covered lines. The
feature's pure logic (model, serialization, migration, dtype check, presenters,
activation matching) is covered at 93–100%.
