# Coverage Delta — Issue #29

Timestamp: 2026-05-29T00-00
Baseline source: `evidence/baseline/baseline-pytest.2026-05-29T00-00.md` (P0-T6)
Post-change source: `evidence/qa-gates/final-pytest.2026-05-29T00-00.md` (P5-T4)

| Scope                | Baseline line% | Post-change line% | Baseline branch% | Post-change branch% |
| -------------------- | -------------- | ----------------- | ---------------- | ------------------- |
| TOTAL                | 99% (1940/1954) | 99% (1970/1985)   | 99.3% (294/296)  | ~99.3% (298/300)    |
| `src/build_exe.py`   | n/a (file did not exist) | 97% (30/31) | n/a              | 100% (4/4)          |

Decision rule:
- PASS iff TOTAL coverage did not regress AND `src/build_exe.py` line% >= 85 AND branch% >= 75.

Decision: **PASS**.
- TOTAL line coverage stayed at 99% (no regression: absolute miss count grew from 14 to 15
  because the new module contributes one unreachable-in-tests line at `_dist_nuitka_exists`,
  but the rounded TOTAL percent is unchanged).
- TOTAL branch coverage stayed at 99% (no regression: partials remained at 2 of an expanded
  branch denominator).
- `src/build_exe.py` line coverage 97% (>= 85% threshold satisfied).
- `src/build_exe.py` branch coverage 100% (>= 75% threshold satisfied).
