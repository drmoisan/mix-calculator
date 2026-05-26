#Requires -Version 7.0
<#
.SYNOPSIS
    Lint all GitHub Actions workflows with actionlint.

.DESCRIPTION
    Local equivalent of the `actionlint` CI gate (.github/workflows/_actionlint.yml).
    Resolves the actionlint executable from PATH and runs it against the workflow
    files under .github/workflows so workflow YAML can be validated before pushing.

    This script does not install actionlint. If the executable is not on PATH it
    fails fast with installation guidance, keeping the dependency explicit rather
    than silently downloading an unpinned binary.

    External-process and host interactions are isolated behind wrapper/adapter
    seams (Invoke-ActionlintExe, Get-ActionlintSource, Get-WorkflowFile) so tests
    mock the seam, never the real executable. The entrypoint is guarded so the
    file can be dot-sourced for testing without executing.

.PARAMETER WorkflowPath
    Directory containing the workflow files to lint. Defaults to the repository's
    .github/workflows directory resolved relative to this script.

.OUTPUTS
    None. Writes actionlint findings to the host. Exits non-zero when actionlint
    reports problems or is not available.

.EXAMPLE
    pwsh scripts/dev-tools/run-actionlint.ps1
    Lints every workflow in .github/workflows.

.NOTES
    Compatible with PowerShell 7+. Tier T4 (dev tooling); coverage thresholds are
    uniform (line >= 85%, branch >= 75%).
#>
[CmdletBinding()]
param(
    [Parameter()]
    [string] $WorkflowPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- External-process wrapper seam (mock the wrapper, never the real exe) ----

function Invoke-ActionlintExe {
    # SYNOPSIS: Splat args into the actionlint executable and return its exit code.
    [CmdletBinding()]
    [OutputType([int])]
    param(
        [Parameter(Mandatory)] [string] $ActionlintPath,
        [Parameter(Mandatory)] [string[]] $ActionlintArgs
    )
    & $ActionlintPath @ActionlintArgs
    return $LASTEXITCODE
}

# --- Host / filesystem adapter seams ---------------------------------------

function Get-ActionlintSource {
    # SYNOPSIS: Return the resolved actionlint executable path, or '' when not on PATH.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    $command = Get-Command -Name 'actionlint' -CommandType Application -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return ''
}

function Get-WorkflowFile {
    # SYNOPSIS: Return full paths of *.yml/*.yaml files directly under the given directory.
    [CmdletBinding()]
    [OutputType([string[]])]
    param([Parameter(Mandatory)] [string] $Path)
    return Get-ChildItem -LiteralPath $Path -File |
        Where-Object { $_.Extension -in '.yml', '.yaml' } |
            Select-Object -ExpandProperty FullName
}

# --- Pure logic ------------------------------------------------------------

function Resolve-WorkflowPath {
    # SYNOPSIS: Resolve the workflows directory. Returns the requested path when set,
    # otherwise derives <repo>/.github/workflows from the script root (scripts/dev-tools).
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter()] [AllowEmptyString()] [string] $RequestedPath,
        [Parameter(Mandatory)] [string] $ScriptRoot
    )
    if ($RequestedPath) { return $RequestedPath }
    $repoRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)
    return Join-Path -Path $repoRoot -ChildPath '.github/workflows'
}

function Get-ActionlintMissingMessage {
    # SYNOPSIS: Return the guidance shown when actionlint is not installed.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    return @'
actionlint was not found on PATH.

Install it (see https://github.com/rhysd/actionlint), for example:
  winget install rhysd.actionlint
  go install github.com/rhysd/actionlint/cmd/actionlint@latest

Then re-run: pwsh scripts/dev-tools/run-actionlint.ps1
'@
}

# --- Orchestration / entrypoint logic --------------------------------------

function Invoke-WorkflowLintMain {
    # SYNOPSIS: Resolve actionlint and the workflow files, run the linter, and return an
    # exit code (0 when clean or no files found). Throws when the directory is missing,
    # actionlint is unavailable, or actionlint reports problems. Separated from the
    # exit-calling guard so it is unit-testable without terminating the test host.
    [CmdletBinding()]
    [OutputType([int])]
    param(
        [Parameter()] [AllowEmptyString()] [string] $WorkflowPath,
        [Parameter(Mandatory)] [string] $ScriptRoot
    )

    $resolvedPath = Resolve-WorkflowPath -RequestedPath $WorkflowPath -ScriptRoot $ScriptRoot
    if (-not (Test-Path -LiteralPath $resolvedPath)) {
        throw "Workflow directory not found: $resolvedPath"
    }

    # actionlint must be installed separately; fail with guidance rather than
    # attempting an unpinned download.
    $actionlintSource = Get-ActionlintSource
    if (-not $actionlintSource) {
        throw (Get-ActionlintMissingMessage)
    }

    Write-Information "Running actionlint on $resolvedPath" -InformationAction Continue

    # actionlint rejects a directory argument on Windows ("Incorrect function"), so
    # enumerate the workflow files and pass their paths explicitly. This is stable
    # across platforms regardless of the current working directory.
    $workflowFiles = Get-WorkflowFile -Path $resolvedPath
    if (-not $workflowFiles) {
        Write-Warning "No workflow files found in $resolvedPath"
        return 0
    }

    $actionlintExit = Invoke-ActionlintExe -ActionlintPath $actionlintSource `
        -ActionlintArgs (@('-color') + $workflowFiles)
    if ($actionlintExit -ne 0) {
        throw "actionlint reported problems (exit code $actionlintExit)."
    }

    Write-Information 'actionlint: no problems found.' -InformationAction Continue
    return 0
}

# --- Entrypoint (guarded so the script can be dot-sourced for testing) -----

if ($MyInvocation.InvocationName -eq '.') {
    return
}

exit (Invoke-WorkflowLintMain -WorkflowPath $WorkflowPath -ScriptRoot $PSScriptRoot)

