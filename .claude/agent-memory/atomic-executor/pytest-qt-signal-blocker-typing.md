---
name: pytest-qt-signal-blocker-typing
description: pytest-qt SignalBlocker.args is list[Unknown] | None under Pyright strict; cast through a typed Protocol view to contain the unknown member type without a per-call suppression.
metadata:
  type: project
---

`pytest-qt`'s `SignalBlocker.args` is typed `list[Unknown] | None` and trips
Pyright strict's `reportUnknownMemberType` at the access point. The fix is the
same containment pattern the repo uses in `src/pandas_io.py` for pandas members
with unknown overloads: declare a tiny `class _SignalBlockerView(Protocol):
    args: list[object] | None`, then `cast("_SignalBlockerView", blocker).args`.
Read the payload through a second `cast` to its known concrete type (`str`,
`dict[str, pd.DataFrame]`, etc.). No `# type: ignore` is needed and Pyright is
happy.

**Why:** Direct `blocker.args` access surfaces the unknown member type even when
the cast target is `list[object] | None` — the access itself reports unknown
before the cast applies. Pushing the cast onto the blocker view eliminates the
unknown-member at the access site.

**How to apply:** In any GUI/Qt test that reads `qtbot.waitSignal(...)` /
`blocker.args[0]`, define `_SignalBlockerView` locally (test-module scope is
fine — the pattern appears in `tests/gui/test_pipeline_worker.py` and
`tests/gui/test_source_input_widget.py`) and route every `blocker.args` access
through it.

Related: `src/pandas_io.py` uses the same Protocol-view + `cast` containment
pattern for pandas `read_excel`/`read_sql`/`to_sql`. See
[[pandas-pyright-stubs]] for the broader pandas-stubs context.
