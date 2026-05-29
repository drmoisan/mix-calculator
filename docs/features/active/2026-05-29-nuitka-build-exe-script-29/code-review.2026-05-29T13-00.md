# Code Review: nuitka-build-exe-script (#29)

**Review Date:** 2026-05-29
**Reviewer:** feature-review
**Cycle:** 0 (initial review)
**Feature Folder:** `docs/features/active/2026-05-29-nuitka-build-exe-script-29/`
**Base Branch:** `main` @ `8ea722e8a8c904732910c669fe0e79c95a10f68c`
**Head Branch:** `feature/nuitka-build-exe-script-29` @ `43ed2b73bc2fdb0a009991984205cf7cc30886a5`
**Review Type:** Initial code-quality review

## Executive Summary

The branch adds a 206-line Python module (`src/build_exe.py`) that compiles the existing `mix-pipeline-gui` PySide6 application into a standalone Windows executable using Nuitka. The module exposes one Poetry entry point (`build-exe`) and delegates to a deterministic argv resolver, an `argparse`-based parser, a small `_dist_nuitka_exists` indirection seam, and a `main` orchestrator that accepts two optional injection seams (`run_nuitka` and `remove_tree`). The companion test module (`tests/test_build_exe.py`, 359 lines) delivers 13 fixture-based Pytest tests using three local recorder dataclasses; the real Nuitka binary is never invoked.

**What changed:**

- `src/build_exe.py` (NEW, 206 lines) — argparse parser, deterministic Nuitka argv resolver, `_dist_nuitka_exists` directory-presence seam, `main` orchestrator with `run_nuitka` / `remove_tree` injection seams. One pre-authorized `# noqa: S603` suppression on the `subprocess.run` call. No other suppressions.
- `tests/test_build_exe.py` (NEW, 359 lines) — 13 Pytest tests covering parser flag shape, `REPO_ROOT` anchor, argv contract (flags, trailing positional, leading invocation triple), dry-run path, clean path (exists / missing sub-cases), exit-code propagation parametrized over `[0, 1, 2, 137]`, clean-then-invoke ordering, default-seam wiring.
- `pyproject.toml` — one-line addition: `build-exe = "src.build_exe:main"` under `[tool.poetry.scripts]`.
- `quality-tiers.yml` — five-line addition: `src/build_exe.py: T4` with explicit rationale.
- Feature folder evidence (`evidence/baseline/`, `evidence/qa-gates/`, `evidence/regression-testing/`, `evidence/other/`).

**Top 3 risks:**

1. The module pins the Nuitka invocation form to `[sys.executable, "-m", "nuitka", ...]`, which delegates to the Nuitka installed in the active interpreter. If a future contributor sets `VIRTUAL_ENV` incorrectly or invokes the script under a Python that lacks Nuitka, the script will fail at subprocess invocation rather than at argv resolution. Mitigation: the failure is loud (Nuitka raises a clear ImportError-style exit code propagated through the seam), and the repo's documented Poetry quirk (memory: `poetry-virtualenv-quirk`) is the standard workaround.
2. The `# noqa: S603` suppression on line 199-201 covers the `subprocess.run` invocation. The suppression is pre-authorized and the rationale (the executable is `sys.executable`, not user input) is stronger than the pre-authorized pattern requires. Mitigation: any future code change near this line should re-evaluate the suppression. The seam parameter `run_nuitka` allows tests to bypass `subprocess.run` entirely, so the suppression is on the production default path only.
3. The `--clean` branch uses `_dist_nuitka_exists()` as a check-before-delete guard. If the directory is created between the check and the `shutil.rmtree` call (TOCTOU race), the call would fail with a `FileNotFoundError`. Mitigation: this is a single-user build tool, not a multi-process service; the TOCTOU window is not exploitable in the documented use case. The test `test_main_clean_removes_existing_dist_tree` covers both branches via monkeypatch.

