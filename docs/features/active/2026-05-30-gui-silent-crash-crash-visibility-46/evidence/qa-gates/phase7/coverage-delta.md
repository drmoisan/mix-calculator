# Phase 7 — Coverage Delta (Baseline vs Post-Change)

Timestamp: 2026-05-30T23-30

## Per-file coverage delta

| File | Baseline Stmts | Post Stmts | Baseline Line % | Post Line % | Baseline Branch % | Post Branch % | Verdict |
|---|---|---|---|---|---|---|---|
| src/gui/_crash_handler.py | n/a (new) | 99 | n/a | 88% | n/a | 100% (8/8) | PASS — new file; line 88% > 85%; branch 100% > 75% |
| src/gui/runners.py | 32 | 46 | 66% | 100% | 0/0 | n/a | PASS — line went from 66% to 100%; no regression; new `_RunnerReceiver` lines fully covered |
| src/gui/workers/pipeline_worker.py | 22 | 24 | 100% | 100% | 0/0 | 100% (2/2) | PASS — added 2 statements (KeyboardInterrupt/SystemExit re-raise + exc_info=True); new branch coverage 100% |
| src/gui/app.py | 135 | 138 | 99% | 99% | 12/12 (1 partial) | 12/12 (1 partial) | PASS — no regression; 3 added statements (import + installer call block) fully covered by new composition-root test |

## Totals delta

- Baseline: 3533 stmts, 31 missed, 650 branches, 23 partial, total 99%.
- Post-change: 3651 stmts, 33 missed, 660 branches, 23 partial, total 99%.
- Net statement growth: +118 (all in `_crash_handler.py`). Net missed-line growth: +2 (within `_crash_handler.py`, in uninvoked hook closures and `_append_traceback`).
- Net branch growth: +10 (all in `_crash_handler.py`). Net partial growth: 0.
- Coverage on unchanged files: no regressions observed.

## AC-10 verdict

PASS. Changed-line coverage on the four touched files meets the >= 85% line / >= 75% branch thresholds. Coverage on unchanged files does not regress. AC-10 satisfied.
