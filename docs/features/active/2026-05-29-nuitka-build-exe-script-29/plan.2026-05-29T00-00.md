# Plan — nuitka-build-exe-script (Issue #29)

- Timestamp: 2026-05-29T00-00
- Feature folder: `docs/features/active/2026-05-29-nuitka-build-exe-script-29/`
- Work Mode: minor-audit
- Promotion Type: feature
- AC source: `docs/features/active/2026-05-29-nuitka-build-exe-script-29/issue.md` `## Acceptance Criteria` (AC1–AC10)
- Tier classification: `src/build_exe.py` will be added to `quality-tiers.yml` as **T4 (Scaffolding)**. Rationale: pure build-tooling glue, no transform logic, parallel to `src/gui/app.py` (T4) — although the build script lives in `src/`, it is a developer-facing build script analogous to `src/gui/app.py` composition glue. Coverage thresholds remain uniform (line >= 85%, branch >= 75%) regardless of tier.
- Evidence root (canonical): `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/`

## Conventions

- Every command-step artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per `evidence-and-timestamp-conventions`.
- All evidence files are written under `<FEATURE>/evidence/<kind>/`; alternative locations (`artifacts/baselines/`, `artifacts/qa/`, etc.) are forbidden and will be rejected.
- Toolchain order for Python (uniform per `.claude/rules/python.md`): Black → Ruff → Pyright → Pytest. Restart from step 1 if any step fails or rewrites files.
- Subprocess seam pattern is mandatory; tests must NOT invoke the real Nuitka binary.
- All path resolution in `src/build_exe.py` anchors to `pathlib.Path(__file__).resolve().parents[1]`.

---

### Phase 0 — Compliance & context

