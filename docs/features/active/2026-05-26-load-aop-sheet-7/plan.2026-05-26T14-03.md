# 2026-05-26-load-aop-sheet - Plan

- **Issue:** #7
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-26T14-03
- **Status:** Draft
- **Version:** 0.2
- **Work Mode:** full-feature

## Required References

- General Code Change Policy: `.claude/rules/general-code-change.md`
- General Unit Test Policy: `.claude/rules/general-unit-test.md`
- Python Code Standards: `.claude/rules/python.md`
- Python Suppression Policy: `.claude/rules/python-suppressions.md`
- Code Commenting and Docstring Policy: `.claude/rules/self-explanatory-code-commenting.md`
- Module Rigor Tiers: `.claude/rules/quality-tiers.md`
- Tonality Policy: `.claude/rules/tonality.md`

**All work must comply with these policies; do not duplicate their content here.**

## Authoritative Source Documents

- Spec: `docs/features/active/2026-05-26-load-aop-sheet-7/spec.md`
- Issue / acceptance criteria: `docs/features/active/2026-05-26-load-aop-sheet-7/issue.md`
- User story: `docs/features/active/2026-05-26-load-aop-sheet-7/user-story.md`
- Research reference (signatures, touch-points): `artifacts/research/2026-05-26-load-aop-sheet-7.md`

## Evidence Location Invariant

All evidence artifacts MUST be written under the canonical feature evidence root:
`docs/features/active/2026-05-26-load-aop-sheet-7/evidence/<kind>/` where `<kind>` is one of
`baseline`, `qa-gates`, `regression-testing`, `issue-updates`, `other`. Timestamps use
`yyyy-MM-ddTHH-mm`. Writing to `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`,
or any other non-canonical path is a policy violation.

## Toolchain Contract (every code/test phase)

Run in this exact order and restart from step 1 if any step fails or changes files; do not stop
until all four complete without error in a single pass:

1. `poetry run black .`
2. `poetry run ruff check .`
3. `poetry run pyright`
4. `poetry run pytest --cov --cov-branch --cov-report=term-missing`

Coverage thresholds are uniform across tiers: line >= 85%, branch >= 75%; no regression on changed
lines. Route unknown-typed pandas/openpyxl members through `src/pandas_io.py`
(`read_excel_sheet`, `write_table`); do not add Pyright suppressions. Any `# noqa`/`# type: ignore`
must match a pre-authorized pattern in `.claude/rules/python-suppressions.md`. No file may exceed
500 lines. No new third-party dependency may be added. All classes and functions require docstrings;
loops, comprehensions, branches, and multi-step blocks require intent comments per the commenting
policy.

---

## Implementation Plan (Atomic Tasks)

### Phase 0 — Compliance, Context, and Baseline Capture

