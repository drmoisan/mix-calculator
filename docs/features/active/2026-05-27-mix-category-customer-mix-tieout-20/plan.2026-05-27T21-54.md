# mix-category-customer-mix-tieout (Plan)

- **Issue:** #20
- **Parent (optional):** none
- **Owner:** drmoisan
- **Work Mode:** full-bug (remediation cycle)
- **Plan Timestamp (remediation):** 2026-05-27T22-40
- **Scope:** Remediate a single Blocking general-code-change finding by splitting `tests/test_mix_rollups.py` (562 lines) into cohesive sub-modules so every file is at or under 500 lines, with no change to test semantics, names, fixtures, assertions, or coverage. No production code change.
- **Source of remediation requirement:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/remediation-inputs.2026-05-27T22-34.md` (Finding 1, Blocking).

## Cohesive split design

Line counts are measured by `wc -l` semantics (equivalent to `(Get-Content $path).Count` in PowerShell), matching the upstream remediation-inputs Finding 1 measurement.

Option B from `remediation-inputs.2026-05-27T22-34.md` is selected because the six fixture helpers in the offending file are shared by tests landing on both sides of the split. Duplicating the helpers would violate the no-copy-paste principle in `.claude/rules/general-code-change.md` and would also push individual files closer to the 500-line limit again.

- `tests/_mix_rollups_fixtures.py` (new shared helper module, underscore-prefixed so pytest does not treat it as a test module). Contains exactly these helpers, copied byte-for-byte from `tests/test_mix_rollups.py` (lines 31-233 in the pre-split file):
  - `_f`
  - `_mix_base_rows`
  - `_mix_base_fixture`
  - `_rate_impacts_fixture`
  - `_single_scenario_mix_base_fixture`
  - `_unfiltered_group_lbs_le`
  Plus the necessary imports (`from __future__ import annotations`, `from typing import cast`, `import pandas as pd`).

- `tests/test_mix_rollups.py` (modified in place, no rename). Retains the rollup/layer/stage tests (no semantic change):
  - `test_build_mix_rollup_1_groups_by_customer_country_category`
  - `test_build_mix_rollup_4_returns_scalar_sum`
  - `test_build_mix_1_sku_produces_sku_mix_column`
  - `test_full_mix_chain_columns_and_fill_zero`
  - `test_mix_4_country_subtracts_scalar_rollup_4`
  - `test_build_mix_0_detail_composite_keys`
  - `test_build_mix_stage_keeps_only_nonzero_lbs_lines`
  - `test_rollup_tie_out_customer_layer_sum_matches_scalar`
  Imports `_f`, `_mix_base_fixture`, `_rate_impacts_fixture` from `tests._mix_rollups_fixtures`. The module docstring is retained, narrowed to describe only the layer/rollup/stage scope.

- `tests/test_mix_rollups_tieout.py` (new). Contains the AC8 four-layer tie-out / issue #20 regression tests (no semantic change). This file preserves the AC8 verification path:
  - `test_category_layer_retains_single_scenario_volume`
  - `test_customer_layer_retains_single_scenario_volume`
  - `test_layer_mix_equals_full_aggregation_minus_rollup`
  Imports `_f`, `_single_scenario_mix_base_fixture`, `_unfiltered_group_lbs_le` from `tests._mix_rollups_fixtures`, and the relevant builder symbols from `src.mix_rollups` / `src._mix_rollups_helpers`. Carries the original block comment that documents the single-scenario volume retention intent.

Estimated post-split line counts (each well under 500):

- `tests/_mix_rollups_fixtures.py`: approximately 210 lines.
- `tests/test_mix_rollups.py`: approximately 225 lines.
- `tests/test_mix_rollups_tieout.py`: approximately 155 lines.

No production code, spec, issue.md, audit, or policy file is touched. No test is deselected, skipped, weakened, renamed, or has any assertion changed. No new dependency is added. The cross-feature `tests/mix_bottomsup_fixtures.py` is not touched.

## Evidence locations (canonical)

All evidence for this remediation cycle is written under:

- Baselines: `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/remediation-baseline/`
- Final QA gates: `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/qa-gates/`
- Regression-testing (if any AC re-verification artifact is needed): `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/regression-testing/`

Any non-canonical evidence path supplied by a caller (for example `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, `artifacts/evidence/`) is rejected and replaced with the canonical path defined in `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. The override is recorded as `EVIDENCE_LOCATION_OVERRIDE_REJECTED:` in the affected artifact.

---

### Phase 0 — Policy read and remediation baseline capture

- [x] [P0-T1] Read `.claude/rules/general-code-change.md` (full file). Record under `evidence/remediation-baseline/phase0-instructions-read.2026-05-27T22-40.md` with `Timestamp:`, `Policy Order:` (1. CLAUDE.md, 2. general-code-change.md, 3. general-unit-test.md, 4. python.md, 5. python-suppressions.md, 6. self-explanatory-code-commenting.md, 7. quality-tiers.md, 8. tonality.md, 9. benchmark-baselines.md, 10. ci-workflows.md), and an explicit `Files Read:` list. Acceptance: the artifact exists with all three required fields and a literal quotation of the File Size Limit clause.

- [x] [P0-T2] Read `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/tonality.md`. Append the file list and any rule excerpts that constrain test-module placement (for example: "Organize tests to mirror code structure") to the same `evidence/remediation-baseline/phase0-instructions-read.2026-05-27T22-40.md`. Acceptance: every file path appears under `Files Read:`.

- [x] [P0-T3] Capture the pre-remediation file size of the offending file using `wc -l` semantics (so the measurement matches the upstream remediation-inputs Finding 1 value of 562 lines). Command: `pwsh -NoProfile -Command "(Get-Content tests/test_mix_rollups.py).Count"`. Write the output to `evidence/remediation-baseline/file-size-baseline.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (must record the integer line count and the policy threshold 500). Acceptance: artifact present with all four fields; `Output Summary:` records 562 as the current line count.

