# Acceptance-Criteria Re-Confirmation (Cycle 2, P2-T9)

Timestamp: 2026-06-05T21-27
Work Mode: full-feature -> AC sources are `spec.md` AND `user-story.md`.

This Cycle-2 remediation addresses only B1 (test-file split) and N4 (coverage-config
change). It changes no production feature behavior. This artifact re-confirms that no
acceptance criterion regressed and that the test split preserved every assertion and
parametrize case.

## (a) AC checkbox state — no regression

Verified directly against the requirement files:

- spec.md (## Acceptance Criteria): 22 AC checkboxes total; 22 checked `[x]`,
  0 unchecked `[ ]`. No checkbox was flipped from `[x]` to `[ ]` by this cycle.
- user-story.md (## Acceptance Criteria): 16 AC checkboxes total; 16 checked `[x]`,
  0 unchecked `[ ]`. No checkbox was flipped by this cycle.

Criterion text was not altered. No new AC was added or removed. Because this cycle
changes no feature, the ACs remain proven by the existing 932-test suite (all
passing under QT_QPA_PLATFORM=offscreen, final-pytest.2026-06-05T21-27.md).

## (b) Test-split fidelity (P1-T5 confirmation)

The B1 split moved every test from the 506-line
tests/gui/test_schema_builder_presenter.py into
tests/gui/test_schema_builder_presenter_core.py (13 functions, one parametrized to 3
cases) and tests/gui/test_schema_builder_presenter_seeding.py (5 functions), with the
two shared helpers in tests/gui/_schema_builder_presenter_fixtures.py.

Fidelity evidence:
- assert-count parity: original (git HEAD) had 51 `assert` statements; the two new
  modules contain 51 `assert` statements combined.
- parametrize parity: original had 1 `@pytest.mark.parametrize` (3 cases); the new
  core module has 1 `@pytest.mark.parametrize` (3 cases).
- collected-item parity: 20 pre-split == 20 post-split
  (test-count-parity.2026-06-05T21-27.md).
- No skip/xfail/weakening introduced (masking-scan.2026-06-05T21-27.md).

## AC Status Summary

- Source: docs/.../spec.md (## Acceptance Criteria) and docs/.../user-story.md
  (## Acceptance Criteria)
- spec.md — Total AC items: 22; Checked off (delivered): 22; Remaining: 0
- user-story.md — Total AC items: 16; Checked off (delivered): 16; Remaining: 0
- Items remaining: none
- No AC regressed by Cycle 2; split fidelity confirmed.
