---
description: "TypeScript-specific code change rules layered on top of the general code change policy"
applyTo: "**/*.ts"
name: typescript-code-change-policy
---

# TypeScript Code Change Policy

This policy **extends** `general-code-change.instructions.md` and applies to all **TypeScript source, test, and script files** (`*.ts`) in this repo.

These instructions assume TypeScript is built with **TypeScript 5.x (or newer)** targeting an **ES2022** JavaScript baseline.

You must:

- Apply **all** rules in the general code change policy.
- Apply **all** TypeScript-specific rules in this file.
- Apply the unit test policies (`general-unit-test.instructions.md` and `typescript-unit-test.instructions.md`) for any work involving TypeScript tests.

If you encounter any conflicting instructions between these documents, **halt and notify the user.**

---

## 1. Tooling & Baseline for TypeScript

These are the required tools for TypeScript code in this repo:

1. **Formatting — Prettier**

   - All TypeScript must be formatted with the repository’s Prettier configuration.
   - Do not hand-format; if a diff disagrees with Prettier, Prettier wins.
   - Approved command: `npm run format`

2. **Linting — ESLint**

   - TypeScript must pass ESLint using the repository’s configuration.
   - Prefer fixing root causes over suppressions.
   - Approved command: `npm run lint`

3. **Type checking — TypeScript compiler (TSC)**

   - TypeScript must pass the repository’s type-check.
   - Avoid `any` (implicit or explicit). Prefer `unknown` plus narrowing.
   - Approved command: `npm run typecheck`

4. **Testing — Jest**

   - TypeScript unit tests must pass Jest.
   - Approved command: `npm run test:unit`

> **Important:** The general code change policy requires the full toolchain loop: formatting → linting → type checking → testing.

---

## 2. TypeScript Design & Typing Principles

These refine the general design principles for TypeScript code.

1. **Strong typing by default**

   - Public functions, methods, and exported APIs must have clear, intentional types.
   - Avoid type assertions (`as X`) unless you can justify why the value is safe; prefer runtime guards.

2. **Prefer explicit domain types**

   - Model domain concepts with interfaces/types that encode invariants.
   - Prefer discriminated unions for state machines and event shapes.

3. **Avoid cleverness**

   - Keep code readable in one pass.
   - Favor small helpers and early returns over deeply nested branching.

4. **Separation of concerns**

   - Keep pure logic separate from:
     - VS Code extension APIs
     - filesystem/network I/O
     - UI/presentation wiring
   - Write core logic so it can be unit tested without VS Code host processes.

---

## 3. Imports, Modules, and Dependencies

1. **Modules**

   - Use ES modules. Do not introduce CommonJS patterns (`require`, `module.exports`).
   - Prefer explicit imports; avoid barrel exports that obscure dependencies unless the repo already uses them for that area.

2. **Dependencies**

   - Do not add new runtime dependencies unless explicitly approved.
   - If a dependency is unavoidable:
     - Prefer widely used, well-maintained packages.
     - Keep dependency surface area small (wrap behind a typed adapter when practical).

---

## 4. Error Handling and Logging

- Fail fast with clear errors when invariants are violated.
- Avoid catch-all `catch (e)` without rethrowing or adding context.
- Use the repo’s established logging/telemetry patterns (where present) instead of ad-hoc `console.log` for permanent behavior.

---

## 5. Suppressions and Escape Hatches

Suppressions are sometimes necessary, but they must be rare, tightly scoped, and well-justified.

**Authorization requirement:**

- Suppressions are allowed without explicit approval only when they match a **pre-authorized pattern** `typescript-suppressions.instructions.md`.
- Any broader suppression (for example, disabling multiple rules, disabling a whole file, or using `@ts-ignore`) requires **explicit user approval**.

**If you encounter an error that seems to require a suppression not matching a pre-authorized pattern:**

1. First, attempt to resolve it without a suppression (refactor, restructure, adjust types).
2. If that fails, try at least five more distinct approaches.
3. Continue iterating until you solve the problem or demonstrate why each approach fails.
4. Only after multiple documented failed attempts may you request user approval, providing:
    - The specific rule/error and diagnostic code
    - Each approach you tried and why it failed
    - Why a suppression is the only remaining option

All rules for ESLint and TypeScript suppressions are defined in:

- `typescript-suppressions.instructions.md`

---

## 6. Public APIs and Compatibility

- Avoid breaking changes to exported APIs unless explicitly required.
- If a breaking change is necessary, update all callers in-repo and add/adjust unit tests that lock in the new contract.

---

## 7. Project Organization, Naming, and Documentation

1. **Project organization**

   - Follow the repository’s established folder and responsibility layout when adding new code.
   - Keep VS Code extension API wiring and other I/O boundaries thin; push complex logic into pure, testable helpers/services.

2. **File naming**

   - Prefer **kebab-case** filenames for new files (for example, `user-session.ts`, `task-runner.ts`) unless the surrounding area of the repo already uses a different convention.

3. **TypeScript naming conventions**

   - Use **PascalCase** for classes, interfaces, enums, and type aliases; use **camelCase** for functions, methods, variables, and object properties.
   - Do not introduce interface prefixes like `I` (for example, prefer `UserSession` over `IUserSession`).

4. **Documentation expectations**

   - Add JSDoc to exported/public APIs when it improves clarity for callers.
   - When JSDoc is used and intent is non-obvious, prefer including a short rationale (and add `@example` / `@remarks` where it materially improves correct usage).

---

## 8. Security, Configuration, and External Integrations

1. **Input validation and safety**

   - Treat all external input as untrusted (user input, files, network responses, VS Code configuration).
   - Prefer explicit runtime validation (type guards / schema validation) at trust boundaries.
   - Avoid dynamic code execution and avoid rendering untrusted content as HTML without proper escaping/sanitization.

2. **Secrets and configuration**

   - Never hardcode secrets. Use the repo’s secure storage / configuration patterns.
   - Guard against missing configuration (`undefined`) and surface clear errors when required configuration is absent.
   - If you introduce new configuration keys, document them and add/update unit tests around validation and defaults.

3. **External integrations (network / I/O)**

   - Instantiate expensive clients outside hot paths and inject them for testability.
   - For network or I/O operations, use clear error mapping and add context when rethrowing.
   - Where applicable, apply retries/backoff and cancellation/timeout handling consistent with the repo’s existing patterns.

---

## 9. UI/UX and Lifecycle Hygiene (VS Code Extension Context)

1. **UI layering**

   - Keep UI layers thin; push business logic into services or pure functions.
   - Prefer events/messaging to decouple UI from domain logic.

2. **Lifecycle and disposal**

   - Dispose resources deterministically and match existing initialization/disposal sequencing.
   - When introducing long-lived services, consider explicit lifecycle hooks (for example, `initialize()` and `dispose()`) and unit tests that lock in lifecycle behavior.

---

## 10. Performance and Reliability

- Avoid obvious hot-path allocations and repeated heavy work.
- Prefer lazy-loading heavy dependencies when it materially reduces startup/activation cost.
- Debounce or batch high-frequency events (for example, configuration changes) to avoid thrash.
- Track resource lifetimes to prevent leaks (timers, listeners, file watchers, disposables).