- [x] [P0-T4] Capture baseline Black status. Command: `env -u VIRTUAL_ENV poetry run black --check tests/test_mix_rollups.py`. Write to `evidence/remediation-baseline/black-baseline.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (state pass/fail and any reformat candidates). Acceptance: artifact present with all four fields.

- [x] [P0-T5] Capture baseline Ruff status. Command: `env -u VIRTUAL_ENV poetry run ruff check tests/test_mix_rollups.py`. Write to `evidence/remediation-baseline/ruff-baseline.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (state error count). Acceptance: artifact present with all four fields.

- [x] [P0-T6] Capture baseline Pyright status against the same file. Command: `env -u VIRTUAL_ENV poetry run pyright tests/test_mix_rollups.py`. Write to `evidence/remediation-baseline/pyright-baseline.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (state error/warning count). Acceptance: artifact present with all four fields.

- [x] [P0-T7] Capture baseline Pytest pass/coverage state with coverage enabled. Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing`. Write to `evidence/remediation-baseline/pytest-baseline.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording: total tests collected, passed count (must equal 220 per remediation-inputs), `tests/test_mix_rollups.py` test count, headline TOTAL line and branch coverage, and per-file line+branch coverage for `src/mix_rollups.py`, `src/_mix_rollups_helpers.py`, and `src/mix_pipeline_run.py`. Acceptance: artifact present with all four fields and the four required coverage numbers (TOTAL line, TOTAL branch, three per-file rows).

- [x] [P0-T8] Capture an enumeration of every test function in `tests/test_mix_rollups.py` for post-split parity. Command: `pwsh -NoProfile -Command "Select-String -Path tests/test_mix_rollups.py -Pattern '^def (test_[A-Za-z0-9_]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value }"`. Write to `evidence/remediation-baseline/test-inventory-baseline.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (the literal list of 11 test function names). Acceptance: artifact present; the list contains exactly the 11 `test_*` names enumerated in the cohesive split design above.

---

### Phase 1 — Cohesive test-file split

- [x] [P1-T1] Create `tests/_mix_rollups_fixtures.py` containing the six shared helpers (`_f`, `_mix_base_rows`, `_mix_base_fixture`, `_rate_impacts_fixture`, `_single_scenario_mix_base_fixture`, `_unfiltered_group_lbs_le`) copied byte-for-byte from `tests/test_mix_rollups.py` lines 31-233. Module docstring states purpose: "Shared Mix_Base / rate-impacts fixture helpers for the mix-rollup test suite. Imported by `tests/test_mix_rollups.py` and `tests/test_mix_rollups_tieout.py`; not itself a pytest module." Required imports: `from __future__ import annotations`, `from typing import cast`, `import pandas as pd`. Acceptance: file exists; `pwsh -NoProfile -Command "(Get-Content tests/_mix_rollups_fixtures.py).Count"` returns a value <= 500 (using `wc -l` semantics); every helper name listed above is present and its function body is identical to the original (verified by diff).

- [x] [P1-T2] Create `tests/test_mix_rollups_tieout.py` containing exactly three test functions copied byte-for-byte from `tests/test_mix_rollups.py` lines 423-562: `test_category_layer_retains_single_scenario_volume`, `test_customer_layer_retains_single_scenario_volume`, `test_layer_mix_equals_full_aggregation_minus_rollup`. Module docstring states purpose: "AC8 four-layer tie-out and issue #20 single-scenario-volume regression tests. Verifies the corrected coarser layers aggregate the unfiltered Mix_Base at their own granularity." Imports: `from __future__ import annotations`; `import pandas as pd`; `from src._mix_rollups_helpers import build_mix_stage`; `from src.mix_rollups import build_mix_2_category, build_mix_3_customer`; `from tests._mix_rollups_fixtures import _f, _single_scenario_mix_base_fixture, _unfiltered_group_lbs_le`. The original explanatory block comment about single-scenario volume retention is carried over verbatim above the first test. Acceptance: file exists; `(Get-Content tests/test_mix_rollups_tieout.py).Count` returns a value <= 500 (using `wc -l` semantics); each test function body matches the original byte-for-byte (verified by diff against pre-split snapshot).

