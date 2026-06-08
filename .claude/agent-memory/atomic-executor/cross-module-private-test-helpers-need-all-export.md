---
name: cross-module-private-test-helpers-need-all-export
description: Splitting a test file that shares an underscore-prefixed helper trips strict Pyright reportPrivateUsage; relocate the helper into an underscore-prefixed module with __all__
metadata:
  type: feedback
---

When a test-file split forces an underscore-prefixed helper (e.g. `_patch_loaders`,
`_load_default`, `_MONTHS_A`) to be imported across modules, strict Pyright raises
`reportPrivateUsage` because the importing module reads a private name from a
public module. Importing the name verbatim from the original public test module
fails the type-check gate.

**Why:** pyproject sets `typeCheckingMode = "strict"` with no reportPrivateUsage
override. Pyright suppresses the rule only when the private name is exported via
`__all__`. The repo's established pattern is `tests/_mix_rollups_fixtures.py`:
shared private test helpers live in a dedicated **underscore-prefixed module** that
declares `__all__ = ["_f", "_mix_base_fixture", ...]`.

**How to apply:** when a plan says to import a shared private helper from the
original module, instead relocate it into a new underscore-prefixed fixtures module
(`tests/.../_<area>_fixtures.py`) with an `__all__` listing the exported private
names, and have both the original and new modules import from there. This is the
in-scope "relocate shared helpers" action and needs no suppression. Watch the
follow-on Ruff TC002/TC003: once a helper's only remaining use of an import is a
type annotation, move that import (pandas, io, SchemaDefinition) into a
`if TYPE_CHECKING:` block. See [[rerouting-loader-breaks-stale-monkeypatches]] for
the related monkeypatch-retargeting hazard in the same #58 test suite.
