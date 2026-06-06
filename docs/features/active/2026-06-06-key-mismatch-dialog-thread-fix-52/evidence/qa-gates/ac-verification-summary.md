# AC verification summary (P6-T6) — issue #52

Timestamp: 2026-06-06T13-12

AC source (full-bug mode): spec.md (mirrored in issue.md). All 8 checked off in
both files.

- AC-1 (no cross-thread crash; dialog on GUI thread): PASS.
  Evidence: src/gui/_key_mismatch_bridge.py (same-thread guard + queued
  cross-thread marshaling); tests/gui/test_key_mismatch_bridge.py (same-thread
  direct call, cross-thread marshaling to GUI thread, exception surfaced);
  batch5-bridge-gate.md (bridge 100% line/branch). The bridge constructs/shows
  the modal on the GUI thread regardless of the calling thread, eliminating the
  off-thread QMessageBox construction that produced QBasicTimer::stop.

- AC-2 (2-3 example pairs shown): PASS.
  Evidence: src/etl_key.py::_collect_diverging_examples (truncates to 3, diverging
  rows only); src/gui/_key_mismatch_dialog.py::_format_examples + _qmessagebox_ask
  (renders pairs in body); tests/test_etl_key.py (collector tests),
  tests/gui/test_key_mismatch_dialog.py::test_qmessagebox_renders_example_pairs;
  batch1-etl-key-gate.md, batch4-dialog-seam-gate.md.

- AC-3 (no dialog when KEY matches / no KEY column): PASS.
  Evidence: resolve_key invokes the resolver only in the diverging branch;
  tests/test_etl_key.py::test_resolve_key_resolver_not_invoked_when_matching and
  ...when_no_key_column (resolver call count 0);
  tests/gui/test_pipeline_service_key_seam.py (resolver not invoked on
  no-divergence path). batch1/batch3 gates.

- AC-4 ("Keep existing" -> trust default; "Rebuild" -> overwrite): PASS.
  Evidence: src/gui/_key_mismatch_dialog.py (AcceptRole default = Keep existing;
  DestructiveRole = Rebuild; mapping in build_key_mismatch_resolver);
  tests/gui/test_key_mismatch_dialog.py (default-button + trust/overwrite mapping
  tests). batch4 gate.

- AC-5 (example-aware resolver; invoked only on divergence; PipelineService
  forwards the callable): PASS.
  Evidence: resolver parameter on resolve_key/load_source/load_aop;
  PipelineService.import_le/import_aop forward resolver=self._key_mismatch_resolver
  (no eager call); tests/gui/test_pipeline_service_key_seam.py asserts the
  callable (not its result) is forwarded and not invoked on no-divergence.
  batch1/batch2/batch3 gates.

- AC-6 (CLI stdin path unchanged): PASS.
  Evidence: decide_key_action untouched; resolver defaults to None on every
  loader so the CLI path uses key_mismatch/is_tty/prompt exactly as before;
  tests/test_etl_key.py::test_resolve_key_resolver_none_preserves_cli_path; the
  6 prompt/tty/key_mismatch CLI tests pass (final-pytest-coverage.md).

- AC-7 (all files <= 500 lines, notably normalize_le.py): PASS.
  Evidence: filesize-compliance.md and coverage-delta.md. normalize_le.py reduced
  495 -> 450 via extraction to src/_normalize_le_columns.py (166); app.py at 500;
  all nine changed/added files <= 500.

- AC-8 (full toolchain pass; coverage >= 85% line / >= 75% branch; no regression
  on changed lines): PASS.
  Evidence: final-black.md, final-ruff.md, final-pyright.md (all EXIT 0);
  final-pytest-coverage.md (834 passed; line 99.49%, branch 96.70%);
  coverage-delta.md (no regression vs baseline; all changed modules 100% except
  the one pre-existing app.py fallback line).

Overall verdict: PASS. All AC-1..AC-8 satisfied with cited, verified evidence.
