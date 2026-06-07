# Cap Precheck — Phase 4 (BuildSpecProvider at composition root)

Timestamp: 2026-06-05T20-28
Cap: 500 lines per file.

Pre-change line count:
- src/gui/app.py: 497 (EXTRACTION-AT-RISK, 3 below cap)

Decision: EXTRACTION REQUIRED. The production BuildSpecProvider construction
(key-to-schema mapping, required/optional split, key-pattern rendering, masked
preview slice) is implemented in a dedicated factory module
`src/gui/_schema_provider_factory.py` (a `build_spec_provider(service)` factory).
app.py adds only a single import and a single construction/threading line, so it
stays within the cap.

Post-change app.py projection: ~497 + ~5 (import + construct + pass-through arg)
= ~502 before offset. To stay <= 500, the provider is constructed and passed via
the discovery/gating wiring's new `spec_provider` parameter without adding a local
helper to app.py. Final app.py line count is verified in P7-T8; if it exceeds 500
after wiring, the construction line is folded into the existing
`wire_schema_discovery_and_gating` call argument.
