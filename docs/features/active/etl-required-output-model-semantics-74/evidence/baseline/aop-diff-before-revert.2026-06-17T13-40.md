# Baseline — AOP Schema Diff Before Revert (CF1 cycle 3, #74)

Timestamp: 2026-06-17T13-40
Command: git diff main -- src/schemas/default_aop.schema.json
EXIT_CODE: 0

Output Summary: Non-empty diff present at head. The only CF1 change to the AOP schema file is
the version bump `"version": "2.0"` -> `"version": "3.0"` (1 line changed). This is the change
R1 will revert via `git checkout main -- src/schemas/default_aop.schema.json`.

```
diff --git a/src/schemas/default_aop.schema.json b/src/schemas/default_aop.schema.json
index 4e5a61a..471800f 100644
--- a/src/schemas/default_aop.schema.json
+++ b/src/schemas/default_aop.schema.json
@@ -1,6 +1,6 @@
 {
   "name": "default_aop",
-  "version": "2.0",
+  "version": "3.0",
   "description": "...",
```
