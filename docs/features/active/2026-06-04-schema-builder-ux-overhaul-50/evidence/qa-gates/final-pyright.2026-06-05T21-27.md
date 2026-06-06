# Final QA — Pyright (Cycle 2)

Timestamp: 2026-06-05T21-27
Command: env -u VIRTUAL_ENV poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations (strict mode).

Loop note: An earlier pass surfaced 5 strict-mode errors caused by importing the two
shared helpers across modules under leading-underscore (private) names:
`reportUnusedFunction` on the fixtures module and `reportPrivateUsage` at the three
import sites. Resolved by giving the two shared helpers public names
(`configure_valid_keyable_view`, `stored_schema_with_structured_key_and_aggregate`),
matching the established repo convention for shared test helpers
(`tests/gui/_wiring_test_doubles.py` exports public `fabricated_imports`). Only the
function-symbol names changed; every helper body line and every assertion remained
byte-identical (verified per P1-T5 / P2-T9). The loop restarted from Black after the
rename; this recorded pass is the clean single-pass result.
