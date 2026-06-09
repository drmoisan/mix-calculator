# T1 Mutation Obligation Note for src/schema_loader.py (P4-T8)

Timestamp: 2026-06-08T14-30

`src/schema_loader.py` carries a T1 module rigor classification. Per
`.claude/rules/quality-tiers.md`, T1 modules carry a mutation-score obligation
(mutation score >= 75%) that is executed in the pre-merge / nightly pipeline, not
in the per-commit toolchain loop (mutation testing is explicitly out of scope for
the per-commit format -> lint -> type -> test loop).

Coverage basis for the seam change delivered in this feature:
- The new keyword-only `resolver`/`is_tty`/`prompt` parameters and their
  forwarding into `resolve_key` are covered by:
  - P1-T8 forwarding test: `test_load_forwards_resolver_seams_to_resolve_key_on_divergence`
    asserts the injected resolver is the decision source on a diverging KEY and the
    prompt seam is never reached.
  - P1-T9 property test (T1 property obligation):
    `test_property_resolver_action_governs_key_on_divergence` asserts, over generated
    diverging-KEY inputs, that the resolver's returned action ("trust"/"overwrite")
    governs the resulting KEY column.
  - P1-T10 backward-compatibility test: `test_load_backward_compatible_without_seam_arguments`
    pins the default-seam behavior for existing positional callers.
- `src/schema_loader.py` is at 100% line and 100% branch coverage (32 stmts, 6 branches,
  0 missed, 0 partial) in the final coverage run.

The mutation-score gate itself is satisfied by the pre-merge/nightly pipeline and is
not run as part of this per-commit execution.
