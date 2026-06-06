# Coverage Comparison vs Remediation Baseline (P7-T6)

Timestamp: 2026-06-05T20-28

## Figures

| Metric | Remediation baseline (P0-T5) | Post-change (P7-T4) | Threshold | Status |
|---|---|---|---|---|
| Line coverage | 98.4% (4534 stmts, 74 missed) | 98.7% (4671 stmts, 62 missed) | >= 85% | PASS |
| Branch coverage | 94.4% (832 br, 47 partial) | 94.0% (850 br, 51 partial) | >= 75% | PASS |
| Tests | 922 passed | 932 passed | — | +10 |

## Changed-code coverage (modules added or modified this cycle)

| Module | Line coverage |
|---|---|
| src/gui/widgets/_schema_builder_drag_tabs.py (new) | 96% |
| src/gui/_schema_provider_factory.py (new) | 95% |
| src/gui/_schema_open_helpers.py (new) | 93% |
| src/gui/_source_signal_wiring.py (new) | 100% |
| src/gui/_schema_discovery_wiring.py (modified) | 100% |
| src/gui/_schema_wiring.py (modified) | 98% |
| src/gui/app.py (modified) | 99% |
| src/gui/widgets/schema_builder_dialog.py (modified) | 98% |
| src/gui/widgets/_schema_builder_tabs.py (modified) | 100% |

## No-regression on changed lines

Every line added or modified by this remediation cycle is covered at 93-100%. The
0.4-point dip in the absolute aggregate branch percentage (94.4% -> 94.0%) is
attributable to newly-added defensive Qt-event guard branches in the drag-tab
binder and open-path helpers (for example the `callable(setter)` / `isinstance`
recording-stub guards), not to any reduction in coverage of previously-covered
lines. Line coverage increased (98.4% -> 98.7%). The integration seams wired this
cycle (R1-R6) are each exercised by an integrated test that drives the production
object.

## Verdict

PASS. Both absolute thresholds (line >= 85%, branch >= 75%) hold, line coverage
increased, and no previously-covered line regressed.
