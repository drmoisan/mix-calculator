---
paths:
  - "**/*.py"
description: Pre-authorized Python Ruff and Pyright suppression patterns. Applies to Python files.
---

# Python Suppression Policy

This rule file summarizes the suppression authorization policy for Python code.

## Authorization Requirement

All `# noqa` and `# type: ignore` suppressions must either:
1. **Match a pre-authorized pattern** defined in this file, OR
2. **Have explicit user approval** for that specific suppression.

**Escalation path before requesting approval:**
1. First, attempt to resolve the error without a suppression (refactor, restructure, use approved patterns).
2. If that fails, try at least five more distinct approaches.
3. Continue iterating until you solve the problem or clearly demonstrate why each approach fails.
4. Only after multiple documented failed attempts may you request user approval, providing: the specific rule/error code, each approach tried and why it failed, and why a suppression is the only remaining option.

## Pre-Authorized `# noqa` Patterns

### S603 — Subprocess with validated executable

**When authorized:** Subprocess calls where the executable is validated via `shutil.which()` before use.

**Required comment format:** `# noqa: S603 - static analysis can't verify runtime validation`

**Rationale:** Cross-platform compatibility requires runtime PATH resolution. Static analysis cannot trace the runtime validation, but the code is safe because the executable path is resolved from PATH (not user input), existence is verified before use, and hardcoding platform-specific paths would break portability.

---

### ARG002 — Unused method argument in test mocks

**When authorized:** Test mock/stub implementations that must match interface signatures but do not use all parameters. Must be in test code (`tests/` directory) implementing a known interface.

**Required comment format:** `# noqa: ARG002 - mock API signature` or `# noqa: ARG002 - match [InterfaceName] API`

---

### B008 — Function call in default argument (Typer)

**When authorized:** Typer CLI option declarations where `Option()` must be evaluated at import time for CLI metadata. Must be a Typer option declaration in a CLI function signature.

**Required comment format:** `# noqa: B008 - Typer framework pattern`

---

### TCH002 / TCH003 — Type checking block violations

**When authorized:** Modules used for both runtime and type hints (pytest fixtures, Typer type hints, runtime `isinstance` checks). The module must be used at runtime and cannot be moved to a `TYPE_CHECKING` block without breaking functionality.

**Required comment format:** `# noqa: TCH002 - [module] required at runtime for [reason]` or `# noqa: TCH003 - [module] required at runtime for [reason]`

---

### S310 — URL open with urllib (trusted endpoints)

**When authorized:** Accessing documented, trusted HTTPS API endpoints with timeout. URL must be a validated HTTPS endpoint, domain must be a documented trusted source, timeout must be set, and the URL must not come from user input.

**Required comment format:** `# noqa: S310 - trusted HTTPS endpoint: [domain]`

---

### S314 — XML parsing with ElementTree (trusted sources)

**When authorized:** Parsing user's own local files (EPUB, configuration) or known-safe data sources (Wikipedia dumps, curated datasets). Must NOT be parsing untrusted network data.

**Required comment format:** `# noqa: S314 - parsing trusted [source type]`

---

### BLE001 — Blind except (CLI entry points only)

**When authorized:** Top-level CLI exception handlers for user-friendly error messages and clean exits. Must be at a CLI entry point, must log or display the error with context, and must exit cleanly. NOT allowed in library or internal code.

**Required comment format:** `# noqa: BLE001 - CLI top-level error handling`

---

### S301 — Pickle deserialization (trusted model artifacts)

**When authorized:** Loading known model artifacts from hardcoded trusted local paths. Path must be hardcoded or validated (not from user input or CLI args). Only for ML model/artifact loading.

**Required comment format:** `# noqa: S301 - trusted model artifact from hardcoded path`

---

### S108 / S105 — Hardcoded paths/passwords in tests only

**When authorized:** Test fixtures with example paths and test data literals. Must be in test code only. Not actual secrets or production paths.

**Required comment format:** `# noqa: S108 - test fixture path` or `# noqa: S105 - test fixture data`

---

## Pre-Authorized `# type: ignore` Patterns

### import-untyped — Optional third-party dependency without stubs

**When authorized:** Optional third-party dependencies that lack type stubs or `py.typed` marker. Import must be in a `try/except ImportError` block; library must be optional; no type stubs available; library lacks `py.typed` marker.

**Required comment format:** `# type: ignore[import-untyped]` with a comment on the same or adjacent line explaining the library and why stubs are absent.

---

## Explicitly Not Authorized (with Required Workarounds)

### S110 — `try`-`except`-`pass` fallback chains

**Not authorized.** Use explicit platform detection via `shutil.which()` or environment variable checks instead. `try`-`except`-`pass` chains hide lazy design and make behavior unpredictable.

**Workaround:** Resolve the correct method at design time using `shutil.which()` for executables or explicit platform detection. Cache the result to avoid repeated detection overhead.

---

### TID252 — Relative imports beyond top-level package

**Not authorized.** Use absolute imports (`from project.module import Thing`) instead of parent-relative imports (`from ..module import`).

---

### S607 — Starting process with partial executable path

**Not authorized.** Resolve executables via `shutil.which()` first; use the full path returned by `which()`. This satisfies both S607 and the pre-authorized S603 pattern.

---

### D401, F401, UP017

**Not authorized.** Fix the root cause: rewrite docstrings in imperative mood (D401), remove unused imports (F401), and use timezone-aware datetime (UP017).

---

## Policy Enforcement Checklist

Before using any suppression, verify:
- [ ] Pattern exactly matches a pre-authorized pattern above.
- [ ] Required comment format is used verbatim.
- [ ] All contextual requirements are met (e.g., in tests/, validated path, try/except block).
- [ ] Suppression scope is as narrow as possible (single line, not file-level).
