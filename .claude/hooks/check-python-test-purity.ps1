<#
.SYNOPSIS
    Pre-tool-use hook for Claude Code that blocks forbidden patterns in Python unit tests.

.DESCRIPTION
    This script is invoked by the Claude Code PreToolUse hook before any Write or Edit
    operation on a file path matching tests/**/*.py. It reads the tool input from the
    CLAUDE_TOOL_INPUT environment variable (JSON with 'file_path' and a content field:
    'content' for Write, 'new_string' for Edit) and rejects the operation when the
    proposed content introduces forbidden runtime dependencies.

    Forbidden patterns in unit tests include:
      - temporary filesystem usage (tempfile, NamedTemporaryFile, TemporaryDirectory,
        mkstemp, mkdtemp, Path.touch)
      - network access (requests, httpx, urllib.request, socket, http.client)
      - subprocess execution (subprocess, os.system, os.popen)
      - time-based flakiness (time.sleep)
      - real database drivers (psycopg2, pymysql, sqlite3.connect on real files)

    If the content contains any forbidden pattern, the script writes a JSON response
    to stdout with 'decision': 'block' and exits with code 0 to let Claude Code surface
    the reason.

.NOTES
    Compatible with PowerShell 7+.
    This script must not modify any state; it is a read-only validation gate.
    It only inspects tool inputs targeting tests/ paths; all other paths pass through.
#>
[CmdletBinding()]
param()

function Get-PythonTestPurityBlockDecision {
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [Parameter(Mandatory)]
        [string] $Reason
    )

    [ordered]@{
        decision = 'block'
        reason   = $Reason
    }
}

function Test-PythonTestFilePath {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath
    )

    $normalized = $FilePath -replace '\\', '/'
    return (($normalized -match '(^|/)tests/.*\.py$') -or ($normalized -match '(^|/)test_[^/]+\.py$'))
}

function Invoke-PythonTestPurityDecision {
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [string] $ToolInputRaw
    )

    if (-not $ToolInputRaw) {
        return [ordered]@{ decision = 'allow' }
    }

    try {
        $toolInput = $ToolInputRaw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        return Get-PythonTestPurityBlockDecision -Reason 'Python unit test purity hook received malformed JSON in CLAUDE_TOOL_INPUT.'
    }

    $filePath = $toolInput.file_path
    if (-not $filePath) {
        return [ordered]@{ decision = 'allow' }
    }

    if (-not (Test-PythonTestFilePath -FilePath $filePath)) {
        return [ordered]@{ decision = 'allow' }
    }

    $content = $null
    if ($null -ne $toolInput.content) {
        $content = [string]$toolInput.content
    } elseif ($null -ne $toolInput.new_string) {
        $content = [string]$toolInput.new_string
    }

    if (-not $content) {
        return [ordered]@{ decision = 'allow' }
    }

    $forbiddenPatterns = @(
        @{ Pattern = 'import\s+tempfile'; Reason = 'tempfile usage forbidden in unit tests' },
        @{ Pattern = 'from\s+tempfile\s+import'; Reason = 'tempfile usage forbidden in unit tests' },
        @{ Pattern = 'NamedTemporaryFile'; Reason = 'temporary files forbidden in unit tests' },
        @{ Pattern = 'TemporaryDirectory'; Reason = 'temporary directories forbidden in unit tests' },
        @{ Pattern = '\bmkstemp\s*\('; Reason = 'temporary files forbidden in unit tests' },
        @{ Pattern = '\bmkdtemp\s*\('; Reason = 'temporary directories forbidden in unit tests' },
        @{ Pattern = '\.touch\s*\('; Reason = 'Path.touch forbidden in unit tests' },
        @{ Pattern = 'import\s+requests\b'; Reason = 'network access forbidden in unit tests' },
        @{ Pattern = 'from\s+requests\b'; Reason = 'network access forbidden in unit tests' },
        @{ Pattern = 'import\s+httpx\b'; Reason = 'network access forbidden in unit tests' },
        @{ Pattern = 'from\s+httpx\b'; Reason = 'network access forbidden in unit tests' },
        @{ Pattern = 'urllib\.request'; Reason = 'network access forbidden in unit tests' },
        @{ Pattern = 'import\s+socket\b'; Reason = 'raw socket access forbidden in unit tests' },
        @{ Pattern = 'from\s+http\.client'; Reason = 'network access forbidden in unit tests' },
        @{ Pattern = 'import\s+subprocess\b'; Reason = 'subprocess execution forbidden in unit tests' },
        @{ Pattern = 'from\s+subprocess\s+import'; Reason = 'subprocess execution forbidden in unit tests' },
        @{ Pattern = 'os\.system\s*\('; Reason = 'os.system forbidden in unit tests' },
        @{ Pattern = 'os\.popen\s*\('; Reason = 'os.popen forbidden in unit tests' },
        @{ Pattern = 'time\.sleep\s*\('; Reason = 'time.sleep forbidden in unit tests; avoid timing hacks' },
        @{ Pattern = 'import\s+psycopg2\b'; Reason = 'real database drivers forbidden in unit tests' },
        @{ Pattern = 'import\s+pymysql\b'; Reason = 'real database drivers forbidden in unit tests' },
        @{ Pattern = 'sqlite3\.connect\s*\('; Reason = 'sqlite3.connect on real files forbidden in unit tests' }
    )

    $violations = @()
    foreach ($entry in $forbiddenPatterns) {
        if ($content -match $entry.Pattern) {
            $violations += $entry.Reason
        }
    }

    if ($violations.Count -eq 0) {
        return [ordered]@{ decision = 'allow' }
    }

    $uniqueViolations = $violations | Select-Object -Unique
    $reason = "Python unit test purity violations in '$filePath': " + ($uniqueViolations -join '; ') + ". Replace with pure code paths, dependency-injection seams, or in-memory fakes per .claude/rules/python.md."

    return Get-PythonTestPurityBlockDecision -Reason $reason
}

if ($MyInvocation.InvocationName -eq '.') {
    return
}

$decision = Invoke-PythonTestPurityDecision -ToolInputRaw $env:CLAUDE_TOOL_INPUT
if ($decision.decision -eq 'block') {
    $decision | ConvertTo-Json -Compress | Write-Output
}

exit 0