- [x] [P1-T3] Update `tests/test_mix_rollups.py` in place to remove the six shared helper definitions and the three tie-out tests, leaving only the rollup/layer/stage tests (`test_build_mix_rollup_1_groups_by_customer_country_category`, `test_build_mix_rollup_4_returns_scalar_sum`, `test_build_mix_1_sku_produces_sku_mix_column`, `test_full_mix_chain_columns_and_fill_zero`, `test_mix_4_country_subtracts_scalar_rollup_4`, `test_build_mix_0_detail_composite_keys`, `test_build_mix_stage_keeps_only_nonzero_lbs_lines`, `test_rollup_tie_out_customer_layer_sum_matches_scalar`). Replace the helper definitions with `from tests._mix_rollups_fixtures import _f, _mix_base_fixture, _rate_impacts_fixture`. Retain `from src._mix_rollups_helpers import build_mix_stage` and the `from src.mix_rollups import ...` block (drop unused symbols only if Ruff F401 flags them). Narrow the module docstring to describe only the layer/rollup/stage scope; do not change any test function name, signature, or assertion. Acceptance: `(Get-Content tests/test_mix_rollups.py).Count` returns a value <= 500 (using `wc -l` semantics); `pwsh -NoProfile -Command "Select-String -Path tests/test_mix_rollups.py -Pattern '^def (test_[A-Za-z0-9_]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value }"` lists exactly the eight test names enumerated for this file.

- [x] [P1-T4] Verify post-split test inventory parity. Command: `pwsh -NoProfile -Command "Select-String -Path tests/test_mix_rollups.py,tests/test_mix_rollups_tieout.py -Pattern '^def (test_[A-Za-z0-9_]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object"`. Write to `evidence/qa-gates/test-inventory-postsplit.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (the literal sorted list of 11 test names). Acceptance: the sorted post-split list is set-equal to the baseline list captured in P0-T8 (no test added, removed, or renamed).

- [x] [P1-T5] Verify the three resulting files all sit at or under the 500-line policy threshold using `wc -l` semantics. Command: `pwsh -NoProfile -Command "Get-ChildItem tests/test_mix_rollups.py,tests/test_mix_rollups_tieout.py,tests/_mix_rollups_fixtures.py | ForEach-Object { [pscustomobject]@{ Path=$_.FullName; Lines=(Get-Content $_.FullName).Count } }"`. Write to `evidence/qa-gates/file-size-postsplit.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (three rows: file path + line count, plus a `Threshold: 500` line and a pass/fail verdict). Acceptance: every recorded line count is <= 500.

---

### Phase 2 — Mandatory Python toolchain loop (restart on any file change)

The loop runs in the fixed order Black -> Ruff -> Pyright -> Pytest. If any step fails or modifies files, restart from P2-T1. The loop terminates only when all four steps complete in a single clean pass. Final-QC tasks below are unconditional: each command MUST be executed and recorded; `EXIT_CODE: SKIPPED` is not a valid completion.

- [x] [P2-T1] Run Black formatter check across the three affected files. Command: `env -u VIRTUAL_ENV poetry run black --check tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py`. Write to `evidence/qa-gates/black-final.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (must include the literal "3 files would be left unchanged" or equivalent). Acceptance: `EXIT_CODE: 0`. If `EXIT_CODE` is nonzero or Black reports `would reformat`, run `env -u VIRTUAL_ENV poetry run black tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py` to apply formatting and then restart the loop from P2-T1.

- [x] [P2-T2] Run Ruff linter across the three affected files plus the whole `tests/` tree for cross-import sanity. Command: `env -u VIRTUAL_ENV poetry run ruff check tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py`. Write to `evidence/qa-gates/ruff-final.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (must state "All checks passed!" or list specific findings). Acceptance: `EXIT_CODE: 0` and zero findings. No new `# noqa` suppression may be introduced; if any Ruff finding requires a code change, restart the loop from P2-T1. Suppressions are bounded by `.claude/rules/python-suppressions.md` and require an unused-imports/structural fix instead.