**PR readiness recommendation:** **Ready for merge** — Black / Ruff / Pyright / Pytest all green; coverage above uniform 85%/75% thresholds on the changed file (97% LINE / 100% BRANCH); all ten ACs PASS; no policy findings.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/build_exe.py` | lines 1-206 | 206-line Nuitka build orchestration module. Four functions: `build_argument_parser`, `resolve_nuitka_command`, `_dist_nuitka_exists`, `main(argv, *, run_nuitka, remove_tree)`. Google-style docstrings on every function; module docstring; inline rationale comments at lines 41-44 (REPO_ROOT anchor), 106-109 (argv contract), 182-185 (clean branch ordering), 191-194 (dry-run branch). One pre-authorized `# noqa: S603` at line 199-201. | None. | Single-purpose module; the design follows the issue's "Design Notes (for the planner)" section verbatim. | Direct file read; AC-verification matrix at `evidence/qa-gates/ac-verification.2026-05-29T00-00.md`. |
| Info | `tests/test_build_exe.py` | lines 1-359 | 359-line Pytest test module. 13 `test_` functions plus three local recorder dataclasses (`_RunNuitkaRecorder`, `_RemoveTreeRecorder`, `_OrderedCallLog`). Uses `pytest.mark.parametrize` over `[0, 1, 2, 137]` for return-code propagation. `monkeypatch.setattr` patches the seam at the import location used by the unit under test (`build_exe_module._dist_nuitka_exists`, `build_exe_module.subprocess.run`, `build_exe_module.shutil.rmtree`). | None. | All five enumerated AC7 paths exercised. The real Nuitka binary is never invoked. | Direct file read; `evidence/qa-gates/final-pytest.2026-05-29T00-00.md` (430/430 passing). |
| Info | `pyproject.toml` | line 37 | `build-exe = "src.build_exe:main"` added under `[tool.poetry.scripts]`. | None. | Closes AC2. | Direct file read; `poetry check` EXIT_CODE 0 per AC-verification matrix. |
| Info | `quality-tiers.yml` | lines 64-67 | `src/build_exe.py: T4` with rationale: "pure build-tooling glue analogous to `src/gui/app.py`: no transform logic, only argparse + a deterministic argv resolver + a subprocess seam." | None. | Required by `.claude/rules/quality-tiers.md`: every project must be classified. T4 is the correct tier (scaffolding / build tooling). | Direct file read of the diff. |
| Info | feature evidence tree | `evidence/baseline/`, `evidence/qa-gates/`, `evidence/regression-testing/`, `evidence/other/` | All evidence under canonical `<FEATURE>/evidence/<kind>/` paths per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Each baseline and final-QA file carries `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. No artifacts written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`. | None. | Evidence-location invariant satisfied. | Git diff scan; `evidence/qa-gates/ac-verification.2026-05-29T00-00.md`. |

No Blocker, Major, or Minor findings.

## Implementation Audit

### Python implementation audit

#### What changed well

- The module is single-purpose and small (206 lines). Four functions each have one clear responsibility: `build_argument_parser` returns a parser, `resolve_nuitka_command` returns the deterministic argv, `_dist_nuitka_exists` is the directory-presence indirection seam, and `main` is the orchestrator.
- The argv contract is enforced as a literal list literal at lines 110-120 with a meta-what comment explaining the three-part structure (leading interpreter triple, flags in AC4 order, trailing positional). A future reader does not need to read the tests to understand the contract.
- The `REPO_ROOT` anchor at line 45 uses `Path(__file__).resolve().parents[1]`, which is deterministic regardless of `cwd`. The inline comment explains the `parents[1]` index (parents[0] is `src/`, parents[1] is the repo root).
- The `--clean` branch at lines 185-187 fires before any other work and is guarded by `_dist_nuitka_exists()`, which keeps a stale or partial tree from being fed to the compile step. The seam parameter `remove_tree` allows tests to substitute a recorder.
- The `--dry-run` branch at lines 193-195 uses `shlex.join` to emit a copy-pasteable line for AC3 stdout preview. The function returns `0` cleanly without invoking Nuitka.
- The default subprocess seam (lines 198-201) resolves to `subprocess.run` only when `run_nuitka is None`, so test injection is the priority path.

#### API and safety notes

