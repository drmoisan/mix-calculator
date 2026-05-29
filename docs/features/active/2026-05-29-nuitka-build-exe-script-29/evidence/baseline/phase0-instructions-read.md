# Phase 0 — Instructions Read

- Timestamp: 2026-05-29T00-00
- Policy Order:
  1. `.claude/rules/general-code-change.md`
  2. `.claude/rules/general-unit-test.md`
  3. `.claude/rules/quality-tiers.md`
  4. `.claude/rules/python.md`
  5. `.claude/rules/python-suppressions.md`
  6. `.claude/rules/self-explanatory-code-commenting.md`
  7. `.claude/rules/tonality.md`

## Files Read (absolute paths)

- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\general-code-change.md
- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\general-unit-test.md
- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\quality-tiers.md
- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\python.md
- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\python-suppressions.md
- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\self-explanatory-code-commenting.md
- c:\Users\DanMoisan\repos\mix-calculator\.claude\rules\tonality.md

## Mode-Source Verification

- Resolved mode: `minor-audit`
- Marker source: `issue.md` line 9 (`- Work Mode: minor-audit`)
- AC source: `docs/features/active/2026-05-29-nuitka-build-exe-script-29/issue.md` `## Acceptance Criteria` section
- AC identifiers verified present: AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10

## GitignoreBaseline

- Literal matching line from `.gitignore` (line 2): `dist`
- Decision rule for P4-T2: `dist` at the top of `.gitignore` already covers `dist/nuitka/` (and any subpath under `dist`). Therefore P4-T2 is a NO-OP — do NOT append `dist/nuitka/`.

## PyProjectBaseline

`[tool.poetry.scripts]` existing entries (verbatim):

- `normalize-le = "src.normalize_le:main"`
- `load-aop = "src.load_aop:main"`
- `mix-pipeline-gui = "src.gui.app:main"`

Confirmation: `build-exe` is NOT yet present.

## CompileTargetVerified

`src/gui/app.py` line 475: `def main(argv: list[str] | None = None) -> int:`

The signature is at module scope, satisfies the `src.gui.app:main` entry-point referenced by `mix-pipeline-gui`, and is the compilation target for `build-exe`.
