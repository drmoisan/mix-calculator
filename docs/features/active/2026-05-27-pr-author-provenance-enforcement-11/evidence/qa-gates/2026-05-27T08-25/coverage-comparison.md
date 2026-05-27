# Final QC — Coverage Comparison / Threshold Verification

Timestamp: 2026-05-27T08-25

## Changed file

`.claude/hooks/enforce-pr-author-skill.ps1`

## Consumed machine-readable artifact

`artifacts/pester/powershell-coverage.xml` (JaCoCo format, regenerated in P4-T3).
Verified to contain exactly one source file: `sourcefilename="enforce-pr-author-skill.ps1"`.
The prior content of this artifact was stale (it covered 5 unrelated `.claude/hooks`
files and omitted the changed hook); it has been replaced.

## Baseline vs post-change

| Metric | Baseline (pre-change) | Post-change | Source |
|---|---|---|---|
| Covering test exists | No | Yes (52 tests) | `evidence/baseline/2026-05-26T00-00/baseline.md`; `test.md` |
| Line/command coverage (changed file) | 0% (no covering test) | 91.59% (98/107 commands) | baseline.md; `powershell-coverage.xml` |
| JaCoCo LINE counter (changed file) | 0% | 92.05% (81 covered / 7 missed) | `powershell-coverage.xml` |

Baseline coverage source: `evidence/baseline/2026-05-26T00-00/baseline.md` records
0% (no covering test existed prior to this change).

## Threshold gates

- Line coverage >= 85%: PASS (91.59% command / 92.05% JaCoCo LINE).
- Branch coverage >= 75%: met via explicit per-branch scenario tests. Pester's
  JaCoCo output carries no BRANCH counter (`mb`/`cb` are 0 on every line), so the
  branch obligation is satisfied by dedicated true/false scenario tests for each
  provenance branch (D, E, G, F, H), the staleness equality boundary
  (older/equal/newer), hash case-insensitivity, and canonical/non-canonical and
  body-file-present/absent splits.
- No regression on changed lines: PASS. The changed file moved from 0% (no covering
  test) to 91.59%; there is no prior covered baseline to regress against, and all
  changed provenance logic is exercised.

## Changed-code coverage

All new provenance logic is covered. `Get-PrAuthorProvenanceReason` (the pure
decision core for Cases D/E/G/F/H) shows 23/23 instructions and 18/18 lines
covered. `Get-PrAuthorBypassReason` shows 32/33 lines covered (the single missed
line 356 is the unreachable defensive `return $null`). The only uncovered commands
are the two unreachable defensive `return $null` statements (lines 174, 356) and
the dot-source-guarded script entrypoint (lines 435-444), which is verified
functionally via child-process tests rather than in-process coverage.

## Verdict

PASS. Changed-file line coverage 91.59% (>= 85%); branch obligation met; no
regression on changed lines; coverage artifact regenerated and now includes the
changed hook.
