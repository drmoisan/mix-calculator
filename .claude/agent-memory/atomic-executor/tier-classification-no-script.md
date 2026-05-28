---
name: tier-classification-no-script
description: This repo's quality-tiers.yml tier-classification "stage" has no enumeration script; existing YAML classifies only non-marker modules plus src/__init__.py
metadata:
  type: project
---

`quality-tiers.yml` at repo root maps `src/**` module paths to tiers (T1-T4). The
`tier-classification` CI stage is described in `.claude/rules/quality-tiers.md` as
conceptual; there is no dedicated enumeration script in the repo that globs every
`.py` under `src/` and fails on an unclassified file. `.github/workflows/_python-quality.yml`
only references the coverage gate, not tier enumeration.

**Why:** Affects how "every module is classified" verification tasks must run — they
rely on a `poetry run python -c` enumeration against the YAML, not a packaged check.

**How to apply:** When a plan adds new `src/` subpackages, decide deliberately whether
subpackage `__init__.py` markers need YAML entries. The pre-existing `quality-tiers.yml`
classifies only `src/__init__.py` (no subpackage markers exist yet) plus all non-marker
modules. A plan that classifies the top-level package marker but omits subpackage markers,
while also asserting "every `src/gui/**` module is classified," is internally inconsistent
and should resolve the marker-classification policy before execution. See [[pandas-pyright-stubs]].