- [x] [P0-T1] Read the repository policy files in precedence order and record the read in a Phase 0 evidence artifact.
  - Files to read (in order): `CLAUDE.md`; `.claude/rules/general-code-change.md`; `.claude/rules/general-unit-test.md`; `.claude/rules/python.md`; `.claude/rules/python-suppressions.md`; `.claude/rules/self-explanatory-code-commenting.md`; `.claude/rules/quality-tiers.md`; `.claude/rules/tonality.md`.
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/baseline/phase0-instructions-read.2026-05-26T14-03.md` exists and contains `Timestamp:`, `Policy Order:`, and the explicit list of files read.

- [x] [P0-T2] Capture the baseline Black formatting state on the unmodified tree.
  - Command: `poetry run black --check .`
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/baseline/black-check.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail and count of files that would be reformatted).

- [x] [P0-T3] Capture the baseline Ruff lint state on the unmodified tree.
  - Command: `poetry run ruff check .`
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/baseline/ruff-check.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail and error count).

- [x] [P0-T4] Capture the baseline Pyright type-check state on the unmodified tree.
  - Command: `poetry run pyright`
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/baseline/pyright.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (error/warning counts).

- [x] [P0-T5] Capture the baseline Pytest result and coverage headline on the unmodified tree.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/baseline/pytest-cov.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording numeric baseline line coverage % and branch coverage % plus passed/failed counts.

### Phase 1 — Neutral Rename, `fill_blank_totals` Generalization, LE-Green Gate

This phase contains no AOP code. The LE suite MUST be green at the phase boundary before any AOP
code is added in Phase 2.

- [x] [P1-T1] Rename `src/le_columns.py` to `src/etl_columns.py` and update its module docstring `:mod:` reference from `src.le_columns` to `src.etl_columns`.
  - Touches: `src/le_columns.py` (delete), `src/etl_columns.py` (create with renamed content).
  - Acceptance: `src/etl_columns.py` exists with identical function bodies; `src/le_columns.py` does not exist; no behavior change to `normalize_name`/`resolve_columns`.

- [x] [P1-T2] Rename `src/le_key.py` to `src/etl_key.py` and update its module docstring `:mod:` reference and the `logging.getLogger(__name__)` logger name now resolving to `src.etl_key`.
  - Touches: `src/le_key.py` (delete), `src/etl_key.py` (create with renamed content).
  - Acceptance: `src/etl_key.py` exists with identical function bodies including `coerce_sku`, `rebuild_key`, `decide_key_action`, `resolve_key`; `src/le_key.py` does not exist; logger name is `src.etl_key`.

- [x] [P1-T3] Rename `src/le_totals.py` to `src/etl_totals.py` and update its module docstring to neutral wording (ETL totals, not LE-specific).
  - Touches: `src/le_totals.py` (delete), `src/etl_totals.py` (create with renamed content).
  - Acceptance: `src/etl_totals.py` exists with `fill_blank_totals` and `total_vs_months_violations`; `src/le_totals.py` does not exist.

- [x] [P1-T4] Update the three leaf imports in `src/normalize_le.py` lines 33-35 to `src.etl_columns`, `src.etl_key`, `src.etl_totals`, and update the inline doc comment at line 43 that references `src.le_columns`/`src.le_key` to the new names.
  - Touches: `src/normalize_le.py`.
  - Acceptance: `src/normalize_le.py` imports only the `etl_*` modules; no remaining `le_columns`/`le_key`/`le_totals` reference in the file.

- [x] [P1-T5] Generalize `fill_blank_totals` in `src/etl_totals.py` to the signature `fill_blank_totals(frame: pd.DataFrame, totals_to_months: dict[str, list[str]]) -> pd.DataFrame`, filling only blank/NaN total cells from the row-wise sum of their constituent months, with no hardcoded `"FY"`. Update the function docstring to describe the mapping contract.
  - Touches: `src/etl_totals.py`.
  - Acceptance: the function iterates the supplied mapping; `"FY"` no longer appears as a literal in the function body; fillna semantics preserved (populated totals untouched; NaN months count as 0).

- [x] [P1-T6] Update the single `fill_blank_totals` call site in `src/normalize_le.py` line 218 to `fill_blank_totals(frame, {"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS})`.
  - Touches: `src/normalize_le.py`.
  - Acceptance: the call passes one mapping argument; LE per-row tie-out behavior is unchanged.

- [x] [P1-T7] Confirm `normalize_le.__all__` re-exports still resolve (`coerce_sku`, `decide_key_action`, `rebuild_key`, `resolve_columns`, `resolve_key`) after the rename.
  - Touches: `src/normalize_le.py` (verification only; edit only if a re-export name breaks).
  - Acceptance: every name in `__all__` is importable from `src.normalize_le`; tests importing helpers from `src.normalize_le` are unaffected.

- [x] [P1-T8] Update the direct leaf import in `tests/test_le_columns.py` line 16 from `src.le_columns` to `src.etl_columns`, and update the module docstring `:mod:` reference at line 1.
  - Touches: `tests/test_le_columns.py`.
  - Acceptance: the file imports `src.etl_columns`; no `src.le_columns` reference remains.

- [x] [P1-T9] Update the two caplog logger-name string literals in `tests/test_le_key.py` lines 152 and 170 from `"src.le_key"` to `"src.etl_key"`, and update the module docstring `:mod:` reference at line 1.
  - Touches: `tests/test_le_key.py`.
  - Acceptance: both `caplog.at_level(..., logger="src.etl_key")` calls target the renamed logger; no `src.le_key` string remains.

- [x] [P1-T10] Rename `tests/test_le_columns.py` to `tests/test_etl_columns.py` to preserve test-to-module mirroring per `python.md`.
  - Touches: `tests/test_le_columns.py` (delete), `tests/test_etl_columns.py` (create with the P1-T8 content).
  - Acceptance: `tests/test_etl_columns.py` exists; `tests/test_le_columns.py` does not.

- [x] [P1-T11] Rename `tests/test_le_key.py` to `tests/test_etl_key.py` to preserve test-to-module mirroring per `python.md`.
  - Touches: `tests/test_le_key.py` (delete), `tests/test_etl_key.py` (create with the P1-T9 content).
  - Acceptance: `tests/test_etl_key.py` exists; `tests/test_le_key.py` does not. No `test_etl_totals.py` rename is required because LE totals are tested via `tests/test_normalize_le_totals.py` through `load_source`, not via a direct leaf-import test file.

- [x] [P1-T12] Update the stale docstring reference to `test_le_columns.py` in `tests/test_normalize_le.py` line 7 to `test_etl_columns.py`.
  - Touches: `tests/test_normalize_le.py`.
  - Acceptance: the docstring names the renamed test file; this is the cross-reference comment only, no assertion change.

- [x] [P1-T13] Run a repository-wide search for residual references to the old names (`le_columns`, `le_key`, `le_totals`, `src.le_columns`, `src.le_key`, `src.le_key` logger strings, `test_le_columns`, `test_le_key`) across `src/`, `tests/`, and `pyproject.toml`; resolve any remaining hit before finalizing the phase.
  - Touches: any file with a residual reference (verification + targeted fix).
  - Acceptance: the search returns zero hits for the old leaf-module names and old test-file names in code, imports, logger strings, and docstrings.

- [x] [P1-T14] Run the full toolchain loop until a clean single pass and capture LE-green-gate evidence.
  - Commands: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step changes files or fails.
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/qa-gates/phase1-le-green.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command, recording the full existing LE suite passing and numeric line/branch coverage %; this gate is the precondition for Phase 2.

### Phase 2 — `src/load_aop.py` Implementation and Console-Script Registration

No AOP code may be authored until Phase 1 (P1-T14) is green. All AOP transform logic reuses the
neutral leaf modules (`src.etl_columns`, `src.etl_key`, `src.etl_totals`) and the
`src.pandas_io` read/write boundary; no helper is re-implemented.

- [x] [P2-T1] Create `src/load_aop.py` with the AOP module constants exactly as specified: `MONTHS` (Jan..Dec), `YTG_MONTHS = MONTHS[4:]`, `QUARTER_COLUMNS` (Q1..Q4), `QUARTER_TO_MONTHS = {q: MONTHS[i*3:i*3+3]}`, `NUMERIC_COLS = [*MONTHS, "YTD", *QUARTER_COLUMNS, "YTG"]`, `SOURCE_COLUMNS` (KEY, Customer, "SKU Descripiton", "SKU #", "Customer Master", Type, *MONTHS, YTD, *QUARTER_COLUMNS, YTG, "Super Category", PPG), `EXPECTED_COLUMNS = [c for c in SOURCE_COLUMNS if c != "KEY"]`, `TARGET_COLUMNS = SOURCE_COLUMNS`.
  - Touches: `src/load_aop.py`.
  - Acceptance: constants match the spec Data & State section verbatim, including the intentional `SKU Descripiton` typo; module has a module docstring.

- [x] [P2-T2] Implement `clean_label_sentinels(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame` in `src/load_aop.py`, replacing sentinel values (numeric `0`, string `"0"`, string `"#N/A"`, NaN) with `None` for the named label columns, with a function docstring and intent comments.
  - Touches: `src/load_aop.py`.
  - Acceptance: the helper converts each listed sentinel to `None` and leaves other values intact; it does not apply the LE `Super Category <- PPG` quirk.

- [x] [P2-T3] Implement `load_aop(source, *, sheet="AOP1", transform=None, key_mismatch="prompt", is_tty=sys.stdin.isatty, prompt=input) -> pd.DataFrame` in `src/load_aop.py` following the spec data-flow order: read via `read_excel_sheet(source, sheet_name=sheet, header=2)`; locate optional KEY by `normalize_name(...) == "key"` (name only, never fuzzy) and exclude from required set; resolve remaining columns via `resolve_columns(actual_without_key, EXPECTED_COLUMNS)`, select/rename to canonical names, and log extras at WARNING; drop blank-`Customer` rows; fill blank totals via `fill_blank_totals(frame, {"YTD": MONTHS, **QUARTER_TO_MONTHS, "YTG": YTG_MONTHS})`; establish KEY via `resolve_key(frame, key_mismatch, has_key_column=..., is_tty=is_tty, prompt=prompt)` wired exactly as `normalize_le.load_source`; coerce `NUMERIC_COLS` with `pd.to_numeric(..., errors="coerce").fillna(0.0)` before validation; clean `["Super Category", "PPG"]` sentinels; validate; apply `transform` AFTER validation; return the frame.
  - Touches: `src/load_aop.py`.
  - Acceptance: `is_tty` is a zero-arg callable passed through to `resolve_key`; the optional KEY is located by name only; numeric coercion precedes validation; `transform` is applied only after validation passes; AOP does not collapse rows by KEY.

- [x] [P2-T4] Implement AOP per-row validation inside `load_aop` that runs after coercion and before transform: require at least 1 data row; compute violations via `total_vs_months_violations` for `YTD` vs `MONTHS`, each of `Q1..Q4` vs `QUARTER_TO_MONTHS`, and `YTG` vs `YTG_MONTHS` at tolerance `1e-6`; WARN (do not fail) on duplicate KEYs via `logging`; raise a single `ValueError` listing all failures when any identity check or the row-count check fails.
  - Touches: `src/load_aop.py`.
  - Acceptance: a single `ValueError` aggregates all per-row identity failures and the empty-frame failure; duplicate KEYs produce a WARNING only and never raise.

- [x] [P2-T5] Implement `persist_aop(df, db_path, table="aop", if_exists="replace") -> None` in `src/load_aop.py`, routing writes through `write_table`, passing `if_exists` through, and creating quoted lowercase lookup indexes for `KEY`, `Customer`, `"SKU #"`, and `Type` with index names made safe by replacing space with `_` and `#` with `num` and lowercasing.
  - Touches: `src/load_aop.py`.
  - Acceptance: persistence routes only through `write_table`; index identifiers are quoted; `if_exists` is forwarded unchanged; no row duplication on `replace`.

- [x] [P2-T6] Implement the run summary writer in `src/load_aop.py` that prints to stdout via `print` (not logging): row count, unique KEYs, customers, SKU #s, sorted Types, YTD total, and validation status, matching the spec example layout, plus the persistence confirmation line `Persisted <n> rows to <db_path> (table='<table>')`.
  - Touches: `src/load_aop.py`.
  - Acceptance: summary and confirmation go to stdout via `print`; warnings remain on `logging`.

- [x] [P2-T7] Implement `_build_parser() -> argparse.ArgumentParser` in `src/load_aop.py` with positional `<input.xlsx>`, required `--output`, `--source-sheet` (default `"AOP1"`), `--table-name` (default `"aop"`), `--key-mismatch` (choices `prompt`/`trust`/`overwrite`, default `prompt`), `--if-exists` (choices `replace`/`append`/`fail`, default `replace`), and `--snake-case` flag (default off).
  - Touches: `src/load_aop.py`.
  - Acceptance: argument defaults and choices match the spec config table; `--output` is a required argument.

- [x] [P2-T8] Implement `main(argv: list[str] | None = None) -> int` in `src/load_aop.py`: call `logging.basicConfig(level=logging.WARNING)` exactly once; parse args; call `load_aop`; apply `--snake-case` renames before writing when set (`sku_num`, `sku_description`, `customer_master`, `super_category`, `ppg`, `ytd`, `ytg`, `q1..q4`, `jan..dec`, `key`, `customer`, `type`); persist via `persist_aop`; print the summary; return `0` on success and `1` when a column-resolution, KEY-resolution, or validation `ValueError` is raised.
  - Touches: `src/load_aop.py`.
  - Acceptance: `main` returns 0 on success and 1 on the named `ValueError` classes; missing `--output` exits non-zero via argparse; `logging.basicConfig` is configured exactly once; default preserves original headers (typo included) and `--snake-case` renames before writing.

- [x] [P2-T9] If `src/load_aop.py` approaches the 500-line limit, extract AOP-specific helpers into `src/_load_aop_helpers.py` and import them back into `src/load_aop.py`; otherwise leave the single-file structure.
  - Touches: `src/load_aop.py`, and `src/_load_aop_helpers.py` only if extraction is required.
  - Acceptance: no file exceeds 500 lines; if extraction occurs, `src/load_aop.py` imports the extracted helpers and the public surface (`load_aop`, `persist_aop`, `main`) is unchanged.

- [x] [P2-T10] Register the Poetry console-script `load-aop = "src.load_aop:main"` in `pyproject.toml` under `[tool.poetry.scripts]` alongside the existing `normalize-le`.
  - Touches: `pyproject.toml`.
  - Acceptance: `[tool.poetry.scripts]` contains both `normalize-le` and `load-aop` entries; no other table is modified.

- [x] [P2-T11] Run the full toolchain loop until a clean single pass and capture Phase 2 QA evidence (coverage may be below threshold here because AOP tests land in Phase 3; record the values regardless).
  - Commands: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black on any change/failure.
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/qa-gates/phase2-aop-impl.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command (Black/Ruff/Pyright clean; LE suite still green; numeric coverage % recorded).

### Phase 3 — AOP Tests (Unit, Integration, CLI, Property)

Tests use in-memory fixtures only (`io.BytesIO` openpyxl workbooks with two leading padding rows
and header on Excel row 3; `PersistentConnection`/`patch_connect` for sqlite in-memory round-trips
surviving `.close()`; injected `is_tty`/`prompt`), reusing the patterns in `tests/le_fixtures.py`.
No temp files.

- [x] [P3-T1] Create `tests/test_load_aop.py` with an AOP in-memory workbook builder helper (or reuse/extend `tests/le_fixtures.py` patterns) that produces a `BytesIO` `AOP1` workbook with two leading non-data rows and the header on Excel row 3, plus a canonical valid-row factory.
  - Touches: `tests/test_load_aop.py` (and `tests/le_fixtures.py` only if a shared helper is extended).
  - Acceptance: the helper builds a readable AOP workbook with all `EXPECTED_COLUMNS`; no temp files are created.

- [x] [P3-T2] Add column-resolution tests in `tests/test_load_aop.py`: exact-by-position, reordered columns, fuzzy match at `>= 0.85`, missing-required-column halt (`ValueError` naming the unbound column), and extra-column warn-and-continue (assert WARNING and that processing continues).
  - Touches: `tests/test_load_aop.py`.
  - Acceptance: each resolution branch has a dedicated AAA-structured test; the optional KEY is asserted to be located by name only and excluded from required resolution.

- [x] [P3-T3] Add KEY-branch tests in `tests/test_load_aop.py` asserting AOP wires `resolve_key` like LE: absent-KEY create branch; present-matching-KEY trust branch; diverging-KEY `trust`/`overwrite` branches (assert WARNING text); diverging-KEY non-interactive `prompt` raising `ValueError` naming `--key-mismatch`; using injected `is_tty=lambda: <bool>` and `prompt`.
  - Touches: `tests/test_load_aop.py`.
  - Acceptance: each KEY branch has a dedicated test; `is_tty` is injected as a zero-arg callable.

- [x] [P3-T4] Add per-row validation tests in `tests/test_load_aop.py`: passing case (all `YTD`/`Q1..Q4`/`YTG` identities hold within `1e-6`); failing case raising a single `ValueError` listing all failures; empty-frame (row-count < 1) failure; duplicate-KEY WARNING that does not raise; assert numeric coercion happens before validation.
  - Touches: `tests/test_load_aop.py`.
  - Acceptance: validation pass/fail, empty-frame, and duplicate-KEY-warn scenarios are each covered; the `ValueError` aggregates multiple failures.

- [x] [P3-T5] Add sentinel-cleaning and transform tests in `tests/test_load_aop.py`: `clean_label_sentinels` converts `0`, `"0"`, `"#N/A"`, and NaN to `None` for `Super Category`/`PPG`; a caller-supplied `transform` is applied only after validation and before return; assert AOP does not apply the LE `Super Category <- PPG` quirk and does not collapse rows by KEY.
  - Touches: `tests/test_load_aop.py`.
  - Acceptance: sentinel conversion, transform-after-validation ordering, and no-quirk/no-collapse behavior are each asserted.

- [x] [P3-T6] Add property-based tests in `tests/test_load_aop.py` using `hypothesis` for the pure AOP functions (at minimum `clean_label_sentinels`; and any other pure function authored in `src/load_aop.py`), meeting the T2 density of at least one property test per pure function. Use seeded/deterministic strategies per the determinism policy.
  - Touches: `tests/test_load_aop.py`.
  - Acceptance: each pure AOP function has at least one hypothesis property test; tests are deterministic.

- [x] [P3-T7] Create `tests/test_load_aop_io.py` with SQLite persistence tests using `patch_connect`/`PersistentConnection`: `persist_aop` round-trip (columns and rows match), `if_exists="replace"` produces no row duplication on a second write, and quoted lowercase lookup indexes for `KEY`/`Customer`/`"SKU #"`/`Type` are created with safe names (space->`_`, `#`->`num`).
  - Touches: `tests/test_load_aop_io.py`.
  - Acceptance: round-trip equality, no-duplication-on-replace, and index-creation are each asserted via the in-memory connection; no temp files.

- [x] [P3-T8] Add CLI tests in `tests/test_load_aop_io.py` exercising `main`: success path returns `0` and prints the summary and persistence confirmation to stdout; missing `--output` exits non-zero; a resolution/KEY/validation `ValueError` path returns `1`; `--snake-case` renames columns before writing; a custom `--source-sheet`/`--table-name` is honored.
  - Touches: `tests/test_load_aop_io.py`.
  - Acceptance: exit codes 0 and 1 and the missing-`--output` non-zero exit are each asserted; `--snake-case` column names are asserted on the persisted table.

- [x] [P3-T9] Run the full toolchain loop until a clean single pass and capture Phase 3 QA evidence with numeric coverage.
  - Commands: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black on any change/failure.
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/qa-gates/phase3-aop-tests.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command, recording line coverage >= 85% and branch coverage >= 75% with the AOP tests included.

### Phase 4 — Tier Classification and Final Full-Toolchain QA

- [x] [P4-T1] Derive the exact `quality-tiers.yml` schema by reading `.claude/rules/quality-tiers.md` (and `docs/ci.research.md` section 1 if that file exists; it is absent at planning time). If the precise YAML shape cannot be derived from the rule, fail fast and report the blocker rather than guessing.
  - Touches: none (research/derivation step).
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/other/quality-tiers-schema-derivation.2026-05-26T14-03.md` records the derived schema (the key/value shape mapping a project to a tier) and the source lines that justify it, or records a fail-fast blocker if the schema is underspecified.

- [x] [P4-T2] Create `quality-tiers.yml` at the repository root classifying every `src` project/module consistently: classify the AOP module and the pure-transform ETL core (`normalize_le`, `etl_columns`, `etl_key`, `etl_totals`, `load_aop`) as T2-Core, and classify `pandas_io` per its role, using the schema derived in P4-T1 so that no project is left unclassified (CI requires every project be classified).
  - Touches: `quality-tiers.yml` (create at repo root).
  - Acceptance: `quality-tiers.yml` exists at repo root, classifies `src/load_aop.py` as T2-Core, classifies the remaining `src` modules consistently, and conforms to the schema derived in P4-T1; no module is left without a tier.

- [x] [P4-T3] Run the full final toolchain loop until a clean single pass and capture final-QA evidence with numeric post-change coverage.
  - Commands: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step changes files or fails.
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/qa-gates/phase4-final-qa.2026-05-26T14-03.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command, recording Black/Ruff/Pyright clean and Pytest passing with numeric line coverage >= 85% and branch coverage >= 75%.

- [x] [P4-T4] Record the coverage delta and threshold verification comparing the Phase 0 baseline to the Phase 4 final result.
  - Touches: none (evidence synthesis step).
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/qa-gates/coverage-delta.2026-05-26T14-03.md` exists recording baseline line/branch coverage % (from P0-T5), post-change line/branch coverage % (from P4-T3), and new/changed-code coverage for `src/load_aop.py` (and `src/_load_aop_helpers.py` if created); reports no regression on changed lines.

- [x] [P4-T5] Verify all Definition of Done acceptance criteria in `docs/features/active/2026-05-26-load-aop-sheet-7/issue.md` and `user-story.md` are satisfied and that no file exceeds 500 lines and no new third-party dependency was added.
  - Touches: none (final verification step).
  - Acceptance: `docs/features/active/2026-05-26-load-aop-sheet-7/evidence/other/dod-verification.2026-05-26T14-03.md` maps each acceptance criterion to its satisfying evidence artifact and confirms the file-size and no-new-dependency constraints.

## Test Plan

- Unit (`tests/test_load_aop.py`): column resolution (exact/reordered/fuzzy/missing-required/extras),
  KEY branches (create/trust/diverge-trust/diverge-overwrite/non-TTY-prompt), per-row validation
  pass/fail, empty-frame failure, duplicate-KEY warning, sentinel cleaning, transform-after-validation,
  no-quirk/no-collapse behavior, hypothesis property tests (>= 1 per pure function).
- Integration (`tests/test_load_aop_io.py`): SQLite persist round-trip via in-memory
  `PersistentConnection`, `if_exists="replace"` no-duplication, quoted lowercase index creation.
- CLI (`tests/test_load_aop_io.py`): success exit 0 with stdout summary and confirmation, missing
  `--output` non-zero, resolution/KEY/validation `ValueError` exit 1, `--snake-case` rename,
  custom sheet/table name.
- Regression: existing LE suite (`tests/test_etl_columns.py`, `tests/test_etl_key.py`,
  `tests/test_normalize_le*.py`) stays green after the rename and `fill_blank_totals` generalization.
- Coverage evidence:
  - Baseline: `evidence/baseline/pytest-cov.2026-05-26T14-03.md`
  - Post-change: `evidence/qa-gates/phase4-final-qa.2026-05-26T14-03.md`
  - Delta/threshold: `evidence/qa-gates/coverage-delta.2026-05-26T14-03.md`

## Open Questions / Notes

- `docs/ci.research.md` does not exist at planning time; P4-T1 derives the `quality-tiers.yml`
  schema from `.claude/rules/quality-tiers.md` and fails fast if the schema is underspecified.
- Research listed five leaf reference sites; a wider grep also found docstring/comment references in
  `tests/test_normalize_le.py` line 7 and the module docstrings of the renamed test files. P1-T12 and
  P1-T13 handle these so the rename leaves zero residual references.
- No `tests/test_le_totals.py` exists; LE totals are exercised through `tests/test_normalize_le_totals.py`
  via `load_source`, so no totals test-file rename is needed.
