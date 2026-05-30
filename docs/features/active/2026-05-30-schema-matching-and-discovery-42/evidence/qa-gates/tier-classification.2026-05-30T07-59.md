# Final QA — Tier classification of new modules (AC8)

Timestamp: 2026-05-30T07-59
Command: `grep -n "src/(etl_column_probe|schema_matching|_schema_matching_helpers)\.py: T2" quality-tiers.yml`
EXIT_CODE: 0

## New-module classification (this feature's responsibility)

`quality-tiers.yml` classifies all three new feature modules as T2-Core:

```
80:  src/etl_column_probe.py: T2
81:  src/schema_matching.py: T2
85:  src/_schema_matching_helpers.py: T2
```

- `src/etl_column_probe.py: T2` — present (line 80).
- `src/schema_matching.py: T2` — present (line 81).
- `src/_schema_matching_helpers.py: T2` — present (line 85), added when the
  coverage-scoring helpers were split out to keep `schema_matching.py` under the
  500-line cap (plan P4-T1).

AC8 tier requirement for this feature: SATISFIED. Every module introduced by
issue #42 is classified.

## Observation (out of this feature's scope)

A repo-wide enumeration of `src/**/*.py` shows several pre-existing GUI modules
that are not listed in `quality-tiers.yml` (e.g.
`src/gui/_import_dispatch_wiring.py`, `src/gui/_render_exclusivity.py`,
`src/gui/presenters/import_dispatch.py`, `src/gui/_velopack_bootstrap.py`,
`src/gui/_icon.py`, `src/gui/_main_window_view.py`). These were introduced by
other features/branches and are outside the scope of issue #42. They are recorded
here as an observation for the orchestrator; this feature did not introduce them
and the plan does not authorize editing them. PyYAML is not installed in the
environment, so the enumeration was performed with a filesystem glob rather than
parsing the YAML.
