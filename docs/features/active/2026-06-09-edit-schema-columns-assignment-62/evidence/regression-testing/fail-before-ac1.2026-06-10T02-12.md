# Fail-Before Evidence — AC-1 (Issue #62, P1-T2)

Timestamp: 2026-06-10T02-12
Command: poetry run pytest tests/gui/test_columns_tab_presenter.py::test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool
EXIT_CODE: 1

Procedure: The production change in src/gui/presenters/_columns_tab_presenter.py
(the `_seed_from_persisted_aliases` second pass) was stashed via
`git stash push -- src/gui/presenters/_columns_tab_presenter.py`, then the new
AC-1 test was executed against the unpatched presenter.

Output Summary:
- 1 failed.
- Assertion: `assert ('Customer', 'cust_col') in view.assignments` failed because
  the unpatched presenter pushed `[('Customer', None), ('Sales', None)]` — every
  aliased row rendered unassigned, reproducing the issue #62 root cause (persisted
  aliases never reflected into `consumed_columns` when the source pool is empty).
- After restoring the production fix (`git stash pop`), the same test passes
  (see final-pytest evidence). This establishes fail-before / pass-after for AC-1.
