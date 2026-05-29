# Phase 3 fail-before evidence — `main()` orchestration tests

Timestamp: 2026-05-29T00-00
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_build_exe.py -k "main_dry_run or main_clean or main_invokes_seam or main_uses_default" --no-header`
EXIT_CODE: 1

Output Summary:
- 8 failed, 5 deselected in 0.22s.
- All failures are attributable to the Phase-1 stub `main()` raising
  `NotImplementedError` or to the absence of the `run_nuitka`/`remove_tree`
  parameters and the `_dist_nuitka_exists` / module-level `subprocess` /
  `shutil` references that Phase 3 introduces:
  - `test_main_dry_run_prints_argv_and_does_not_invoke_seam`
  - `test_main_clean_removes_existing_dist_tree`
  - `test_main_invokes_seam_and_propagates_returncode[0|1|2|137]` (4 parametrized cases)
  - `test_main_clean_flag_then_invokes_seam`
  - `test_main_uses_default_seams_when_unspecified` (fails at the monkeypatch
    line: `AttributeError: module 'src.build_exe' has no attribute 'subprocess'`)
- Expected pre-implementation state. P3-T7 (implement `main`) is the next task.
