# nrr-summary-mix-pipeline - Plan

- **Issue:** #15
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T20-40
- **Status:** Draft
- **Version:** 0.2
- **Work Mode:** minor-audit (small path)
- **Requirements source:** `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/issue.md` (sole source; `## Acceptance Criteria` AC1-AC10 is the minor-audit AC source). `spec.md` and `user-story.md` are not required and must not be present in the active folder.

## Required References

Policy is auto-loaded via `.claude/rules/`; this plan does not duplicate policy content. The reading order recorded in Phase 0 is: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`.

**All work must comply with these policies; do not duplicate their content here.**

## Evidence Locations (Canonical, Non-Overridable)

All evidence artifacts resolve under `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/evidence/<kind>/` per `evidence-and-timestamp-conventions`:

- Phase 0 policy read + baselines: `evidence/baseline/`
- Phase 2 final QC + regression results: `evidence/qa-gates/`
- End-to-end run evidence: `evidence/other/`

Timestamps use `yyyy-MM-ddTHH-mm`. Writing evidence to any `artifacts/...` path is a policy violation and is rejected.

## Scope (constrained small path)

Production-file budget (small):

- New pure builder: `src/mix_nrr_summary.py` (I/O-free; <= 500 lines).
- Pipeline integration edit: `src/mix_pipeline_run.py` (build `nrr_summary` in the runner and add it to the returned dict) and/or `src/mix_pipeline.py` (persist as the final derived table through `src/pandas_io.py`; `main` stays I/O-only).
- Classification: `quality-tiers.yml` (add `src/mix_nrr_summary.py: T2`).
- Documentation: `README.md` (document the appended `nrr_summary` table).

New test module: `tests/test_mix_nrr_summary.py` (fabricated values only).

Confidentiality: tests, fixtures, and docs use fabricated values only (for example `SKU-001`, `Category X`); never real source numbers, SKU descriptions, or category names. The `mix_3_customer["Customer Mix"]` column is read for the Mix Breakdown `Customer Mix` total (the pipeline's rename of the Excel `Mix_3_Customer[[#Totals],[Category Mix]]` reference); this mapping is preserved deliberately and documented in code (AC5).

## Implementation Plan (Atomic Tasks)

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read the policy files in required order (`CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`) and confirm the minor-audit precondition (only `issue.md` present in the active folder; no `spec.md`/`user-story.md`).
  - Acceptance: `evidence/baseline/phase0-instructions-read.md` exists with `Timestamp:`, `Policy Order:`, and an explicit list of files read; it records that `issue.md` contains a `## Acceptance Criteria` section (AC1-AC10) and that `spec.md`/`user-story.md` are absent.
- [x] [P0-T2] Capture the Black baseline by running `poetry run black --check .`.
  - Acceptance: `evidence/baseline/black-baseline.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run black --check .`, `EXIT_CODE:`, and `Output Summary:` (pass/fail and count of files that would be reformatted).
- [x] [P0-T3] Capture the Ruff baseline by running `poetry run ruff check .`.
  - Acceptance: `evidence/baseline/ruff-baseline.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run ruff check .`, `EXIT_CODE:`, and `Output Summary:` (error count).
- [x] [P0-T4] Capture the Pyright baseline by running `poetry run pyright`.
  - Acceptance: `evidence/baseline/pyright-baseline.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run pyright`, `EXIT_CODE:`, and `Output Summary:` (error/warning count).
- [x] [P0-T5] Capture the Pytest + coverage baseline by running `poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  - Acceptance: `evidence/baseline/pytest-baseline.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run pytest --cov --cov-branch --cov-report=term-missing`, `EXIT_CODE:`, and `Output Summary:` carrying numeric baseline line-coverage and branch-coverage headline values plus the passed/failed test counts.

### Phase 1 — Constrained Small-Path Implementation (delegated)

Single delegated handoff to the small-path implementation engineer. The engineer implements the full scope below; `main` stays I/O-only and the builder performs no I/O. The Phase 2 QC loop is the verification gate for this phase.

- [x] [P1-T1] Implement `src/mix_nrr_summary.py` as a pure, I/O-free builder that constructs the `nrr_summary` frame from the six input frames (`aop_vs_le`, `rate_impacts`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`, `mix_4_country`), mirroring sibling `src/mix_*` style, typing, and Google-style docstrings, and staying within the 500-line limit. The implementation must satisfy, with explicit AC traceability noted in code/docstrings:
  - **AC1** — module exposes a pure builder function over the six named frames; no I/O; <= 500 lines.
  - **AC2** — attribute-summary block: `Lbs`, `Gross Sales`, `Net-Revenue $` as `aop_vs_le` SUMIF-by-`Attribute` sums (`aop`=sum AOP, `le`=sum LE, `value`=sum Diff, `pct`=value/aop); derived `GS / Lb` and `Net Rev / Lb` (`aop`/`le` as ratios, `value`=le-aop, `pct`=value/aop); `All in TS%` (`aop`=1-NetRev.AOP/GrossSales.AOP, `le`=1-NetRev.LE/GrossSales.LE, `value`=(le-aop)*10000 basis points, no `pct`).
  - **AC3** — Net Revenue Realization block: `Volume Impact` (`value`=Lbs.Abs * NetRevPerLb.AOP) and `Price/Mix` (`value`=NetRev.Abs - VolumeImpact.value), each `pct`=value/NetRev.AOP.
  - **AC4** — Net Pricing Breakdown block: `Gross Pricing`, `OI Rate`, `Promo Rate`, `Non-trade Rate` as `rate_impacts` column totals of `Calc Gross Price Impact on Net`, `OI Rate Impact`, `Trade Rate Impact`, `Non-Trade Rate Impact`; `Total Net Pricing` as their sum; each `pct`=value/NetRev.AOP.
  - **AC5** — Mix Breakdown block: `SKU Mix`=sum `mix_1_sku["SKU Mix"]`, `Category Mix`=sum `mix_2_category["Category Mix"]`, `Customer Mix`=sum `mix_3_customer["Customer Mix"]` (with an inline code comment recording that this maps the Excel `Mix_3_Customer[[#Totals],[Category Mix]]` reference renamed by the pipeline), `Country Mix`=sum `mix_4_country["Country Mix"]`; `Total Mix` as their sum.
  - **AC6** — reconciliation block: `Price / Mix` build-up (`value`=Total Mix + Total Net Pricing; `pct`=%Total Mix + %Total Net Pricing) and the `Check` row = `"CHECK"` when `round(PriceMix_realization - PriceMix_buildup, 0) == 0` (computed independently for the NR$ and %NR comparisons) else `"ERROR"`.
  - Output schema follows the issue's recommended tidy long table (`section`, `metric`, `aop`, `le`, `value`, `pct`, `check`), one row per source-tab label in source order; the executor selects and pins the single chosen `check` representation.
  - Per-Lb and `%` divisions guard the zero-denominator path explicitly (fail-fast or `None`/`NaN` per the chosen convention), since tests exercise the zero path.
  - Acceptance: `src/mix_nrr_summary.py` exists, is import-clean, is pure (no `read_table`/`write_table`/`open`/`sqlite3`/`read_excel`), and is <= 500 lines.
- [x] [P1-T2] Integrate the builder into the orchestration: build `nrr_summary` from the existing derived frames in `src/mix_pipeline_run.py` (add it to the returned dict as the final derived table) and/or persist it as the final derived table in `src/mix_pipeline.py` through `src/pandas_io.write_table`; `main` performs no transform logic and the stdout summary lists `nrr_summary`; existing CLI exit semantics are unchanged (**AC7**).
  - Acceptance: `nrr_summary` is the final key in the persisted derived-tables mapping and is written via `src/pandas_io.py`; no I/O is added to the builder; `main` remains I/O-only.
- [x] [P1-T3] Create `tests/test_mix_nrr_summary.py` with deterministic Pytest unit tests using fabricated inputs only (no temp files, no network, no real source values): cover each block (attribute summary, realization, pricing, mix, reconciliation), the division-by-zero / empty-input edges of the per-Lb and `%` derivations, and the `Check == "ERROR"` divergence path (**AC8**). Tests pin the chosen `check` representation and assert the `Customer Mix` column-mapping behavior.
  - Acceptance: `tests/test_mix_nrr_summary.py` exists; all new tests pass; changed-code line coverage >= 85% and branch coverage >= 75% (verified numerically in Phase 2).
- [x] [P1-T4] Classify the new module in `quality-tiers.yml` by adding `src/mix_nrr_summary.py: T2` alongside the sibling transforms, and document the appended `nrr_summary` table in `README.md` (extend the derived-tables list/count to include `nrr_summary` as the final derived table) (**AC9** classification + docs).
  - Acceptance: `quality-tiers.yml` contains `src/mix_nrr_summary.py: T2`; `README.md` lists `nrr_summary` as the appended final derived table using only schema/fabricated examples.

### Phase 2 — Final QC Loop

Run the Python toolchain in order (format -> lint -> type-check -> test). If any step changes files or fails, restart from P2-T1 until a single clean pass completes. All tasks are unconditional; `SKIPPED` is not a valid completion outcome.

- [x] [P2-T1] Run `poetry run black .` and record the result.
  - Acceptance: `evidence/qa-gates/black-final.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run black .`, `EXIT_CODE:`, `Output Summary:` (files reformatted; if any file changed, the loop restarts at P2-T1).
- [x] [P2-T2] Run `poetry run ruff check .` and record the result.
  - Acceptance: `evidence/qa-gates/ruff-final.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run ruff check .`, `EXIT_CODE: 0`, `Output Summary:` (0 errors); any new suppression is pre-authorized per `.claude/rules/python-suppressions.md` or has explicit approval.
- [x] [P2-T3] Run `poetry run pyright` and record the result.
  - Acceptance: `evidence/qa-gates/pyright-final.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run pyright`, `EXIT_CODE: 0`, `Output Summary:` (0 errors, 0 warnings).
- [x] [P2-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` in coverage mode and record numeric post-change coverage (**AC8**, **AC9** toolchain).
  - Acceptance: `evidence/qa-gates/pytest-final.<timestamp>.md` exists with `Timestamp:`, `Command: poetry run pytest --cov --cov-branch --cov-report=term-missing`, `EXIT_CODE: 0`, `Output Summary:` carrying numeric post-change line-coverage and branch-coverage headline values and the passed test count.
- [x] [P2-T5] Verify coverage deltas and thresholds by comparing the Phase 0 baseline and Phase 2 post-change coverage and computing changed-code coverage for `src/mix_nrr_summary.py` and the integration edit.
  - Acceptance: `evidence/qa-gates/coverage-delta.<timestamp>.md` exists reporting baseline coverage, post-change coverage, and new/changed-code coverage; line coverage >= 85% and branch coverage >= 75% with no regression on changed lines. If thresholds are unmet, the outcome is remediation-required (not PASS).
- [x] [P2-T6] Run the end-to-end pipeline against the real workbook: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db`, confirm the `nrr_summary` table is written and that its internal `Check` is computed and reported accurately (**AC7**, **AC10**). Record evidence without exposing confidential source values (report the `Check` result and table presence/row count only; no source numerics, SKU descriptions, or category names). NOTE (2026-05-27, user Option A): AC10 was revised from "Check reconciles to CHECK" to "Check reflects the true reconciliation state". The end-to-end run writes `nrr_summary` (20 rows) and the `Check` reports `"ERROR"`, faithfully surfacing a pre-existing upstream issue #9 defect (`mix_2_category`/`mix_3_customer` mix-column totals do not tie out to the workbook); that defect is tracked as a separate follow-up bug and is out of scope here.
  - Acceptance: `evidence/other/e2e-run.<timestamp>.md` exists with `Timestamp:`, `Command:` (the exact command above), `EXIT_CODE: 0`, and `Output Summary:` confirming `nrr_summary` is the final table written, its row count, and the accurately reported `Check` result, with no confidential values disclosed.

## Reduced Audit (small path)

- [x] [P2-T7] Hand off to the small-audit reviewer for the reduced post-implementation audit. Reduced artifact checks: Phase 0 policy-read + four baseline artifacts present and schema-complete; Phase 2 final-QC artifacts (black/ruff/pyright/pytest) present with required fields and a single clean toolchain pass; coverage-delta artifact present with numeric thresholds met; end-to-end artifact present with `Check == "CHECK"`; AC1-AC10 traceable to plan tasks; no confidential values in any artifact, test, or doc.
  - Acceptance: reduced-audit verdict recorded; verdict is BLOCKED or INCOMPLETE (never PASS) if any required baseline, QC, coverage-delta, or end-to-end artifact is missing or incomplete, or if checklist state contradicts evidence on disk.

## Acceptance Criteria Traceability

- AC1 -> P1-T1 (pure builder, six frames, <= 500 lines)
- AC2 -> P1-T1 (attribute-summary block)
- AC3 -> P1-T1 (Net Revenue Realization block)
- AC4 -> P1-T1 (Net Pricing Breakdown block)
- AC5 -> P1-T1 (Mix Breakdown block + documented `Customer Mix` mapping)
- AC6 -> P1-T1 (reconciliation block + `Check`)
- AC7 -> P1-T2, P2-T6 (pipeline integration + persist + stdout)
- AC8 -> P1-T3, P2-T4, P2-T5 (deterministic tests + coverage thresholds)
- AC9 -> P1-T4, P2-T1..P2-T4 (classification, README, clean toolchain pass)
- AC10 -> P2-T6 (end-to-end run, `Check == "CHECK"`, confidentiality preserved)

## Test Plan

- Unit: `tests/test_mix_nrr_summary.py` — per-block coverage, per-Lb and `%` division-by-zero/empty-input edges, and the `Check == "ERROR"` divergence path; fabricated inputs only; AAA structure; no temp files or network.
- Integration / Manual CLI: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db` confirming `nrr_summary` is written as the final table and its `Check` reconciles.
- Coverage evidence:
  - Baseline: `evidence/baseline/pytest-baseline.<timestamp>.md`
  - Post-change: `evidence/qa-gates/pytest-final.<timestamp>.md`
  - Comparison: `evidence/qa-gates/coverage-delta.<timestamp>.md`

## Open Questions / Notes

- The executor selects one `check` representation (string in `value`/`pct` mirrored into `check`, or a single `check`-only field); the reconciliation logic itself is non-negotiable and tests pin the chosen representation.
- The `mix_3_customer["Customer Mix"]` read for the Mix Breakdown `Customer Mix` total is deliberate (the pipeline renamed the Excel tab's `Mix_3_Customer[[#Totals],[Category Mix]]` reference); preserved and documented in code per AC5.