- [x] [P0-T1] Read `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`, and `.claude/rules/tonality.md` in that order. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/baseline/phase0-instructions-read.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read with absolute paths.
- [x] [P0-T2] Read `docs/features/active/2026-05-29-nuitka-build-exe-script-29/issue.md` and confirm an explicit `## Acceptance Criteria` section is present with AC1–AC10. Acceptance: append a `Mode-Source Verification:` block to `phase0-instructions-read.md` recording resolved mode `minor-audit` (per `- Work Mode: minor-audit` marker in `issue.md` line 9) and listing AC1–AC10 identifiers.
- [x] [P0-T3] Capture baseline Black state. Command: `poetry run black --check .`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/baseline/baseline-black.2026-05-29T00-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (one line stating pass/fail and number of files that would be reformatted).
- [x] [P0-T4] Capture baseline Ruff state. Command: `poetry run ruff check .`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/baseline/baseline-ruff.2026-05-29T00-00.md` with the four required fields; `Output Summary:` must include the violation count or `All checks passed`.
- [x] [P0-T5] Capture baseline Pyright state. Command: `poetry run pyright`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/baseline/baseline-pyright.2026-05-29T00-00.md` with the four required fields; `Output Summary:` must include error / warning / information counts from the Pyright summary line.
- [x] [P0-T6] Capture baseline Pytest + coverage state. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/baseline/baseline-pytest.2026-05-29T00-00.md` with the four required fields; `Output Summary:` must include numeric headline totals (passed / failed counts) AND numeric baseline line coverage % and branch coverage % drawn from the TOTAL row of the term-missing report.
- [x] [P0-T7] Confirm `dist` is already in `.gitignore` (line 2). Acceptance: append a `GitignoreBaseline:` block to `phase0-instructions-read.md` recording the literal matching line from `.gitignore` and the decision rule for P4-T2 (skip adding `dist/nuitka/` if `dist` already covers it; otherwise add `dist/nuitka/`).
- [x] [P0-T8] Confirm `pyproject.toml` `[tool.poetry.scripts]` contains `normalize-le`, `load-aop`, `mix-pipeline-gui` and does NOT yet contain `build-exe`. Acceptance: append a `PyProjectBaseline:` block to `phase0-instructions-read.md` listing the three existing script entries verbatim.
- [x] [P0-T9] Confirm `src/gui/app.py` defines `def main(argv: list[str] | None = None) -> int` at module scope. Acceptance: append a `CompileTargetVerified:` block to `phase0-instructions-read.md` citing the line number of `main` in `src/gui/app.py` (line 475 at baseline).

---

### Phase 1 — Module skeleton + argparse + path resolution (test-first)

Objective: write the `src/build_exe.py` skeleton with the argparse parser and path-anchor constant, plus the tests covering both, ending with the toolchain green for the new files.

- [x] [P1-T1] Create `tests/test_build_exe.py` with a failing test `test_build_argument_parser_exposes_dry_run_and_clean_flags` that imports `src.build_exe.build_argument_parser` and asserts the parser exposes both `--dry-run` and `--clean` as boolean flags defaulting to `False`. Acceptance: file exists at `tests/test_build_exe.py`; running `poetry run pytest tests/test_build_exe.py::test_build_argument_parser_exposes_dry_run_and_clean_flags` fails with `ModuleNotFoundError` or `AttributeError` (expected pre-implementation failure recorded in step P1-T3).
- [x] [P1-T2] Add the test `test_repo_root_resolves_to_project_root` to `tests/test_build_exe.py` asserting `src.build_exe.REPO_ROOT` equals `pathlib.Path(__file__).resolve().parents[1]` for the build_exe module (i.e. the directory containing `pyproject.toml`). The test verifies the anchor by checking that `(REPO_ROOT / "pyproject.toml").is_file()` is `True`. Acceptance: the new test is appended to `tests/test_build_exe.py`; no production code changes yet.
- [x] [P1-T3] Capture the expected-failing pre-implementation pytest run for the two tests above. Command: `poetry run pytest tests/test_build_exe.py -k "build_argument_parser_exposes or repo_root_resolves" --no-header`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/regression-testing/p1-fail-before.2026-05-29T00-00.md` with the four schema fields; `Output Summary:` must record both tests failing because `src.build_exe` does not yet exist.
- [x] [P1-T4] Create `src/build_exe.py` with: (a) module-level docstring per `.claude/rules/self-explanatory-code-commenting.md`; (b) `REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]`; (c) a public `build_argument_parser() -> argparse.ArgumentParser` returning a parser with `--dry-run` and `--clean` as `store_true` flags (defaults `False`); (d) a stub `def main(argv: Sequence[str] | None = None) -> int: raise NotImplementedError` reserved for Phase 3. Acceptance: file exists at `src/build_exe.py` and is < 500 lines.
- [x] [P1-T5] Add `src/build_exe.py` to `quality-tiers.yml` under `projects:` as `src/build_exe.py: T4` with a short inline rationale comment matching the surrounding style (pure build-tooling glue analogous to `src/gui/app.py`). Acceptance: `quality-tiers.yml` contains the new mapping line; no other entries change.
- [x] [P1-T6] Run `poetry run black src/build_exe.py tests/test_build_exe.py`. Acceptance: command exits 0 and reports both files unchanged or formatted; no toolchain-level errors.
- [x] [P1-T7] Run `poetry run ruff check src/build_exe.py tests/test_build_exe.py`. Acceptance: command exits 0 with `All checks passed!`.
- [x] [P1-T8] Run `poetry run pyright src/build_exe.py tests/test_build_exe.py`. Acceptance: command exits 0 with `0 errors, 0 warnings, 0 informations`.
- [x] [P1-T9] Run `poetry run pytest tests/test_build_exe.py -k "build_argument_parser_exposes or repo_root_resolves"`. Acceptance: both Phase-1 tests pass; command exits 0.

---

### Phase 2 — Command-resolution function + tests

Objective: implement and test the deterministic Nuitka argv resolver covering AC4. Tests are written before production code; phase ends with the toolchain silent.

