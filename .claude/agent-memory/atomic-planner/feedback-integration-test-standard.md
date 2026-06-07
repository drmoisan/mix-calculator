---
name: feedback-integration-test-standard
description: For wiring/integration remediation, each closed finding needs a production-call-site (build_application / opened dialog) assertion, not an isolated unit test
metadata:
  type: feedback
---

When planning remediation for integration/wiring defects in this repo, every
finding's acceptance criterion must require an INTEGRATED test that drives the
production object (the composition root `build_application`, or the opened
production dialog/widget), not an isolated widget/presenter unit test.

**Why:** Issue #50 (schema-builder-ux-overhaul) cycle 1 FAILed because new
collaborator seams were added with `None`-default parameters, fully unit-tested in
isolation, but never injected at the composition root. High unit coverage masked
the missing wiring — the dialog the user opened still rendered the pre-feature
plain-text editors. The defect class is "isolated coverage hides missing
production wiring."

**How to apply:** In any plan whose task wires an existing module into the live
app, the proving test must (a) instantiate the production object the user reaches
(e.g. `SchemaBuilderDialog`, or call `build_application`), (b) assert the seam is
reachable from that object, and (c) fail if the code falls back to the old path.
Pair the integrated test with a production grep showing a non-test call site.
Place the proving test in the same phase as the wiring (self-validating phase).