- No new public types beyond the three public functions and the `REPO_ROOT` constant. The seam parameters on `main` are kwarg-only (`*` separator at line 143), which prevents positional misuse.
- No `Invoke-Expression`-equivalent (no `eval`, no `exec`, no `shell=True` on the subprocess call). The argv is a `list[str]`, not a shell string.
- No plaintext secrets, no environment-variable reads, no network access. The only external dependencies are stdlib modules.
- The `# noqa: S603` suppression on the `subprocess.run` invocation matches the pre-authorized pattern verbatim per `.claude/rules/python-suppressions.md`. The rationale is stronger than the pre-authorized pattern requires because the executable is `sys.executable` (the currently-running interpreter), not a PATH-resolved binary.

#### Error handling and logging

- The module does not raise any custom exceptions. It propagates Nuitka's `returncode` through the seam's return value. This is the documented AC6 contract.
- The dry-run path uses `print(shlex.join(argv_list))`, which is the documented AC3 stdout preview, not a permanent log. The module imports no `logging` because there is no operational logging requirement.
- The `if __name__ == "__main__"` block at line 205-206 uses `raise SystemExit(main())`, which is the standard Python entry-point convention.

#### Type annotation discipline

- Every function has a complete type signature with named, kwarg-only seam parameters.
- `Sequence` and `Callable` are imported only under `TYPE_CHECKING` (lines 38-39), satisfying TCH003 without a suppression.
- The seam type signature `Callable[[Sequence[str]], subprocess.CompletedProcess[str]]` accurately reflects the `subprocess.run` contract.

### Test implementation audit

#### What changed well

- Three local recorder dataclasses (`_RunNuitkaRecorder`, `_RemoveTreeRecorder`, `_OrderedCallLog`) replace the production seams. Each has a `__call__` method matching the production seam signature so the production code does not know it is being tested. Each carries a docstring explaining purpose, attributes, and side effects.
- The four-way parametrize over `[0, 1, 2, 137]` covers AC6 return-code propagation across success (0), generic failure (1), distinct error (2), and POSIX-style termination signal exit (137). A future regression in any of the four cases would identify the specific failing return code.
- The `monkeypatch.setattr(build_exe_module.subprocess, "run", recording_run)` pattern at line 342 patches at the import location used by the unit under test, per `.claude/rules/python.md`. The same pattern is used for `shutil.rmtree` at line 355.
- `test_main_clean_flag_then_invokes_seam` uses a shared `_OrderedCallLog` to verify ordering: the `remove_tree` event must precede the `run_nuitka` event so a half-cleaned tree is never fed to the compile step. This ordering test is a load-bearing safety invariant.
- The Arrange-Act-Assert pattern is explicit in every `test_` function. Example: `test_main_dry_run_prints_argv_and_does_not_invoke_seam` Arranges `_RunNuitkaRecorder()`, Acts `main(["--dry-run"], run_nuitka=run_recorder)`, Asserts on captured stdout and recorder call count.

#### Notes

- The `tmp_path_factory` parameter on `test_main_clean_removes_existing_dist_tree` (line 212) is declared but never used to create files. The test exercises the clean branch via the `_dist_nuitka_exists` monkeypatch instead. The unused parameter carries a `# type: ignore[unused-ignore]` annotation (line 212) which is a Pyright variance suppression on a Pytest fixture, not a true ignore of a real error. Ruff EXIT_CODE 0 confirms this is acceptable. The parameter could be removed in a future cleanup since it is dead weight, but its presence is non-blocking.
- The use of `list[list[str]]` and `list[pathlib.Path]` as `field(default_factory=...)` arguments at lines 37 and 71 uses the PEP 585 generic-list syntax as a factory; this is a Python 3.9+ idiom and is type-correct per Pyright EXIT_CODE 0.

### TOML configuration audit

#### What changed well

- `pyproject.toml` line 37 places `build-exe = "src.build_exe:main"` adjacent to the three existing script entries (`normalize-le`, `load-aop`, `mix-pipeline-gui`), preserving the file's existing ordering convention. The single-line add is minimal.
- `quality-tiers.yml` adds the new module classification with a three-line rationale comment that names the tier (T4-Scaffolding), the analogue (`src/gui/app.py`), and the structural reason (argparse + argv resolver + subprocess seam, no transform logic). The classification is correct: the module has no business logic to verify, only invocation glue.

