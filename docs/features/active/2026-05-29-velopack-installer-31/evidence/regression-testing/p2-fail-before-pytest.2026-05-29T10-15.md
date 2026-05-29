# Phase 2 — Fail-before pytest evidence [expect-fail] (exception dossier)

Timestamp: 2026-05-29T10-15

Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -x` (would be)

EXIT_CODE: not run (see below)

Output Summary: Fail-before exception dossier.

WhyFailingRunImpossible: The Phase 2 tests (`test_main_dry_run_prints_argv_and_does_not_invoke_seam`, `test_main_clean_removes_dist_velopack`, `test_main_propagates_seam_returncode`, `test_main_clean_then_invokes_seam`, `test_main_exits_two_when_app_exe_missing`, `test_main_exits_two_when_icon_missing`) were authored in P1-T1 together with the Phase 1 tests, because Pyright strict mode flags the recorder helper classes (`_RunVpkRecorder`, `_RemoveTreeRecorder`, `_OrderedCallLog`) as unused private members unless the Phase 2 tests reference them. The Phase 1 fail-before run (see `p1-fail-before-pytest.2026-05-29T10-15.md`) recorded the structural ModuleNotFoundError for the entire test file — including the Phase 2 cases — so a separate Phase 2 fail-before run would not surface new information.

Alternative proof: artifact `p1-fail-before-pytest.2026-05-29T10-15.md` records EXIT_CODE 1 with `ModuleNotFoundError: No module named 'src.build_velopack'` collected before any Phase 2 test could run. That single failure represents the fail-before state for every test in the file.

SearchScope: docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/
SearchPatterns: p2-fail-before*.md, p1-fail-before*.md
SearchResult: p1-fail-before-pytest.2026-05-29T10-15.md present.
