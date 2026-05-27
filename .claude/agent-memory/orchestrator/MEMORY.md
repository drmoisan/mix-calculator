# Orchestrator Memory Index

- [normalize-le file-size ceiling](normalize-le-file-size-ceiling.md) — src/normalize_le.py is at 495/500 lines; extract, don't add in place, for future work there
- [CI required checks enforceable](ci-required-checks-enforceable.md) — main has 5 required checks (CodeQL, dep-review, py3.12/3.13, actionlint); S9 CI gate is live, verify via gh
- [Evidence + lifecycle for every change](evidence-and-lifecycle-for-every-change.md) — evidence only under a feature folder; promote to issue + active folder before ANY implementation, even 1-file tooling fixes
- [Small-path = minor-audit selection](small-path-minor-audit-selection.md) — 1-3 production-file bug = small path + minor-audit, no spec.md, AC lives in issue.md
