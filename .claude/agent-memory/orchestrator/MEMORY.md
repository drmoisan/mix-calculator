# Orchestrator Memory Index

- [normalize-le file-size ceiling](normalize-le-file-size-ceiling.md) — src/normalize_le.py is at 495/500 lines; extract, don't add in place, for future work there
- [CI required checks enforceable](ci-required-checks-enforceable.md) — main has 5 required checks (CodeQL, dep-review, py3.12/3.13, actionlint); S9 CI gate is live, verify via gh
- [Evidence + lifecycle for every change](evidence-and-lifecycle-for-every-change.md) — evidence only under a feature folder; promote to issue + active folder before ANY implementation, even 1-file tooling fixes
- [Small-path = minor-audit selection](small-path-minor-audit-selection.md) — 1-3 production-file bug = small path + minor-audit, no spec.md, AC lives in issue.md
- [MCP tools available to orchestrator](mcp-tools-available-to-orchestrator.md) — if a worker reports MCP gate/lifecycle tools unavailable, run them from the orchestrator yourself, don't accept the block
- [potential_to_issue creates the GitHub issue](potential-to-issue-creates-github-issue.md) — the promotion tool opens the GitHub issue itself; do not also gh issue create (caused a duplicate in #15)
- [Subagents cannot open .xlsx](subagents-cannot-open-xlsx.md) — orchestrator must extract Excel logic via openpyxl and transcribe (value-free) into issue.md for planner/executor
- [Derived aggregates are confidential](derived-aggregates-are-confidential.md) — computed workbook figures (mix totals, sums) must not land in committed files; describe qualitatively, scan before commit
- [S9 CI-gate parser fallback](s9-ci-gate-parser-fallback.md) — Invoke-CiGateParser.ps1 is absent; derive ci_gate from gh pr checks JSON, use gh run watch to wait
- [Remediation loop strict handoff](remediation-loop-strict-handoff.md) — remediation cycles must run atomic-planner -> atomic-executor -> feature-review only; no direct typed-engineer worker calls; five required artifacts per cycle
- [Remediation-plan em-dash required](remediation-plan-em-dash-required.md) — the plan validator rejects `### Phase N (continued) — <Title>`; only canonical `### Phase N — <Title>` passes
- [PySide6 CI system libs](pyside6-ci-system-libs.md) — Ubuntu runner needs libegl1/libgl1/libxkbcommon0/libdbus-1-3/libfontconfig1 plus QT_QPA_PLATFORM=offscreen for pytest-qt to collect
- [asteval approved for formula engine](asteval-approved-for-formula-engine.md) — user approved asteval dependency for the configurable-schema formula engine; no need to re-ask for that specific use
