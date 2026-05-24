---
paths:
  - "**/*.py"
description: Python-specific toolchain and coding standards.
---

# Python Code Standards

This rule file summarizes the Python-specific policies for this repository.

## Toolchain

1. **Formatting — Black**: All Python code must be formatted with Black (default settings). Command: `poetry run black .`
2. **Linting — Ruff**: Python code must pass Ruff using the project configuration. Command: `poetry run ruff check .` Suppressions require pre-authorization per `python-suppressions.instructions.md` or explicit user approval.
3. **Type Checking — Pyright**: All Python code must be fully type-annotated and pass Pyright. Avoid `Any` unless unavoidable and commented. Command: `poetry run pyright`
4. **Testing — Pytest**: All tests use Pytest. Coverage thresholds are uniform across tiers per `.claude/rules/quality-tiers.md` (>= 85% line, >= 75% branch). Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

Run the toolchain in order: format → lint → type-check → test. Restart from step 1 if any step fails or changes files. Do not stop the loop until all four steps complete without errors in a single pass.

If the environment prevents running tools, stop implementation and provide a plan and proposed diffs only, clearly marked **unverified**.

## Coding Standards

- **PEP 8 naming**: `snake_case` for functions/methods/variables, `PascalCase` for classes/exceptions, `CONSTANT_CASE` for module constants.
- **Strong typing**: All public functions and methods must have full type hints for parameters and return values.
- **Dataclasses**: Prefer `@dataclass` for value objects. Use `frozen=True` where appropriate. Enforce invariants in `__post_init__` (dataclasses) or `__init__`.
- **Protocols**: Use `typing.Protocol` or `abc.ABC` when multiple implementations are expected.
- **Imports**: Prefer absolute imports. Avoid circular dependencies.
- **Error handling**: Fail fast with specific exceptions. Avoid broad `except:` or `except Exception:` without context. Reserve broad handlers for well-defined boundaries (CLI/entrypoints) with context logging.
- **Assertions**: Use `assert` only for internal sanity checks, not for user-facing validation.
- **Logging**: Use the standard `logging` module. No ad-hoc `print` statements for permanent behavior.

## Python Design Rules

### Small, cohesive modules

- Each class or module has one clear purpose. Avoid grab-bag utilities.
- Prefer explicit names and straightforward control flow.
- Keep the public surface area small. Internal helpers are `_prefixed` or live in `_internal` modules.

### Classes vs functions

Create a class when at least one of the following is true:

- A clear domain concept with data and behavior.
- State and invariants must travel together.
- Multiple implementations behind a common interface are expected.
- A multi-step workflow shares context across steps.

Create a standalone function when:

- The operation is pure, stateless, and simple.
- It is a small helper that does not naturally belong on a specific domain class.
- It is a simple transformation from inputs to outputs.

Keep methods small and focused. Avoid god objects that know about too many unrelated concerns. Avoid long, deeply branching functions; factor logic into smaller helpers.

### Strong typing by default (Pyright-clean)

- All public functions, methods, and constructors must have complete type hints.
- Avoid `Any`. If unavoidable, isolate it by wrapping untyped libraries behind small typed adapters.
- Use line-specific `# type: ignore[...]` only when justified with a brief comment.
- Prefer `typing.Protocol` (or `abc.ABC`) only when multiple implementations are expected.

### Dependency seams (testability without frameworks)

Introduce the smallest seam that enables reliable testing:

- Inject collaborators via constructor parameters (preferred).
- Accept optional callables with sensible defaults for time/randomness (for example, `clock: Callable[[], datetime] = datetime.now`).
- Extract boundary interactions into a tiny helper function and patch that helper in tests.

Do not introduce generic service-locator patterns or heavy dependency-injection frameworks.

## Pytest Rules

- Use **Pytest** as the test runner.
- One behavior per test. Follow Arrange–Act–Assert structure.
- Use descriptive `test_...` function names.
- Prefer behavioral assertions over implementation detail.
- Use `pytest.mark.parametrize` for boundary matrices.
- Fixtures should be narrow by default (function scope unless justified).
- Mock sparingly; prefer real pure code paths. Use `monkeypatch` for environment variables and module attributes.
- Patch at the **import location used by the unit under test**, not where a symbol originated.
- No sleeps, retries, or timing hacks.
- Organize tests to mirror code structure (for example, `tests/test_module_name.py` for `module_name.py`).
- No external dependencies (network, databases, external processes, runtime filesystem temp files) in unit tests.
- Line coverage must remain >= 85% across all tiers (T1–T4) per `.claude/rules/quality-tiers.md`.
- Branch coverage must remain >= 75% across all tiers (T1–T4).
- Coverage regression on changed lines is a blocking finding.

## Prohibited Behaviors

- Broad refactors across multiple modules outside the approved scope.
- Adding new dependencies without explicit user instruction.
- Reducing typing strictness to make Pyright pass.
- Weakening tests to make them pass (removing assertions, overbroad exception checks).
- Using runtime temp files or external services in unit tests.
- Claiming success without running the toolchain.
