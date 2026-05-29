"""Behavioral integration tests for the mix-pipeline GUI (v2 issue #19).

This package contains button-driven behavioral integration tests that exercise
the fully-wired ``build_application`` end-to-end with a deterministic
``SynchronousRunner`` and fake services. The tests assert behavior via direct
model inspection — no polling primitives (no ``qtbot.waitUntil``, no
``QTest.qWait``, no ``time.sleep``).
"""
