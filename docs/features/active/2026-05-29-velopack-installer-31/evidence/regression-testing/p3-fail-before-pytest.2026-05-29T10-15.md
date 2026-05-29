# Phase 3 — Fail-before pytest evidence [expect-fail] (exception dossier)

Timestamp: 2026-05-29T10-15

Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -x` (would be)

EXIT_CODE: not run (see below)

Output Summary: Fail-before exception dossier.

WhyFailingRunImpossible: The Phase 3 tests (`test_resolve_upload_command_argv_shape`, `test_redact_token_replaces_token_in_argv`, `test_upload_without_github_token_exits_two`, `test_upload_with_token_runs_pack_then_upload`, `test_upload_skipped_when_pack_fails`, `test_main_rejects_invalid_version_before_any_seam_call`) were authored in P1-T1 together with the Phase 1 tests so that Pyright strict mode would not flag the recorder helper classes as unused. The Phase 1 fail-before run (see `p1-fail-before-pytest.2026-05-29T10-15.md`) captured the structural ModuleNotFoundError for the entire test file — including every Phase 3 case.

Alternative proof: artifact `p1-fail-before-pytest.2026-05-29T10-15.md` records EXIT_CODE 1 with `ModuleNotFoundError: No module named 'src.build_velopack'` collected at line 117 before any Phase 3 test could run.

SearchScope: docs/features/active/2026-05-29-velopack-installer-31/evidence/regression-testing/
SearchPatterns: p3-fail-before*.md, p1-fail-before*.md
SearchResult: p1-fail-before-pytest.2026-05-29T10-15.md present.
