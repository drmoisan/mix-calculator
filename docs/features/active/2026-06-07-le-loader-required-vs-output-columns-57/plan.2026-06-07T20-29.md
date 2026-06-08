# Plan — le-loader-required-vs-output-columns (Issue #57)

- Issue: #57
- Branch: fix/loader-header-row-detection (rides in PR #56)
- Work Mode: full-bug
- Spec (authoritative): docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/spec.md
- Issue + AC-1..AC-8: docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/issue.md
- Plan timestamp: 2026-06-07T20-29
- Feature folder (FEATURE): docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57
- Evidence root: docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence

**Fail-closed evidence rule:** Include explicit baseline artifact tasks, final-QA artifact tasks, and coverage-comparison tasks for the in-scope language (Python). If any required baseline artifact, QA artifact, or coverage-comparison artifact is missing or incomplete, the verdict must be BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Each evidence-producing task names its exact artifact path under `<FEATURE>/evidence/<kind>/`. Do not mark evidence-backed work complete without the artifact.

## Objective

Make the protected LE loader (`src/normalize_le.load_source` via
`src/_normalize_le_columns.resolve_le_columns`) require only the 23 must-have
source columns and treat `YTD/YTG` and source `Super Category` as
optional-by-name (located if present, tolerated if absent), mirroring the AOP
`load_aop` pattern. Parity for the standard `LE-8 + 4` source (with `YTD/YTG` +
`Super Category` present) is the top invariant: byte-identical output. No change
to `src/load_aop.py`, the schema loader, or the CLI surface.

## Locked design (implement exactly)

1. `src/_normalize_le_columns.py`
   - Add `REQUIRED_COLUMNS = TEXT_COLUMNS + [*MONTH_COLUMNS, "FY", *QUARTER_COLUMNS, "PPG"]` (the 23 must-have source columns).
   - Add `OPTIONAL_BY_NAME = ["YTD/YTG", "Super Category"]`.
   - Redefine `EXPECTED_COLUMNS = REQUIRED_COLUMNS` (required-only, matching the AOP module convention).
   - Update `__all__` to export `REQUIRED_COLUMNS` and `OPTIONAL_BY_NAME`.
   - Rewrite `resolve_le_columns`: locate KEY (as today) AND each `OPTIONAL_BY_NAME` column by normalized name (`src.etl_columns.normalize_name`; no fuzzy, no raise on absence); exclude located KEY + optionals from the `resolvable` list passed to `resolve_columns`; pass only `REQUIRED_COLUMNS` as the required set; build `selection` from `REQUIRED_COLUMNS` plus each located optional (mapped to its canonical name) plus KEY when present; warn about extras as today. Full docstring + intent comments per `.claude/rules/self-explanatory-code-commenting.md`.
2. `src/normalize_le.py` `load_source`
   - Update the select/rename block to build `columns_to_keep` from `REQUIRED_COLUMNS` plus the located optional and KEY columns carried in `selection` (mirror `src/load_aop.py:240-246`). `normalize()` and `validate_tieouts()` are NOT changed (they never read `YTD/YTG` or source `Super Category`; output `Super Category` is created from `PPG`).
3. Do NOT touch `src/load_aop.py` or the schema loader.

## Batch / file-cap policy

- Per-batch cap: 3 production files + 3 test files maximum.
- Production files in scope (2): `src/_normalize_le_columns.py`, `src/normalize_le.py`.
- Batch 1 (Phase 2): both production files + the `resolve_le_columns` unit tests (1 test file).
- Batch 2 (Phase 3): loader/integration/etl_columns test updates, split to respect the 3-test cap (`tests/test_normalize_le.py`, `tests/test_normalize_le_header.py`, `tests/test_etl_columns.py`).
- Every changed file must remain <= 500 lines; a guard task confirms `src/normalize_le.py` stays under after the `load_source` edit.

## AC coverage map

- AC-1 (YTD/YTG-less import): P2-T2, P3-T1, P3-T2
- AC-2 (Super Category-less import; output from PPG): P2-T2, P3-T1, P3-T2
- AC-3 (require only 23 must-have; YTD/YTG + Super Category optional): P2-T1, P2-T2, P2-T3
- AC-4 (parity; existing LE loader tests pass): P3-T2, P4-T4
- AC-5 (missing must-have raises naming it): P2-T3, P3-T1
- AC-6 (flat sheet -> TARGET_COLUMNS): P3-T2, P3-T3
- AC-7 (load_aop unchanged): P3-T4 (scope guard), P4-T4 (full suite)
- AC-8 (full toolchain + coverage + file-size): P0-T6..T9, P2-T4..T7, P3-T5..T9, P4 all

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record them in `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/phase0-instructions-read.md` with `Timestamp:`, `Policy Order:`, and the explicit list of files read. Policy order: `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md` (CLAUDE.md is harness-auto-loaded and is not a files-to-read item).
- [x] [P0-T2] Read the authoritative inputs and confirm scope in `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/phase0-inputs-read.md` (files: `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/spec.md`, `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/issue.md`, `src/_normalize_le_columns.py`, `src/normalize_le.py`, `src/load_aop.py`, `tests/le_fixtures.py`). Record `Timestamp:` and a one-line confirmation that Work Mode is `full-bug`.
- [x] [P0-T3] Capture current line counts of every file to edit by running `(Get-Content <file>).Count` for each of `src/normalize_le.py`, `src/_normalize_le_columns.py`, `tests/test_normalize_le.py`, `tests/test_etl_columns.py`, `tests/test_normalize_le_header.py`, `tests/le_fixtures.py`. Write actual measured numbers to `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-line-counts.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` listing each path and its current line count. Do not hardcode stale values.
- [x] [P0-T4] Grep every `EXPECTED_COLUMNS` importer/user across `tests/` (`tests/test_etl_columns.py`, `tests/test_load_aop.py`, `tests/test_load_skulu.py`) and `src/` and record each path + line in `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-expected-columns-usage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Confirm whether `tests/test_etl_columns.py` uses LE `EXPECTED_COLUMNS` as both the actual and the expected argument to `resolve_columns` (self-consistent under a 23-column redefinition).
- [x] [P0-T5] Determine the test target for `resolve_le_columns` unit tests by confirming no existing test file imports `resolve_le_columns` and no `tests/test_normalize_le_columns.py` exists (new-file vs extend decision). Record the decision in `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-test-target.md` with `Timestamp:`, `Command:` (the grep/glob used), `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T6] Capture Black baseline: run `poetry run black --check .` and write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T7] Capture Ruff baseline: run `poetry run ruff check .` and write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T8] Capture Pyright baseline: run `poetry run pyright` and write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).
- [x] [P0-T9] Capture Pytest + coverage baseline: run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-pytest-coverage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric headline line coverage % and branch coverage % (baseline values) and the passed/failed test counts.

