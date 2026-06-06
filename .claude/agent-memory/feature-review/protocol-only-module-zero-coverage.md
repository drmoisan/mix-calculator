---
name: protocol-only-module-zero-coverage
description: typing.Protocol modules imported only under TYPE_CHECKING report 0% coverage; classify as non-blocking PARTIAL not FAIL when concrete implementers are well-covered
metadata:
  type: feedback
---

A new `typing.Protocol` contract module imported only inside `if TYPE_CHECKING:`
blocks (referenced structurally, not by inheritance) will report 0% line coverage:
its `...` method bodies are coverage-excluded by `pyproject.toml`
(`^\s*\.\.\.\s*$`), and the remaining signature/decorator/class lines never execute
at runtime because the module is never imported at runtime.

**Why:** On issue #50, `src/gui/_columns_tab_protocol.py` and `_key_tab_protocol.py`
showed 0% while their concrete implementers were 93–100% covered
(`_columns_tab_drag.py` 95%, `_columns_tab_presenter.py` 93%,
`_key_tab_presenter.py` 100%). Treating 0% as a FAIL on a non-executable contract
module would be a false positive — there is no untested behavior.

**How to apply:** Before flagging a 0%-coverage new file as a coverage FAIL, grep
for its import sites. If it is imported only under `TYPE_CHECKING` and is a pure
Protocol/ABC contract whose implementers are covered, record it as a non-blocking
PARTIAL with the remediation suggestion to add `# pragma: no cover` or a runtime
import. Contrast: protocol modules imported at runtime (e.g.
`_schema_view_protocols.py`) show 100% and need no exception.