- [x] [P2-T3] Run Pyright type checker across the three affected files. Command: `env -u VIRTUAL_ENV poetry run pyright tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py`. Write to `evidence/qa-gates/pyright-final.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (must record "0 errors, 0 warnings, 0 informations" or the specific counts). Acceptance: zero errors and zero warnings against the changed files. If any new diagnostic appears, restart the loop from P2-T1.

- [x] [P2-T4] Run the full Pytest suite with coverage on `src/`. Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing`. Write to `evidence/qa-gates/pytest-final.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (must record total tests collected, passed/failed/skipped counts, and TOTAL line and branch coverage percentages). Acceptance: `EXIT_CODE: 0`; total passed == 220 (matching the baseline in `remediation-inputs.2026-05-27T22-34.md`); zero failed; zero deselected; zero skipped beyond what the baseline already reported.

- [x] [P2-T5] Verify coverage on the three production files most relevant to issue #20 is preserved (>= 85% line / >= 75% branch per `.claude/rules/quality-tiers.md`, and matches the baseline 100/100 reported in `remediation-inputs.2026-05-27T22-34.md`). Source: the term-missing coverage block in `evidence/qa-gates/pytest-final.2026-05-27T22-40.md`. Write to `evidence/qa-gates/coverage-delta.2026-05-27T22-40.md` with `Timestamp:`, `Command:` (the same `pytest --cov=...` invocation), `EXIT_CODE:` (mirroring P2-T4), and `Output Summary:` listing for each of `src/mix_rollups.py`, `src/_mix_rollups_helpers.py`, `src/mix_pipeline_run.py`: baseline line%/branch% (from P0-T7), post-split line%/branch% (from P2-T4), and a `Delta:` row stating "no regression on changed lines" (no `src/**` lines changed in this remediation). Acceptance: every post-split coverage value is >= the baseline value captured in P0-T7; the artifact records the explicit no-regression statement and the policy thresholds.

- [x] [P2-T6] Re-verify the file-size policy compliance after the toolchain loop terminates clean (formatters may have shifted line counts) using `wc -l` semantics. Command: `pwsh -NoProfile -Command "Get-ChildItem tests/test_mix_rollups.py,tests/test_mix_rollups_tieout.py,tests/_mix_rollups_fixtures.py | ForEach-Object { [pscustomobject]@{ Path=$_.FullName; Lines=(Get-Content $_.FullName).Count } }"`. Append to `evidence/qa-gates/file-size-postsplit.2026-05-27T22-40.md` under a `## Post-Toolchain Verification` section, or write a sibling `evidence/qa-gates/file-size-final.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (three rows). Acceptance: every recorded line count remains <= 500.

- [x] [P2-T7] Verify no production code (`src/**`), no spec, no issue.md, and no `.claude/rules/**` file was touched in this remediation. Command: `pwsh -NoProfile -Command "git diff --name-only main...HEAD"`. Write to `evidence/qa-gates/scope-guard.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (the changed-files list). Acceptance: every changed path is one of `tests/test_mix_rollups.py`, `tests/test_mix_rollups_tieout.py`, `tests/_mix_rollups_fixtures.py`, `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/**`; no `src/**`, no `spec.md`, no `issue.md`, and no `.claude/rules/**` appears in the list.

- [x] [P2-T8] Confirm the AC8 four-layer tie-out verification path is preserved by re-running only the tie-out module under coverage. Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rollups_tieout.py -v`. Write to `evidence/regression-testing/ac8-tieout-postsplit.2026-05-27T22-40.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (must list the three tie-out test names as `PASSED`). Acceptance: `EXIT_CODE: 0`; all three tests pass; no test is deselected, marked xfail, or skipped.

---

## Out-of-scope (explicit)

The following are explicitly out of scope for this remediation cycle and MUST NOT be changed:

- Any file under `src/**`.
- `spec.md`, `issue.md`, `user-story.md` (if present), any audit document.
- Any policy document under `.claude/rules/**` or `.github/instructions/**`.
- The cross-feature fixture file `tests/mix_bottomsup_fixtures.py`.
- Any other test module in `tests/**` besides the three files enumerated in Phase 1.
- Any dependency addition or removal.

## Completion criteria

Remediation is complete when:

1. `tests/test_mix_rollups.py`, `tests/test_mix_rollups_tieout.py`, and `tests/_mix_rollups_fixtures.py` are each at or under 500 lines.
2. The post-split test inventory is set-equal to the pre-split inventory (no test added, removed, renamed, deselected, or skipped).
3. Black, Ruff, and Pyright produce zero findings against the three affected files in a single clean toolchain pass.
4. Pytest reports 220 passed, 0 failed, 0 skipped, with TOTAL line >= 85% and branch >= 75% and the three issue-#20 production files at >= their baseline coverage.
5. No `src/**`, spec, issue.md, or policy file is modified.
6. Every Phase 0, Phase 1, and Phase 2 task artifact exists at the canonical evidence path with all required schema fields populated.
