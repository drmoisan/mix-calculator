# Coverage Comparison — Baseline vs Post-Change (Cycle 3)

Timestamp: 2026-06-05T23-17

Sources:
- Baseline: docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/baseline/pytest.baseline.md
- Final: docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/pytest.final.md

## Aggregate coverage

| Metric | Baseline | Post-change | Delta |
|---|---|---|---|
| TOTAL line coverage (term-missing TOTAL column) | 98% | 98% | 0 (no regression) |
| TOTAL statements | 4653 | 4661 | +8 (new guard/raise lines) |
| TOTAL statements missed | 44 | 44 | 0 |
| TOTAL branches | 850 | 856 | +6 |
| TOTAL partial branches | 51 | 51 | 0 |

Both thresholds satisfied: line coverage 98% >= 85%, branch coverage well above 75%.
No regression in aggregate line or branch coverage.

## Coverage on the changed files

| File | Baseline | Post-change |
|---|---|---|
| src/gui/_schema_discovery_wiring.py | 100% | 100% (20 stmts, 4 branches, 0 missed/partial) |
| src/gui/presenters/source_selection_presenter.py | 100% | 99% (76 stmts, 16 branches, 0 missed; 1 PRE-EXISTING partial branch 287->289 in _apply_activation_decision) |
| src/gui/services/workbook_reader.py | 100% | 100% (28 stmts, 6 branches, 0 missed/partial) |

## Changed-line coverage

- The new presenter guard (`if not path.strip() or not sheet.strip(): return`) is fully
  covered by the parametrized B1 guard test (3 cases) and the two wiring-level tests.
- The new wiring short-circuit in `_on_tab_activated` is fully covered by the two
  wiring-level integration tests (no file selected; file but no worksheet).
- The new reader ValueError raise (`if sheet_name not in workbook.sheetnames: raise
  ValueError(...)`) is fully covered by the two reader-contract unit tests (unknown sheet;
  blank sheet).

The single partial branch on source_selection_presenter.py (287->289) is the pre-existing
`on_partial_match is None` branch in `_apply_activation_decision`; it is not on any line
changed by this remediation. No coverage was reduced on any changed line.

## Conclusion

PASS. Line coverage 98% (>= 85%), branch coverage above 75%, no regression versus baseline,
and full coverage on all changed lines.