- [x] [P2-T1] Append two failing tests to `tests/test_build_exe.py`: (a) `test_resolve_nuitka_command_contains_required_flags` asserting `resolve_nuitka_command()` returns a list whose elements include `--standalone`, `--enable-plugin=pyside6`, `--include-package=pandas`, `--include-package=openpyxl`, and `--output-dir=<REPO_ROOT>/dist/nuitka` (string-compared after `Path` normalization on Windows); (b) `test_resolve_nuitka_command_ends_with_app_entry` asserting the final positional argument equals `str(REPO_ROOT / "src" / "gui" / "app.py")`. Acceptance: both tests are present; they currently fail because the symbol does not exist.
- [x] [P2-T2] Append a third failing test `test_resolve_nuitka_command_starts_with_python_nuitka_invocation` asserting the first three argv elements are `[sys.executable, "-m", "nuitka"]`. Acceptance: test is appended; fails pre-implementation.
- [x] [P2-T3] Capture pre-implementation failure evidence. Command: `poetry run pytest tests/test_build_exe.py -k resolve_nuitka_command --no-header`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/regression-testing/p2-fail-before.2026-05-29T00-00.md` with the four schema fields; `Output Summary:` must record three failures attributable to missing `resolve_nuitka_command`.
- [x] [P2-T4] Implement `def resolve_nuitka_command() -> list[str]` in `src/build_exe.py`. Return value (exact order):
  `[sys.executable, "-m", "nuitka", "--standalone", "--enable-plugin=pyside6", "--include-package=pandas", "--include-package=openpyxl", f"--output-dir={REPO_ROOT / 'dist' / 'nuitka'}", str(REPO_ROOT / "src" / "gui" / "app.py")]`.
  The function must have a docstring covering Purpose, Returns, and Side Effects (`None`) per the commenting policy. Acceptance: function exists; module still under 500 lines.
- [x] [P2-T5] Run `poetry run black src/build_exe.py tests/test_build_exe.py`. Acceptance: exits 0; no errors.
- [x] [P2-T6] Run `poetry run ruff check src/build_exe.py tests/test_build_exe.py`. Acceptance: exits 0 with `All checks passed!`.
- [x] [P2-T7] Run `poetry run pyright src/build_exe.py tests/test_build_exe.py`. Acceptance: exits 0 with `0 errors`.
- [x] [P2-T8] Run `poetry run pytest tests/test_build_exe.py -k resolve_nuitka_command`. Acceptance: all three Phase-2 tests pass; command exits 0.

---

### Phase 3 — Subprocess seam + dry-run / clean / invoke logic + tests

Objective: implement the subprocess seam (`run_nuitka`) and the `main()` orchestration covering `--dry-run`, `--clean`, and Nuitka invocation including exit-code propagation. Tests are added first; phase ends with toolchain silent and coverage on `src/build_exe.py` >= 85% line / >= 75% branch.

- [x] [P3-T1] Append to `tests/test_build_exe.py` a test `test_main_dry_run_prints_argv_and_does_not_invoke_seam` that calls `main(["--dry-run"], run_nuitka=<recording_stub>)` where the stub records every invocation. The test captures stdout via `capsys`, asserts the printed line contains each required argv token (`--standalone`, `--enable-plugin=pyside6`, `--include-package=pandas`, `--include-package=openpyxl`, `--output-dir=`, `app.py`), asserts the stub was called exactly 0 times, and asserts `main()` returned `0`. Acceptance: test is present and fails pre-implementation.
- [x] [P3-T2] Append `test_main_clean_removes_existing_dist_tree` to `tests/test_build_exe.py`. The test uses `monkeypatch` to replace `src.build_exe.REPO_ROOT` with a `Path` object whose tree contains a pre-populated `dist/nuitka/` subdirectory created entirely in memory via `pyfakefs` (or, if `pyfakefs` is not already a dev dependency, via a `monkeypatch`-injected fake `shutil.rmtree` recorder — the test MUST NOT create real temp files per `.claude/rules/general-unit-test.md`). The test injects a `rmtree` recorder via the production seam (`remove_tree: Callable[[Path], None]`) and asserts the recorder is invoked exactly once with the path `REPO_ROOT / "dist" / "nuitka"`. A second sub-case asserts the recorder is NOT invoked when the directory does not exist (the production code must guard with `Path.is_dir()`). Acceptance: test is present and fails pre-implementation.
- [x] [P3-T3] Append `test_main_invokes_seam_and_propagates_returncode` parametrized over return codes `[0, 1, 2, 137]`. The test passes a stub `run_nuitka` returning an object with `.returncode == code`, calls `main([])`, and asserts the return value equals `code` and the stub was called exactly once with the argv list from `resolve_nuitka_command()`. Acceptance: test is present and fails pre-implementation.
- [x] [P3-T4] Append `test_main_clean_flag_then_invokes_seam` asserting that when both `--clean` is supplied and the directory exists, the `remove_tree` seam fires before the `run_nuitka` seam (order verified via a shared call-log list). Acceptance: test is present and fails pre-implementation.
- [x] [P3-T5] Append `test_main_uses_default_seams_when_unspecified` asserting that when `main()` is called without overriding `run_nuitka`/`remove_tree`, the defaults bind to `subprocess.run` and `shutil.rmtree` respectively — verified by patching those module-level symbols in `src.build_exe` with recorders, calling `main(["--dry-run"])` (so `subprocess.run` is not invoked) and `main(["--clean", "--dry-run"])` (so `shutil.rmtree` is invoked when the directory exists). Acceptance: test is present and fails pre-implementation.
- [x] [P3-T6] Capture pre-implementation failure evidence for all Phase-3 tests. Command: `poetry run pytest tests/test_build_exe.py -k "main_dry_run or main_clean or main_invokes_seam or main_uses_default" --no-header`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/regression-testing/p3-fail-before.2026-05-29T00-00.md` with the four schema fields; `Output Summary:` must record the expected failure count attributable to `main` returning `NotImplementedError` or missing parameters.
- [x] [P3-T7] Implement the production `main(argv, *, run_nuitka=subprocess.run, remove_tree=shutil.rmtree) -> int` in `src/build_exe.py`. Behavior:
  1. Parse `argv` via `build_argument_parser()`.
  2. If `args.clean` and `(REPO_ROOT / "dist" / "nuitka").is_dir()`, call `remove_tree(REPO_ROOT / "dist" / "nuitka")`.
  3. Compute `argv_list = resolve_nuitka_command()`.
  4. If `args.dry_run`, print the argv (quoted with `shlex.join` so the printed line is copy-pasteable) and return `0`.
  5. Otherwise call `run_nuitka(argv_list)` and return its `.returncode` attribute.
  The function and its decision branches must carry docstrings and decision-logic comments per `.claude/rules/self-explanatory-code-commenting.md`. Acceptance: file remains < 500 lines; no `# noqa` or `# type: ignore` introduced.
