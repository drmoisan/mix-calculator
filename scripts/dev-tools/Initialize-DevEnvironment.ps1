#Requires -Version 7.0
<#
.SYNOPSIS
    Verifies and, on confirmation, installs the host prerequisites for the
    mix-calculator development environment, then provisions the in-project venv.

.DESCRIPTION
    Checks each prerequisite in order (Python 3.12-3.14, Poetry, MSVC C++ build tools,
    and the in-project Poetry environment). For any missing prerequisite the script asks
    for confirmation (via ShouldProcess) and installs it, requesting elevation only for
    the install that needs administrator rights (MSVC build tools). The script is
    idempotent and ends with a summary of every requirement's final state.

    Pure decision logic lives in the sibling module DevEnvironment.psm1. This file holds
    the external-process wrapper seams, detection, install actions, orchestration, and
    the entrypoint. Every external executable call is isolated behind a wrapper so tests
    mock the wrapper, never the real executable. Installs are winget-first, with
    documented fallbacks: Poetry uses its official installer, and the MSVC build tools
    modify an existing Visual Studio install via the VS Installer when one is present,
    else fall back to the winget BuildTools package.

.PARAMETER AutoApprove
    Approve every required install without an interactive prompt. Alias: -Force.

.PARAMETER DryRun
    Report what would be installed without changing state. Equivalent to -WhatIf.

.EXAMPLE
    pwsh ./scripts/dev-tools/Initialize-DevEnvironment.ps1 -AutoApprove
    Verifies and installs prerequisites without prompting.

.NOTES
    Compatible with PowerShell 7+. Tier T4 (dev tooling); coverage thresholds are
    uniform (line >= 85%, branch >= 75%).
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter()]
    [Alias('Force')]
    [switch] $AutoApprove,

    [Parameter()]
    [switch] $DryRun
)

Import-Module -Name (Join-Path $PSScriptRoot 'DevEnvironment.psm1') -Force

# --- External-process wrapper seams (mock the wrapper, never the real exe) --

function Invoke-WingetExe {
    # SYNOPSIS: Splat args into winget and return combined output.
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $WingetArgs)
    return (winget @WingetArgs 2>&1 | Out-String)
}

function Invoke-PyLauncherExe {
    # SYNOPSIS: Splat args into the py launcher and return combined output.
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $PyArgs)
    return (py @PyArgs 2>&1 | Out-String)
}

function Invoke-PythonExe {
    # SYNOPSIS: Splat args into python and return combined output.
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $PythonArgs)
    return (python @PythonArgs 2>&1 | Out-String)
}

function Invoke-PoetryExe {
    # SYNOPSIS: Splat args into poetry and return combined output.
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $PoetryArgs)
    return (poetry @PoetryArgs 2>&1 | Out-String)
}

function Invoke-VsWhereExe {
    # SYNOPSIS: Splat args into vswhere.exe at the given path and return output.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)] [string] $VsWherePath,
        [Parameter(Mandatory)] [string[]] $VsWhereArgs
    )
    return (& $VsWherePath @VsWhereArgs 2>&1 | Out-String)
}

function Invoke-PoetryInstaller {
    # SYNOPSIS: Run the official Poetry installer via the py launcher.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    return ((Invoke-RestMethod -Uri 'https://install.python-poetry.org') | py - 2>&1 | Out-String)
}

function Invoke-ElevatedProcess {
    # SYNOPSIS: Start a process with -Verb RunAs (UAC) and return its exit code.
    [CmdletBinding()]
    [OutputType([int])]
    param(
        [Parameter(Mandatory)] [string] $FilePath,
        [Parameter(Mandatory)] [string[]] $ArgumentList
    )
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -Verb RunAs -Wait -PassThru
    return $process.ExitCode
}

# --- Environment / host adapter seams --------------------------------------