### Phase 1 — Implementation Handoff

- [x] [P1-T1] Hand off the locked design above to the implementation engineer with the constraint that Phase 2 and Phase 3 batches respect the 3-production + 3-test per-batch cap, the 500-line file cap, and the parity invariant. Acceptance: implementer confirms scope is limited to `src/_normalize_le_columns.py`, `src/normalize_le.py`, and the named test files, and that `src/load_aop.py` and the schema loader are untouched. Record the handoff confirmation in `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/other/impl-handoff.md` with `Timestamp:`.

### Phase 2 — Batch 1: Production Changes and resolve_le_columns Unit Tests

- [x] [P2-T1] In `src/_normalize_le_columns.py`, add `REQUIRED_COLUMNS = TEXT_COLUMNS + [*MONTH_COLUMNS, "FY", *QUARTER_COLUMNS, "PPG"]` and `OPTIONAL_BY_NAME = ["YTD/YTG", "Super Category"]`, redefine `EXPECTED_COLUMNS = REQUIRED_COLUMNS`, and add both new constants to `__all__`. Acceptance: `REQUIRED_COLUMNS` has exactly 23 entries (5 text + 12 months + FY + 4 quarters + PPG), `OPTIONAL_BY_NAME == ["YTD/YTG", "Super Category"]`, `EXPECTED_COLUMNS` equals `REQUIRED_COLUMNS`, and `__all__` exports `REQUIRED_COLUMNS` and `OPTIONAL_BY_NAME`. (AC-3)
- [x] [P2-T2] In `src/_normalize_le_columns.py`, rewrite `resolve_le_columns` so it locates KEY and each `OPTIONAL_BY_NAME` column by normalized name (no fuzzy match, no raise on absence), excludes located KEY + optionals from the `resolvable` list passed to `resolve_columns`, passes only `REQUIRED_COLUMNS` as the required set, and builds `selection` from `REQUIRED_COLUMNS` plus each located optional (mapped to its canonical name) plus KEY when present, warning about extras as today. Update the docstring and intent comments per `.claude/rules/self-explanatory-code-commenting.md`. Acceptance: function returns `(selection, key_actual)`; for a full-column source `selection` maps every `REQUIRED_COLUMNS` entry plus `YTD/YTG`, `Super Category`, and (when present) KEY to their canonical names; absent optionals are not in `selection`. (AC-1, AC-2, AC-3)
- [x] [P2-T3] Create `tests/test_normalize_le_columns.py` with unit tests for `resolve_le_columns`: (a) `YTD/YTG` absent -> not required, not in selection; (b) source `Super Category` absent -> not required, not in selection; (c) both present -> located and carried (mapped to canonical names); (d) a required column absent (for example `PPG`) -> raises `ValueError` naming the missing column. All fixtures are in-memory column-name lists; no workbook, no temp files, no network. Acceptance: four tests pass and each asserts the specific behavior named. (AC-1, AC-2, AC-3, AC-5)
- [x] [P2-T4] Batch-1 gate — Black: run `poetry run black .` then `poetry run black --check .`; if files changed, restart this gate. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch1-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P2-T5] Batch-1 gate — Ruff: run `poetry run ruff check .` (zero errors; suppressions only per `.claude/rules/python-suppressions.md`). Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch1-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P2-T6] Batch-1 gate — Pyright: run `poetry run pyright` (zero errors). Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch1-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P2-T7] Batch-1 gate — Pytest + coverage: run `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch1-pytest-coverage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric line % and branch %. If any step changed files or failed, restart from P2-T4.

### Phase 3 — Batch 2: Loader Selection and Integration / etl_columns Test Updates

- [x] [P3-T1] In `src/normalize_le.py` `load_source`, update the select/rename block to build `columns_to_keep` from `REQUIRED_COLUMNS` plus the located optional and KEY columns carried in `selection` (mirror `src/load_aop.py:240-246`), instead of iterating the full former `EXPECTED_COLUMNS`. Import `REQUIRED_COLUMNS` from `src._normalize_le_columns` and add it to this module's `__all__` re-export. Do NOT change `normalize()` or `validate_tieouts()`. Also update the header-detection intent comment in `load_source` (currently `src/normalize_le.py:147-150`) so its token-count math matches the redefined 23-column `EXPECTED_COLUMNS`: it now derives `expected_tokens` from 23 required tokens (not 25), so `min_match=20` tolerates 3 absent/aliased columns (not 5). Comment-only update — do NOT change the `min_match=20` value or any other behavior (per `.claude/rules/self-explanatory-code-commenting.md`). Acceptance: `load_source` of a YTD/YTG-less or Super-Category-less source succeeds; a source missing a must-have column still raises a `ValueError` naming it; the header-detection comment reflects the 23-token set and `min_match=20`, and detection still selects index 2 for the standard fixture and index 0 for the flat fixture (verified by `tests/test_normalize_le_header.py`). (AC-1, AC-2, AC-5)
- [x] [P3-T2] Extend `tests/test_normalize_le.py`: add (a) `load_source` with `YTD/YTG` absent succeeds and the loaded frame lacks `YTD/YTG`; (b) `load_source` with source `Super Category` absent succeeds and `normalize()` output `Super Category == PPG`; (c) both absent -> `normalize()` produces all 26 `TARGET_COLUMNS`; (d) parity: full-column-source output is unchanged versus the standard fixture output. Use `build_workbook(..., header=<pruned header>)` to drop optional columns; no temp files. Confirm the existing `test_load_source_header_and_columns` (asserts `set(frame.columns) == set(SOURCE_COLUMNS)`) stays valid for the full-column fixture and update only if that assertion now requires the located-optionals form. Acceptance: the four new tests pass and the existing full-column assertion remains green. (AC-1, AC-2, AC-4, AC-6)
- [x] [P3-T3] Extend `tests/test_normalize_le_header.py`: add a test that an LE84Data-style flat sheet (header row index 0, no `YTD/YTG`, no `KEY`) imports and that `normalize()` of the loaded frame yields the full `TARGET_COLUMNS` set. Build the flat workbook in-memory via `build_workbook(rows, leading_rows=0, header=<flat header without YTD/YTG and without KEY>)`; no temp files. Acceptance: the flat-sheet import test passes and asserts `set(out.columns) == set(TARGET_COLUMNS)`. (AC-6)
- [x] [P3-T4] Update `tests/test_etl_columns.py` where it imports/uses LE `EXPECTED_COLUMNS` as both the actual and the expected argument to `resolve_columns` (now 23 columns): confirm each existing case (identity, reorder, fuzzy, missing-required, extra-column) still holds with the 23-column set, adjusting only fixtures that referenced now-optional columns. Do not change AOP/skulu cases. Acceptance: all `tests/test_etl_columns.py` cases pass with the redefined 23-column `EXPECTED_COLUMNS`; AOP and skulu importers of their own `EXPECTED_COLUMNS` are unaffected. (AC-4, AC-7)
- [x] [P3-T5] File-size guard (post-edit): run `(Get-Content src/normalize_le.py).Count` and `(Get-Content src/_normalize_le_columns.py).Count` and confirm each is <= 500 lines. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/file-size-guard.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` listing each changed file and its post-edit line count. (AC-8)
- [x] [P3-T6] Batch-2 gate — Black: run `poetry run black .` then `poetry run black --check .`; if files changed, restart. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch2-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P3-T7] Batch-2 gate — Ruff: run `poetry run ruff check .`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch2-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P3-T8] Batch-2 gate — Pyright: run `poetry run pyright`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch2-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P3-T9] Batch-2 gate — Pytest + coverage: run `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/batch2-pytest-coverage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric line % and branch %. If any step changed files or failed, restart from P3-T6.

### Phase 4 — Final QA Loop and Parity Verification

- [x] [P4-T1] Final Black: run `poetry run black --check .`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. If it reports changes needed, run `poetry run black .` and restart the final loop from P4-T1.
- [x] [P4-T2] Final Ruff: run `poetry run ruff check .`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Restart from P4-T1 on any change/failure.
- [x] [P4-T3] Final Pyright: run `poetry run pyright`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (zero errors required). Restart from P4-T1 on any change/failure.
- [x] [P4-T4] Parity and full-suite verification: run the full existing LE loader suite plus the AOP suite with coverage — `poetry run pytest tests/test_normalize_le.py tests/test_normalize_le_columns.py tests/test_normalize_le_header.py tests/test_normalize_le_io.py tests/test_normalize_le_totals.py tests/test_etl_columns.py tests/test_load_aop.py --cov --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/regression-testing/parity-le-aop-suite.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` confirming all LE loader tests pass (parity for the full-column source) and AOP tests pass unchanged. (AC-4, AC-7)
- [x] [P4-T5] Final Pytest + coverage (whole suite): run `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/final-pytest-coverage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric post-change line % and branch %. Restart from P4-T1 on any change/failure. (AC-8)
- [x] [P4-T6] Coverage delta / threshold verification: compare baseline (`baseline-pytest-coverage.md`) against post-change (`final-pytest-coverage.md`) and confirm line coverage >= 85%, branch coverage >= 75%, and no regression on changed lines (`src/_normalize_le_columns.py`, `src/normalize_le.py`). Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/coverage-delta.md` with `Timestamp:`, baseline line %/branch %, post-change line %/branch %, changed-code coverage, and PASS or REMEDIATION-REQUIRED. (AC-8)
- [x] [P4-T7] Final file-size guard: run `(Get-Content src/_normalize_le_columns.py).Count` and `(Get-Content src/normalize_le.py).Count` and confirm both <= 500 lines. Write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/final-file-size.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-8)
- [x] [P4-T8] Final AC reconciliation: confirm AC-1..AC-8 each map to passing evidence and write `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/other/ac-reconciliation.md` with `Timestamp:` and a per-AC status line citing the evidence artifact path for each.