- [x] [P3-T8] Add `if __name__ == "__main__":\n    raise SystemExit(main())` at end of `src/build_exe.py` (excluded from coverage by the existing `[tool.coverage.report] exclude_lines` rule). Acceptance: line is present; pyright remains clean.
- [x] [P3-T9] Run `poetry run black src/build_exe.py tests/test_build_exe.py`. Acceptance: exits 0.
- [x] [P3-T10] Run `poetry run ruff check src/build_exe.py tests/test_build_exe.py`. Acceptance: exits 0 with `All checks passed!`.
- [x] [P3-T11] Run `poetry run pyright src/build_exe.py tests/test_build_exe.py`. Acceptance: exits 0 with `0 errors`.
- [x] [P3-T12] Run `poetry run pytest tests/test_build_exe.py --cov=src.build_exe --cov-branch --cov-report=term-missing`. Acceptance: exits 0; ALL Phase-1/2/3 tests pass; line coverage on `src/build_exe.py` >= 85% and branch coverage >= 75% as reported by the TOTAL row of the term-missing output.

---

### Phase 4 — `pyproject.toml` entry-point and `.gitignore` edits

Objective: register the Poetry script entry point (AC2) and ensure `.gitignore` excludes the Nuitka output tree (AC10).

- [x] [P4-T1] Edit `pyproject.toml` `[tool.poetry.scripts]`: append a new line `build-exe = "src.build_exe:main"` after the existing `mix-pipeline-gui` entry. Acceptance: `poetry check` exits 0; running `poetry run python -c "import importlib; importlib.import_module('src.build_exe').main"` succeeds (no exception, no output beyond Poetry's own).
- [x] [P4-T2] Inspect `.gitignore` line 2 (`dist`). Decision rule: if `dist` is present at the file's top level (it is, per the P0-T7 baseline), this task is a NO-OP and the acceptance is satisfied by recording the decision; if `dist` were absent, append `dist/nuitka/` on a new line under the `# Python` section. Acceptance: append a `GitignoreDecision:` block to `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/other/p4-gitignore-decision.2026-05-29T00-00.md` with `Timestamp:`, `Command:` (the inspection command `Get-Content .gitignore | Select-Object -First 5`), `EXIT_CODE: 0`, and `Output Summary:` stating the decision (`NO-OP: dist already covers dist/nuitka/` or `ADDED: dist/nuitka/`).
- [x] [P4-T3] Run `poetry run black .` over the workspace. Acceptance: exits 0; no files reformatted.
- [x] [P4-T4] Run `poetry run ruff check .`. Acceptance: exits 0 with `All checks passed!`.

---

### Phase 5 — Final QA loop + coverage delta + AC verification

Objective: run the full mandatory Python toolchain loop on the workspace and persist final QA evidence with numeric post-change coverage and the AC1–AC10 verification matrix.

- [x] [P5-T1] Run final-pass formatting. Command: `poetry run black --check .`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/qa-gates/final-black.2026-05-29T00-00.md` with the four schema fields; `EXIT_CODE: 0`; `Output Summary:` must state `All files pass Black formatting.` If exit is non-zero, restart from P5-T1 after running `poetry run black .`.
- [x] [P5-T2] Run final-pass linting. Command: `poetry run ruff check .`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/qa-gates/final-ruff.2026-05-29T00-00.md` with the four schema fields; `EXIT_CODE: 0`; `Output Summary:` must include `All checks passed!`.
- [x] [P5-T3] Run final-pass type checking. Command: `poetry run pyright`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/qa-gates/final-pyright.2026-05-29T00-00.md` with the four schema fields; `EXIT_CODE: 0`; `Output Summary:` must include the trailing `N errors, N warnings, N informations` line and the error count must be `0`.
- [x] [P5-T4] Run final-pass tests with coverage. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/qa-gates/final-pytest.2026-05-29T00-00.md` with the four schema fields; `EXIT_CODE: 0`; `Output Summary:` must record the overall passed/failed counts AND a per-module headline for `src/build_exe.py` showing line% and branch% (both must satisfy the uniform thresholds: line >= 85%, branch >= 75%).
- [x] [P5-T5] Write a coverage delta artifact. Source the baseline numbers from `evidence/baseline/baseline-pytest.2026-05-29T00-00.md` (P0-T6) and the post-change numbers from `evidence/qa-gates/final-pytest.2026-05-29T00-00.md` (P5-T4). Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/qa-gates/coverage-delta.2026-05-29T00-00.md` containing a single table with columns `Scope | Baseline line% | Post-change line% | Baseline branch% | Post-change branch%` and rows for `TOTAL` and `src/build_exe.py`. The artifact also records the decision rule: PASS iff TOTAL coverage did not regress AND `src/build_exe.py` line% >= 85 AND branch% >= 75. If any value is missing or below threshold, the plan outcome is remediation-required.
- [x] [P5-T6] Write the AC verification matrix. Acceptance: write `docs/features/active/2026-05-29-nuitka-build-exe-script-29/evidence/qa-gates/ac-verification.2026-05-29T00-00.md` containing one row per AC1–AC10 with columns `AC | Status (PASS/FAIL) | Evidence Path | Notes`. Status sources:
  - AC1 → `src/build_exe.py` exists and contains `main` (link to file path + line range).
  - AC2 → `pyproject.toml` `[tool.poetry.scripts]` contains `build-exe = "src.build_exe:main"` (cite line).
  - AC3 → P3-T12 pytest output for `test_main_dry_run_prints_argv_and_does_not_invoke_seam`.
  - AC4 → P3-T12 pytest output for `resolve_nuitka_command` tests.
  - AC5 → P3-T12 pytest output for the two clean-path test cases.
  - AC6 → P3-T12 pytest output for `test_main_invokes_seam_and_propagates_returncode`.
  - AC7 → `final-pytest.2026-05-29T00-00.md` + `coverage-delta.2026-05-29T00-00.md`.
  - AC8 → line counts of `src/build_exe.py` and `tests/test_build_exe.py` (must be < 500).
  - AC9 → all four `final-*.2026-05-29T00-00.md` artifacts EXIT_CODE 0.
  - AC10 → P4-T2 `p4-gitignore-decision.2026-05-29T00-00.md`.
- [x] [P5-T7] Confirm file-size cap. Commands: `(Get-Content src/build_exe.py | Measure-Object -Line).Lines` and `(Get-Content tests/test_build_exe.py | Measure-Object -Line).Lines`. Acceptance: append a `FileSize:` block to `ac-verification.2026-05-29T00-00.md` recording both line counts; both must be < 500 per AC8.

---

## End-of-plan status

- All Phase 1–3 tasks end with the test suite green and Black/Ruff/Pyright silent.
- Phase 5 produces the final coverage delta and AC verification matrix.
- Plan failure modes: any final-QC EXIT_CODE != 0, missing artifact, or coverage value below threshold transitions the plan outcome to `remediation-required` and the planner / executor handoff is not approved.
