#Requires -Version 7.0
<#
.SYNOPSIS
    Activate the in-project Poetry venv and set a repo-relative prompt.

.DESCRIPTION
    Must be dot-sourced so the prompt redefinition and venv activation persist in
    the caller's session:

        . .\scripts\dev-tools\activate.ps1

    The script resolves the repository root by walking ancestor directories
    upward from its own location to the first ancestor that contains a `.venv`
    directory. This is robust to the script's own directory depth and does not
    assume a fixed number of parent levels. It then dot-sources the venv's
    Activate.ps1 and installs a `global:prompt` that renders as
    `(<project-name>)<repo-relative-path>> ` - for example `(mix-calculator)> `
    at the repository root and `(mix-calculator)\.claude> ` inside `.claude`.

    Pure logic (repo-root resolution and prompt-string construction) is isolated
    into testable functions with injected filesystem/path seams so the behavior
    can be verified with deterministic Pester tests - no real venv, PATH
    dependence, live executables, or temp files. The activation side effects are
    kept thin and separate from the pure logic. Tests import the function
    definitions via AST extraction without executing the entrypoint, so production
    control flow does not depend on the test harness.

.OUTPUTS
    None. When dot-sourced, redefines `global:prompt` and activates the venv as a
    side effect. When invoked without dot-sourcing, writes corrective guidance and
    returns without activating.

.EXAMPLE
    . .\scripts\dev-tools\activate.ps1
    Activates the in-project venv and replaces the prompt for the session.

.NOTES
    Compatible with PowerShell 7+. Tier T4 (dev tooling); coverage thresholds are
    uniform (line >= 85%, branch >= 75%).
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Pure logic ------------------------------------------------------------

function Resolve-RepoRoot {
    <#
    .SYNOPSIS
        Resolve the repository root by walking ancestors upward to the first one
        that contains a `.venv` directory.

    .DESCRIPTION
        Starts at $StartDir and tests each ancestor (including $StartDir itself)
        for a child `.venv`, using the injected $PathExists probe. Returns the
        first qualifying directory's full path, or '' when no ancestor qualifies.
        Depth-robust: it does not assume a fixed number of parent levels.

    .PARAMETER StartDir
        The directory to begin the upward search from (typically $PSScriptRoot).

    .PARAMETER PathExists
        A probe ScriptBlock that takes a single path string and returns a boolean
        indicating whether that path exists. Defaults to a real Test-Path probe;
        tests inject a deterministic in-memory probe.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $StartDir,

        [Parameter()]
        [ValidateNotNull()]
        [scriptblock] $PathExists = { param([string] $Path) Test-Path -LiteralPath $Path }
    )

    $current = $StartDir
    while (-not [string]::IsNullOrEmpty($current)) {
        $candidate = Join-Path -Path $current -ChildPath '.venv'
        if (& $PathExists $candidate) {
            return $current
        }
        $parent = Split-Path -Parent $current
        if ($parent -eq $current) {
            break
        }
        $current = $parent
    }

    return ''
}

function Get-RepoRelativePrompt {
    <#
    .SYNOPSIS
        Build the repo-relative prompt string for an active venv.

    .DESCRIPTION
        Returns `(<leaf>)<rel>> ` where <leaf> is the venv root's leaf name.
        - At the venv root: rel is empty (e.g. `(mix-calculator)> `).
        - In a descendant: rel is the repo-relative path with a leading backslash
          (e.g. `(mix-calculator)\.claude> `).
        - Outside the venv tree: rel is ' <absolute-path>' (e.g.
          `(mix-calculator) D:\elsewhere> `).
        Path comparisons use OrdinalIgnoreCase so drive/path casing does not
        change the result.

    .PARAMETER CurrentPath
        The current filesystem location to render relative to the venv root.

    .PARAMETER VenvRoot
        The repository root that contains the active venv.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $CurrentPath,

        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $VenvRoot
    )

    $name = Split-Path -Path $VenvRoot -Leaf

    if ($CurrentPath.Equals($VenvRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        $rel = ''
    }
    elseif ($CurrentPath.StartsWith($VenvRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        $rel = $CurrentPath.Substring($VenvRoot.Length)
    }
    else {
        $rel = " $CurrentPath"
    }

    return "($name)$rel> "
}

function Get-DefaultPrompt {
    <#
    .SYNOPSIS
        Build the default `PS <path>> ` prompt used when no venv is active.

    .PARAMETER CurrentPath
        The current filesystem location to render.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $CurrentPath
    )

    return "PS $CurrentPath> "
}

