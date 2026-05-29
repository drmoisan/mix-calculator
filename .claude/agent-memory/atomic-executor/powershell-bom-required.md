---
name: powershell-bom-required
description: New .ps1 files in this repo must be saved with a UTF-8 BOM or PSScriptAnalyzer will fail the analyze stage with PSUseBOMForUnicodeEncodedFile.
metadata:
  type: feedback
---

When creating a new PowerShell file (e.g., `*.Tests.ps1`) in this repository, prepend a UTF-8 BOM (`0xEF 0xBB 0xBF`) at the time of creation. PoshQC analyze will otherwise raise `PSUseBOMForUnicodeEncodedFile` and the toolchain loop must restart from format.

**Why:** PSScriptAnalyzer is configured to enforce `PSUseBOMForUnicodeEncodedFile`. This bit cycle 0 of issue #25 (one loop restart) and again cycle 1 (one loop restart). The Write tool produces UTF-8 without BOM by default on Windows.

**How to apply:** After Write-ing a new .ps1 file, run a one-shot BOM-prepend command before invoking `mcp__drm-copilot__run_poshqc_analyze`:

```powershell
$bytes = [System.IO.File]::ReadAllBytes($path)
if (-not ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)) {
    [System.IO.File]::WriteAllBytes($path, [byte[]](0xEF,0xBB,0xBF) + $bytes)
}
```

This avoids a guaranteed format-loop restart on every new .ps1 file.
