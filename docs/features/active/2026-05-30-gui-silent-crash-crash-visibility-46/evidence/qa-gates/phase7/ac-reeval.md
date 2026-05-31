# Phase 7 — AC Re-Evaluation (Cycle 2)

- Timestamp: 2026-05-31T03-25

## AC-12 (file-size cap)

Status: [x] (unchanged on the literal production-only spec scope; cross-cutting cap now enforced on test code via the R5 split).

Spec line: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md` line 225.

Cycle-2 update appended under AC-12 (see line 227): the R5 split moves the `_FakePath` / `_FakeHandle` fixture pair and the three R4 closure-invocation tests from `tests/gui/test_crash_handler.py` (was 549, over the cross-cutting cap by 49) into a new sibling `tests/gui/test_crash_handler_closures.py` (258). The original file is now 332 lines. Both files are under the cap; the cycle-2 driver (R5) is the cross-cutting cap defined in `.claude/rules/general-code-change.md`, not a violation of AC-12's literal spec text.

Verification evidence:
- `evidence/qa-gates/phase8/file-sizes.md` — post-cycle-2 table includes the four test files plus the bootstrap module; every row shows `PASS`.
- `evidence/qa-gates/phase4/single-pass-summary.md` — single-pass green QA loop (black / ruff / pyright / pytest all EXIT_CODE 0).
- `evidence/qa-gates/phase8/pytest.md` — 737 passed; `src/gui/_crash_handler.py` 100% line / 100% branch; three closure tests now collected from `tests/gui/test_crash_handler_closures.py`.

## Other AC items

AC-1..AC-11 statuses are unchanged from the cycle-1 post-state. Cycle 2 introduces no new behavior, no new dependency, no new suppression marker, and no test rename/delete/addition beyond the relocation. The total test count is unchanged at 737.

## spec.md Last Updated

Bumped from `2026-05-31T02-43` to `2026-05-31T03-25` to reflect the cycle-2 R5 remediation note appended under AC-12.