function Get-VenvAwarePrompt {
    <#
    .SYNOPSIS
        Build the prompt string from the current path and the active venv value.

    .DESCRIPTION
        Pure decision used by the installed `global:prompt` shim. When $VenvEnv is
        empty (no active venv) it returns the default `PS <path>> ` form; otherwise
        it derives the repository root as the parent of the venv directory and
        delegates to Get-RepoRelativePrompt.

    .PARAMETER CurrentPath
        The current filesystem location.

    .PARAMETER VenvEnv
        The value of $env:VIRTUAL_ENV (the path to the active venv), or '' when no
        venv is active.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $CurrentPath,

        [Parameter()]
        [AllowEmptyString()]
        [AllowNull()]
        [string] $VenvEnv
    )

    if ([string]::IsNullOrEmpty($VenvEnv)) {
        return Get-DefaultPrompt -CurrentPath $CurrentPath
    }

    $venvRoot = Split-Path -Path $VenvEnv -Parent
    return Get-RepoRelativePrompt -CurrentPath $CurrentPath -VenvRoot $venvRoot
}

function Test-IsDotSourced {
    <#
    .SYNOPSIS
        Return $true when the script was dot-sourced.

    .DESCRIPTION
        PowerShell sets the invocation name to '.' when a script is dot-sourced.
        Extracted as a pure predicate so the entrypoint decision is unit-testable.

    .PARAMETER InvocationName
        The value of $MyInvocation.InvocationName for the invocation under test.
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string] $InvocationName
    )

    return $InvocationName -eq '.'
}

function Get-NotDotSourcedMessage {
    <#
    .SYNOPSIS
        Return the corrective guidance shown when the script is run without being
        dot-sourced.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param()

    return @'
activate.ps1 must be dot-sourced so the venv activation and prompt change persist in your session.

Run it like this (note the leading dot and space):
  . .\scripts\dev-tools\activate.ps1
'@
}

# --- Activation side effects (thin; skipped when dot-sourced for testing) ---

function Invoke-VenvActivateScript {
    <#
    .SYNOPSIS
        Dot-source the venv's Activate.ps1 into the current session.

    .DESCRIPTION
        Thin wrapper around the dot-source side effect so the orchestration in
        Invoke-VenvActivation can be unit-tested by mocking this function rather
        than executing a real Activate.ps1.

    .PARAMETER ActivatePath
        Full path to the venv's Activate.ps1.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $ActivatePath
    )

    . $ActivatePath
}

function Invoke-VenvActivation {
    <#
    .SYNOPSIS
        Resolve the repo root, activate the in-project venv, and install the
        repo-relative prompt.

    .DESCRIPTION
        Orchestrates the side-effecting activation: resolves the repository root
        from $ScriptRoot, fails fast with guidance when no `.venv` ancestor is
        found, sets VIRTUAL_ENV_DISABLE_PROMPT (the script owns the prompt),
        dot-sources the venv's Activate.ps1, and assigns the global prompt
        function. Separated from the pure logic so the pure functions remain
        unit-testable in isolation.

    .PARAMETER ScriptRoot
        The directory the activate script lives in (typically $PSScriptRoot).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $ScriptRoot
    )

    $repoRoot = Resolve-RepoRoot -StartDir $ScriptRoot
    if (-not $repoRoot) {
        throw "Could not locate a '.venv' directory in any ancestor of $ScriptRoot. Run 'poetry install' first."
    }

    $activate = Join-Path -Path $repoRoot -ChildPath '.venv\Scripts\Activate.ps1'
    if (-not (Test-Path -LiteralPath $activate)) {
        throw "venv missing at $activate. Run 'poetry install' first."
    }

    $env:VIRTUAL_ENV_DISABLE_PROMPT = '1'   # we own the prompt, not the venv
    Invoke-VenvActivateScript -ActivatePath $activate

    function global:prompt {
        Get-VenvAwarePrompt -CurrentPath (Get-Location).Path -VenvEnv $env:VIRTUAL_ENV
    }
}

# --- Entrypoint ------------------------------------------------------------

# This script must be dot-sourced so the prompt redefinition and venv activation
# persist in the caller's session. When run directly, the changes would apply
# only to a discarded child scope, so surface corrective guidance instead.
if (-not (Test-IsDotSourced -InvocationName $MyInvocation.InvocationName)) {
    Write-Error (Get-NotDotSourcedMessage)
    return
}

Invoke-VenvActivation -ScriptRoot $PSScriptRoot