function Test-IsElevated {
    # SYNOPSIS: Return $true when the current process is elevated (Administrator).
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    $principal = [Security.Principal.WindowsPrincipal]::new(
        [Security.Principal.WindowsIdentity]::GetCurrent())
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandAvailable {
    # SYNOPSIS: Return $true when a command of the given name is resolvable.
    [CmdletBinding()]
    [OutputType([bool])]
    param([Parameter(Mandatory)] [string] $Name)
    return [bool](Get-Command -Name $Name -ErrorAction SilentlyContinue)
}

function Test-WingetAvailable {
    # SYNOPSIS: Return $true when winget is resolvable.
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    return Test-CommandAvailable -Name 'winget'
}

function Get-EnvironmentVariableValue {
    # SYNOPSIS: Read a process-scoped environment variable.
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string] $Name)
    return [Environment]::GetEnvironmentVariable($Name, [EnvironmentVariableTarget]::Process)
}

function Set-EnvironmentVariableValue {
    # SYNOPSIS: Set or clear a process-scoped environment variable.
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter()] [AllowNull()] [string] $Value
    )
    if ($PSCmdlet.ShouldProcess($Name, 'Set process environment variable')) {
        [Environment]::SetEnvironmentVariable($Name, $Value, [EnvironmentVariableTarget]::Process)
    }
}

function Get-VsWhereLocation {
    # SYNOPSIS: Return the vswhere.exe path if present, else an empty string.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    $candidate = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    return ''
}

# --- Detection helpers (compose seams + pure logic) ------------------------

function Get-DetectedPythonVersion {
    # SYNOPSIS: Collect candidate Python versions via the py launcher and python.
    [CmdletBinding()]
    [OutputType([string[]])]
    param()

    $versions = @()

    if (Test-CommandAvailable -Name 'py') {
        $paths = (Invoke-PyLauncherExe -PyArgs @('-0p')) -split "`r?`n"
        foreach ($path in $paths) {
            $trimmed = $path.Trim()
            if (-not $trimmed) { continue }
            $bandMatch = [regex]::Match($trimmed, '(\d+\.\d+)')
            if ($bandMatch.Success) { $versions += $bandMatch.Groups[1].Value }
        }
    }

    if (Test-CommandAvailable -Name 'python') {
        $versions += (Invoke-PythonExe -PythonArgs @('--version'))
    }

    return $versions
}

function Test-PythonRequirementSatisfied {
    # SYNOPSIS: Return $true when any detected interpreter is in the 3.12-3.14 band.
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    return Select-PythonBandSatisfied -VersionText (Get-DetectedPythonVersion)
}

function Test-PoetryRequirementSatisfied {
    # SYNOPSIS: Return $true when `poetry --version` resolves and reports Poetry.
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    if (-not (Test-CommandAvailable -Name 'poetry')) { return $false }
    $output = Invoke-PoetryExe -PoetryArgs @('--version')
    return [bool]([regex]::Match($output, 'Poetry').Success)
}

function Test-MsvcRequirementSatisfied {
    # SYNOPSIS: Return @{Satisfied;VsInstallPath}. VsInstallPath is the latest VS install
    # path when any VS install exists (even without VC tools), so the caller can modify it.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param()

    $result = [pscustomobject]@{ Satisfied = $false; VsInstallPath = '' }

    $vsWhere = Get-VsWhereLocation
    if (-not $vsWhere) { return $result }

    $installPath = (Invoke-VsWhereExe -VsWherePath $vsWhere -VsWhereArgs @(
            '-products', '*', '-latest',
            '-property', 'installationPath')).Trim()
    if ($installPath) { $result.VsInstallPath = $installPath }

    $withTools = (Invoke-VsWhereExe -VsWherePath $vsWhere -VsWhereArgs @(
            '-products', '*', '-latest',
            '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
            '-property', 'installationPath')).Trim()
    if ($withTools) {
        $result.Satisfied = $true
        $result.VsInstallPath = $withTools
    }

    return $result
}

# --- Confirmation seam -----------------------------------------------------

function Approve-RequirementInstall {
    # SYNOPSIS: Decide whether an install is approved. -AutoApprove returns $true without
    # prompting; otherwise the caller's ShouldProcessResult (honoring -WhatIf/-Confirm) wins.
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)] [string] $Target,
        [Parameter(Mandatory)] [bool] $ShouldProcessResult,
        [Parameter(Mandatory)] [bool] $AutoApprove
    )

    [void]$Target
    if ($AutoApprove) { return $true }
    return $ShouldProcessResult
}

# --- Install actions (compose seams; elevation only where required) --------