## Test Quality Audit

### Reviewed test and QA artifacts

- `tests/test_build_exe.py` (NEW, 359 lines) — 13 fixture-based tests.
- `evidence/qa-gates/final-pytest.2026-05-29T00-00.md` — 430/430 passing in 19.23s; `src/build_exe.py` LINE 97% (30/31), BRANCH 100% (4/4).
- `evidence/qa-gates/coverage-delta.2026-05-29T00-00.md` — PASS verdict; no TOTAL regression; new-file thresholds met.
- `evidence/qa-gates/final-black.2026-05-29T00-00.md` — Black clean, 107 files unchanged.
- `evidence/qa-gates/final-ruff.2026-05-29T00-00.md` — Ruff clean, `All checks passed!`.
- `evidence/qa-gates/final-pyright.2026-05-29T00-00.md` — Pyright clean, 0 errors / 0 warnings / 0 informations.
- `evidence/qa-gates/ac-verification.2026-05-29T00-00.md` — All 10 ACs PASS.
- `evidence/regression-testing/p1-fail-before.2026-05-29T00-00.md`, `p2-fail-before.2026-05-29T00-00.md`, `p3-fail-before.2026-05-29T00-00.md` — pre-implementation failing tests captured before each phase's implementation, demonstrating TDD discipline.

### Quality assessment

- **Determinism:** No randomness, no time dependency, no real disk fixtures. The clean branch is forced by `monkeypatch.setattr(build_exe_module, "_dist_nuitka_exists", lambda: True)`. PASS.
- **Isolation:** Each test constructs its own recorder instances; no shared mutable state. `monkeypatch` is reset between tests by Pytest. PASS.
- **Speed:** 13 new tests are part of the 430-test 19.23s suite. No real subprocess invocations. PASS.
- **Diagnostics:** Assertions reference specific tokens (`assert "--standalone" in argv`, `assert rc == code`); a regression would name the missing flag or the mismatched return code. PASS.
- **AAA discipline:** Every `test_` function has Arrange (recorder construction or monkeypatch setup), Act (call to `main` or to `resolve_nuitka_command`), Assert (specific check on stdout / recorder / return value). PASS.

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | Hand-reviewed; no tokens, credentials, or hardcoded paths beyond the `REPO_ROOT`-relative argv. |
| No unsafe subprocess construction | PASS | The subprocess seam call uses a `list[str]` argv (no `shell=True`); the executable is `sys.executable`, not user input. The pre-authorized `# noqa: S603` is justified. |
| Input validation at boundaries | PASS | `argparse` validates the `--dry-run` / `--clean` flags; no other user input. The argv contract is fixed in `resolve_nuitka_command`. |
| Error handling remains explicit | PASS | Non-zero subprocess exit codes are propagated, not swallowed. The four-way parametrize verifies propagation. |
| Configuration / path handling is safe | PASS | All paths are derived from `REPO_ROOT` (anchored deterministically off `__file__`). No `cwd`-dependent paths. |
| Schema constraints match code constraints | N/A | No JSON schemas in this feature. |

## Research Log

No external research required. The issue body documents the Nuitka 4.x MSVC auto-detection behavior, the canonical `--enable-plugin=pyside6` flag, and the rationale for explicit `--include-package=pandas` and `--include-package=openpyxl` (avoiding module-graph auto-detection). The implementation follows the issue verbatim.

## Verdict

The initial implementation satisfies all ten acceptance criteria with focused, minimal changes (one new production module, one new test module, one Poetry script-entry line, one quality-tier classification). The PowerShell-irrelevant gates (no PowerShell, TypeScript, or C# files changed) are not invoked. The Python toolchain (Black, Ruff, Pyright, Pytest) is green in a single pass; coverage is above the uniform 85% LINE / 75% BRANCH thresholds on the changed file (97% LINE / 100% BRANCH); the only suppression is a pre-authorized `# noqa: S603` whose comment text matches the policy pattern verbatim. The branch is ready for merge.

**Cycle-0 exit gate:** `blocking_count == 0`. No remediation cycle required.