function Install-PythonRequirement {
    # SYNOPSIS: Install Python 3.12 via winget, or fail clearly when winget is absent.
    [CmdletBinding()]
    [OutputType([void])]
    param()
    if (-not (Test-WingetAvailable)) {
        throw 'winget is not available; install Python 3.12 manually from python.org.'
    }
    [void](Invoke-WingetExe -WingetArgs @('install', '--id', 'Python.Python.3.12', '-e'))
}

function Install-PoetryRequirement {
    # SYNOPSIS: Install Poetry via the official installer (winget has no reliable pkg).
    [CmdletBinding()]
    [OutputType([void])]
    param()
    [void](Invoke-PoetryInstaller)
}

function Install-MsvcRequirement {
    # SYNOPSIS: Install MSVC C++ build tools (requires elevation). Modifies an existing VS
    # install via the VS Installer when present, else winget BuildTools. Invoke-ElevatedProcess
    # uses -Verb RunAs to trigger UAC for the scoped child; the script itself is not relaunched.
    [CmdletBinding()]
    [OutputType([void])]
    param(
        [Parameter()] [string] $VsInstallPath = '',
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    [void]$IsElevated

    if ($VsInstallPath) {
        $setup = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\setup.exe'
        $setupArgs = @(
            'modify', '--installPath', $VsInstallPath,
            '--add', 'Microsoft.VisualStudio.Workload.NativeDesktop',
            '--includeRecommended', '--quiet', '--norestart')
        [void](Invoke-ElevatedProcess -FilePath $setup -ArgumentList $setupArgs)
        return
    }

    if (-not (Test-WingetAvailable)) {
        throw 'winget is not available and no Visual Studio install was found; install the C++ build tools manually.'
    }

    $override = '--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --quiet --norestart'
    $wingetArgs = @(
        'install', '--id', 'Microsoft.VisualStudio.2022.BuildTools', '-e',
        '--override', $override)
    [void](Invoke-ElevatedProcess -FilePath 'winget' -ArgumentList $wingetArgs)
}

function Install-ProjectRequirement {
    # SYNOPSIS: Run `poetry install` with VIRTUAL_ENV cleared so the in-project .venv is used.
    # The shell sets VIRTUAL_ENV to the global Python, which would push Poetry into global
    # site-packages; clear it for the child invocation and restore it afterward.
    [CmdletBinding()]
    [OutputType([void])]
    param()

    $previous = Get-EnvironmentVariableValue -Name 'VIRTUAL_ENV'
    try {
        Set-EnvironmentVariableValue -Name 'VIRTUAL_ENV' -Value $null
        [void](Invoke-PoetryExe -PoetryArgs @('install'))
    }
    finally {
        Set-EnvironmentVariableValue -Name 'VIRTUAL_ENV' -Value $previous
    }
}

# --- Orchestration ---------------------------------------------------------

function Test-RequirementPresent {
    # SYNOPSIS: Detect whether a requirement is satisfied; return @{IsPresent;MsvcState}.
    # 'project' is always not-present because `poetry install` is idempotent and is the
    # final provisioning step.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param([Parameter(Mandatory)] [string] $Id)

    $state = [pscustomobject]@{ IsPresent = $false; MsvcState = $null }

    switch ($Id) {
        'python' { $state.IsPresent = Test-PythonRequirementSatisfied }
        'poetry' { $state.IsPresent = Test-PoetryRequirementSatisfied }
        'msvc' {
            $state.MsvcState = Test-MsvcRequirementSatisfied
            $state.IsPresent = [bool]$state.MsvcState.Satisfied
        }
        'project' { $state.IsPresent = $false }
        default { throw "Unknown requirement id: $Id" }
    }

    return $state
}

function Invoke-RequirementInstall {
    # SYNOPSIS: Dispatch the install action for a single requirement id. MsvcState is used
    # for the 'msvc' id; IsElevated is passed through to the MSVC install.
    [CmdletBinding()]
    [OutputType([void])]
    param(
        [Parameter(Mandatory)] [string] $Id,
        [Parameter()] [psobject] $MsvcState,
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    switch ($Id) {
        'python' { Install-PythonRequirement }
        'poetry' { Install-PoetryRequirement }
        'msvc' {
            $path = if ($MsvcState) { [string]$MsvcState.VsInstallPath } else { '' }
            Install-MsvcRequirement -VsInstallPath $path -IsElevated $IsElevated
        }
        'project' { Install-ProjectRequirement }
        default { throw "Unknown requirement id: $Id" }
    }
}

function Invoke-RequirementCheck {
    # SYNOPSIS: Detect, optionally install, and record the outcome of one requirement.
    # ShouldProcessCallback takes a target string and returns the ShouldProcess result.
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [Parameter(Mandatory)] [hashtable] $Definition,
        [Parameter(Mandatory)] [bool] $IsDryRun,
        [Parameter(Mandatory)] [bool] $AutoApprove,
        [Parameter(Mandatory)] [scriptblock] $ShouldProcessCallback,
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    $state = Test-RequirementPresent -Id $Definition.Id

    if ($state.IsPresent) {
        return Get-RequirementResult -Id $Definition.Id -Name $Definition.Name -State 'Satisfied'
    }

    $confirmed = Approve-RequirementInstall `
        -Target $Definition.Name `
        -ShouldProcessResult ([bool](& $ShouldProcessCallback $Definition.Name)) `
        -AutoApprove $AutoApprove

    $decision = Resolve-InstallDecision -IsPresent $false -IsDryRun $IsDryRun -IsConfirmed $confirmed

    $terminal = Resolve-RequirementOutcome -Decision $decision -Id $Definition.Id -Name $Definition.Name
    if ($terminal) {
        return $terminal
    }

    try {
        Invoke-RequirementInstall -Id $Definition.Id -MsvcState $state.MsvcState -IsElevated $IsElevated
        return Get-RequirementResult -Id $Definition.Id -Name $Definition.Name -State 'Installed'
    }
    catch {
        return Get-RequirementResult -Id $Definition.Id -Name $Definition.Name `
            -State 'Failed' -Detail $_.Exception.Message
    }
}

function Invoke-DevEnvironmentSetup {
    # SYNOPSIS: Run every requirement check in order and return the result records.
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary[]])]
    param(
        [Parameter(Mandatory)] [bool] $IsDryRun,
        [Parameter(Mandatory)] [bool] $AutoApprove,
        [Parameter(Mandatory)] [scriptblock] $ShouldProcessCallback,
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    $results = @()
    foreach ($definition in Get-DevRequirementDefinition) {
        $results += Invoke-RequirementCheck `
            -Definition $definition `
            -IsDryRun $IsDryRun `
            -AutoApprove $AutoApprove `
            -ShouldProcessCallback $ShouldProcessCallback `
            -IsElevated $IsElevated
    }

    return $results
}

function Invoke-DevEnvironmentMain {
    # SYNOPSIS: Run the full setup, print the summary, and return an exit code (0 ok,
    # 1 when any requirement Failed). Separated from the exit-calling guard block so it
    # is unit-testable without terminating the test host.
    [CmdletBinding()]
    [OutputType([int])]
    param(
        [Parameter(Mandatory)] [bool] $IsDryRun,
        [Parameter(Mandatory)] [bool] $AutoApprove,
        [Parameter(Mandatory)] [scriptblock] $ShouldProcessCallback,
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    $results = Invoke-DevEnvironmentSetup `
        -IsDryRun $IsDryRun `
        -AutoApprove $AutoApprove `
        -ShouldProcessCallback $ShouldProcessCallback `
        -IsElevated $IsElevated

    foreach ($line in (Get-DevEnvironmentSummary -Result $results)) {
        Write-Information -MessageData $line -InformationAction Continue
    }

    if ($results | Where-Object { $_.State -eq 'Failed' }) {
        return 1
    }
    return 0
}

# --- Entrypoint (guarded so the script can be dot-sourced for testing) -----

if ($MyInvocation.InvocationName -eq '.') {
    return
}

$dryRunEffective = [bool]($DryRun -or $WhatIfPreference)
$shouldProcessCallback = { param($target) $PSCmdlet.ShouldProcess($target, 'Install') }

$exitCode = Invoke-DevEnvironmentMain `
    -IsDryRun $dryRunEffective `
    -AutoApprove ([bool]$AutoApprove) `
    -ShouldProcessCallback $shouldProcessCallback `
    -IsElevated (Test-IsElevated)

exit $exitCode
