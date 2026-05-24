#Requires -Version 7.0
<#
.SYNOPSIS
    Verifies and, on confirmation, installs the host prerequisites for the
    mix-calculator development environment, then provisions the in-project venv.

.DESCRIPTION
    Checks each prerequisite in order (Python 3.12-3.14, Poetry, MSVC C++ build
    tools, and the in-project Poetry environment). For any missing prerequisite the
    script asks for confirmation (via ShouldProcess) and installs it, requesting
    elevation only for the install that needs administrator rights (MSVC build
    tools). The script is idempotent: prerequisites already satisfied are reported
    as skipped. A summary of every requirement's final state is emitted at the end.

    Pure decision logic (version-band checks, requirement definitions, install
    decisions, summary building) is separated from the external-process seams
    (winget, the py launcher, Poetry, vswhere, the VS Installer, the elevation
    relaunch). Every external executable call goes through a wrapper function so
    tests mock the wrapper, never the real executable.

.PARAMETER AutoApprove
    Approve every required install without an interactive confirmation prompt.
    Intended for non-interactive runs. Alias: -Force.

.PARAMETER DryRun
    Report what would be installed without changing any state. Equivalent in effect
    to -WhatIf; provided as an explicit switch for readability.

.EXAMPLE
    pwsh ./scripts/dev-tools/Initialize-DevEnvironment.ps1
    Interactively verifies and installs prerequisites, prompting before each install.

.EXAMPLE
    pwsh ./scripts/dev-tools/Initialize-DevEnvironment.ps1 -AutoApprove
    Verifies and installs prerequisites without prompting.

.EXAMPLE
    pwsh ./scripts/dev-tools/Initialize-DevEnvironment.ps1 -DryRun
    Reports the actions that would be taken without changing state.

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

Set-Variable -Name PythonMinVersion -Value ([version]'3.12') -Option Constant -Scope Script -Force
Set-Variable -Name PythonMaxExclusiveVersion -Value ([version]'3.15') -Option Constant -Scope Script -Force

# ---------------------------------------------------------------------------
# Pure decision logic (no I/O; fully unit-testable)
# ---------------------------------------------------------------------------

function Test-PythonVersionInBand {
    <#
    .SYNOPSIS
        Returns $true when a Python version string falls in [3.12, 3.15).
    .PARAMETER VersionText
        A version string such as '3.13.12', 'Python 3.13.12', or '3.12'.
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string] $VersionText
    )

    $match = [regex]::Match($VersionText, '(?<major>\d+)\.(?<minor>\d+)(?:\.(?<patch>\d+))?')
    if (-not $match.Success) {
        return $false
    }

    $parsed = [version]::new(
        [int]$match.Groups['major'].Value,
        [int]$match.Groups['minor'].Value)

    return ($parsed -ge $script:PythonMinVersion) -and ($parsed -lt $script:PythonMaxExclusiveVersion)
}

function Select-PythonBandSatisfied {
    <#
    .SYNOPSIS
        Returns $true when any of the supplied version strings is in band.
    .PARAMETER VersionText
        Zero or more candidate version strings from detected interpreters.
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter()]
        [AllowEmptyCollection()]
        [string[]] $VersionText = @()
    )

    foreach ($candidate in $VersionText) {
        if (Test-PythonVersionInBand -VersionText $candidate) {
            return $true
        }
    }

    return $false
}

function Resolve-InstallDecision {
    <#
    .SYNOPSIS
        Decides the action for a single requirement given its detected state.
    .DESCRIPTION
        Returns one of: 'Skip' (already satisfied), 'WouldInstall' (missing, but a
        dry-run/WhatIf path is active), 'Install' (missing and approved to proceed),
        or 'Declined' (missing and the user did not confirm).
    .PARAMETER IsPresent
        Whether the requirement is already satisfied.
    .PARAMETER IsDryRun
        Whether a non-mutating dry-run/WhatIf path is active.
    .PARAMETER IsConfirmed
        Whether installation was confirmed (by ShouldProcess or -AutoApprove).
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)] [bool] $IsPresent,
        [Parameter(Mandatory)] [bool] $IsDryRun,
        [Parameter(Mandatory)] [bool] $IsConfirmed
    )

    if ($IsPresent) { return 'Skip' }
    if ($IsDryRun) { return 'WouldInstall' }
    if ($IsConfirmed) { return 'Install' }
    return 'Declined'
}

function Get-DevRequirementDefinition {
    <#
    .SYNOPSIS
        Returns the ordered prerequisite definitions for this repository.
    .DESCRIPTION
        Each definition is a hashtable with: Id, Name, RequiresElevation. The order
        of the returned array is the order in which requirements are checked.
    #>
    [CmdletBinding()]
    [OutputType([System.Collections.Hashtable[]])]
    param()

    return @(
        @{ Id = 'python'; Name = 'Python 3.12-3.14'; RequiresElevation = $false },
        @{ Id = 'poetry'; Name = 'Poetry'; RequiresElevation = $false },
        @{ Id = 'msvc'; Name = 'MSVC C++ build tools'; RequiresElevation = $true },
        @{ Id = 'project'; Name = 'Project environment (poetry install)'; RequiresElevation = $false }
    )
}

function New-RequirementResult {
    <#
    .SYNOPSIS
        Builds a single requirement-result record for the summary.
    .PARAMETER Id
        Stable requirement identifier.
    .PARAMETER Name
        Human-readable requirement name.
    .PARAMETER State
        Final state: 'Satisfied', 'Installed', 'WouldInstall', 'Declined', or 'Failed'.
    .PARAMETER Detail
        Optional supporting detail (detected version, error text, etc.).
    #>
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [Parameter(Mandatory)] [string] $Id,
        [Parameter(Mandatory)] [string] $Name,
        [Parameter(Mandatory)]
        [ValidateSet('Satisfied', 'Installed', 'WouldInstall', 'Declined', 'Failed')]
        [string] $State,
        [Parameter()] [string] $Detail = ''
    )

    return [ordered]@{
        Id     = $Id
        Name   = $Name
        State  = $State
        Detail = $Detail
    }
}

function Get-DevEnvironmentSummary {
    <#
    .SYNOPSIS
        Formats requirement-result records into summary text lines.
    .PARAMETER Result
        One or more records produced by New-RequirementResult.
    #>
    [CmdletBinding()]
    [OutputType([string[]])]
    param(
        [Parameter()]
        [AllowEmptyCollection()]
        [System.Collections.Specialized.OrderedDictionary[]] $Result = @()
    )

    $lines = @('Development environment summary:')
    foreach ($record in $Result) {
        $line = "  [{0}] {1} - {2}" -f $record.State, $record.Name, $record.Id
        if ($record.Detail) {
            $line += " ({0})" -f $record.Detail
        }
        $lines += $line
    }

    return $lines
}

# ---------------------------------------------------------------------------
# External-process wrapper seams (mocked in tests; never call real exes in tests)
# ---------------------------------------------------------------------------

function Invoke-WingetExe {
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $WingetArgs)
    return (winget @WingetArgs 2>&1 | Out-String)
}

function Invoke-PyLauncherExe {
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $PyArgs)
    return (py @PyArgs 2>&1 | Out-String)
}

function Invoke-PythonExe {
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $PythonArgs)
    return (python @PythonArgs 2>&1 | Out-String)
}

function Invoke-PoetryExe {
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string[]] $PoetryArgs)
    return (poetry @PoetryArgs 2>&1 | Out-String)
}

function Invoke-VsWhereExe {
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)] [string] $VsWherePath,
        [Parameter(Mandatory)] [string[]] $VsWhereArgs
    )
    return (& $VsWherePath @VsWhereArgs 2>&1 | Out-String)
}

function Invoke-PoetryInstaller {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    return ((Invoke-RestMethod -Uri 'https://install.python-poetry.org') | py - 2>&1 | Out-String)
}

function Invoke-ElevatedProcess {
    [CmdletBinding()]
    [OutputType([int])]
    param(
        [Parameter(Mandatory)] [string] $FilePath,
        [Parameter(Mandatory)] [string[]] $ArgumentList
    )
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -Verb RunAs -Wait -PassThru
    return $process.ExitCode
}

# ---------------------------------------------------------------------------
# Environment / host adapter seams
# ---------------------------------------------------------------------------

function Test-IsElevated {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    $principal = [Security.Principal.WindowsPrincipal]::new(
        [Security.Principal.WindowsIdentity]::GetCurrent())
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandAvailable {
    [CmdletBinding()]
    [OutputType([bool])]
    param([Parameter(Mandatory)] [string] $Name)
    return [bool](Get-Command -Name $Name -ErrorAction SilentlyContinue)
}

function Get-EnvironmentVariableValue {
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)] [string] $Name)
    return [Environment]::GetEnvironmentVariable($Name, [EnvironmentVariableTarget]::Process)
}

function Set-EnvironmentVariableValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter()] [AllowNull()] [string] $Value
    )
    [Environment]::SetEnvironmentVariable($Name, $Value, [EnvironmentVariableTarget]::Process)
}

function Get-VsWhereLocation {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    $candidate = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    return ''
}

# ---------------------------------------------------------------------------
# Detection helpers (compose seams + pure logic)
# ---------------------------------------------------------------------------

function Get-DetectedPythonVersion {
    <#
    .SYNOPSIS
        Collects candidate Python version strings via the py launcher and python.
    #>
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
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    return Select-PythonBandSatisfied -VersionText (Get-DetectedPythonVersion)
}

function Test-PoetryRequirementSatisfied {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    if (-not (Test-CommandAvailable -Name 'poetry')) { return $false }
    $output = Invoke-PoetryExe -PoetryArgs @('--version')
    return [bool]([regex]::Match($output, 'Poetry').Success)
}

function Test-MsvcRequirementSatisfied {
    <#
    .SYNOPSIS
        Returns the detected MSVC install path when the VC tools workload is present,
        or an empty string when not present. Also reports whether a VS install exists.
    #>
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param()

    $result = [ordered]@{ Satisfied = $false; VsInstallPath = '' }

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

# ---------------------------------------------------------------------------
# Confirmation seam
# ---------------------------------------------------------------------------

function Approve-RequirementInstall {
    <#
    .SYNOPSIS
        Decides whether an install is approved, honoring -AutoApprove and ShouldProcess.
    .DESCRIPTION
        When -AutoApprove is set, returns $true without prompting. Otherwise defers to
        the caller's $PSCmdlet.ShouldProcess result, which honors -WhatIf and -Confirm.
    .PARAMETER Target
        The description of the item being installed (for the ShouldProcess prompt).
    .PARAMETER ShouldProcessResult
        The boolean result of $PSCmdlet.ShouldProcess(...) evaluated by the caller.
    .PARAMETER AutoApprove
        Whether non-interactive approval is in effect.
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)] [string] $Target,
        [Parameter(Mandatory)] [bool] $ShouldProcessResult,
        [Parameter(Mandatory)] [bool] $AutoApprove
    )

    if ($AutoApprove) { return $true }
    return $ShouldProcessResult
}

# ---------------------------------------------------------------------------
# Install actions (compose seams; elevation only where required)
# ---------------------------------------------------------------------------

function Install-PythonRequirement {
    [CmdletBinding()]
    [OutputType([void])]
    param()
    if (-not (Test-WingetAvailable)) {
        throw 'winget is not available; install Python 3.12 manually from python.org.'
    }
    [void](Invoke-WingetExe -WingetArgs @('install', '--id', 'Python.Python.3.12', '-e'))
}

function Install-PoetryRequirement {
    [CmdletBinding()]
    [OutputType([void])]
    param()
    # Poetry is not reliably on winget; use the official installer.
    [void](Invoke-PoetryInstaller)
}

function Install-MsvcRequirement {
    <#
    .SYNOPSIS
        Installs the MSVC C++ build tools, modifying an existing VS install when present.
    .PARAMETER VsInstallPath
        The installation path of an existing Visual Studio install, or empty.
    .PARAMETER IsElevated
        Whether the current process is already elevated.
    #>
    [CmdletBinding()]
    [OutputType([void])]
    param(
        [Parameter()] [string] $VsInstallPath = '',
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    # Elevation: Invoke-ElevatedProcess uses -Verb RunAs, which triggers the UAC
    # prompt when the current process is not already elevated. The scoped elevated
    # child process is sufficient; the whole script is not relaunched. $IsElevated
    # is retained for caller diagnostics and future no-prompt paths.
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
    <#
    .SYNOPSIS
        Runs `poetry install` with VIRTUAL_ENV cleared so the in-project .venv is used.
    .DESCRIPTION
        This machine's shell sets VIRTUAL_ENV to the global Python install, which makes
        Poetry install into global site-packages. The variable is cleared for the child
        invocation and restored afterward.
    #>
    [CmdletBinding()]
    [OutputType([void])]
    param()

    $previous = Get-EnvironmentVariableValue -Name 'VIRTUAL_ENV'
    try {
        Set-EnvironmentVariableValue -Name 'VIRTUAL_ENV' -Value $null
        [void](Invoke-PoetryExe -PoetryArgs @('install'))
    } finally {
        Set-EnvironmentVariableValue -Name 'VIRTUAL_ENV' -Value $previous
    }
}

function Test-WingetAvailable {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    return Test-CommandAvailable -Name 'winget'
}

# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

function Invoke-RequirementCheck {
    <#
    .SYNOPSIS
        Detects, optionally installs, and records the outcome of one requirement.
    .PARAMETER Definition
        A requirement definition from Get-DevRequirementDefinition.
    .PARAMETER IsDryRun
        Whether a non-mutating dry-run/WhatIf path is active.
    .PARAMETER AutoApprove
        Whether non-interactive approval is in effect.
    .PARAMETER ShouldProcessCallback
        A ScriptBlock taking a target string and returning the ShouldProcess result.
    .PARAMETER IsElevated
        Whether the current process is already elevated.
    #>
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [Parameter(Mandatory)] [hashtable] $Definition,
        [Parameter(Mandatory)] [bool] $IsDryRun,
        [Parameter(Mandatory)] [bool] $AutoApprove,
        [Parameter(Mandatory)] [scriptblock] $ShouldProcessCallback,
        [Parameter(Mandatory)] [bool] $IsElevated
    )

    $msvcState = $null
    switch ($Definition.Id) {
        'python' { $isPresent = Test-PythonRequirementSatisfied }
        'poetry' { $isPresent = Test-PoetryRequirementSatisfied }
        'msvc' {
            $msvcState = Test-MsvcRequirementSatisfied
            $isPresent = [bool]$msvcState.Satisfied
        }
        'project' {
            # The project environment is always (re)provisioned when host tools pass;
            # `poetry install` is idempotent, so treat it as not-yet-satisfied to run it.
            $isPresent = $false
        }
        default { throw "Unknown requirement id: $($Definition.Id)" }
    }

    if ($isPresent) {
        return New-RequirementResult -Id $Definition.Id -Name $Definition.Name -State 'Satisfied'
    }

    $confirmed = Approve-RequirementInstall `
        -Target $Definition.Name `
        -ShouldProcessResult ([bool](& $ShouldProcessCallback $Definition.Name)) `
        -AutoApprove $AutoApprove

    $decision = Resolve-InstallDecision -IsPresent $false -IsDryRun $IsDryRun -IsConfirmed $confirmed

    switch ($decision) {
        'WouldInstall' {
            return New-RequirementResult -Id $Definition.Id -Name $Definition.Name `
                -State 'WouldInstall' -Detail 'dry-run: no changes made'
        }
        'Declined' {
            return New-RequirementResult -Id $Definition.Id -Name $Definition.Name `
                -State 'Declined' -Detail 'install not confirmed'
        }
        'Install' {
            try {
                switch ($Definition.Id) {
                    'python' { Install-PythonRequirement }
                    'poetry' { Install-PoetryRequirement }
                    'msvc' { Install-MsvcRequirement -VsInstallPath $msvcState.VsInstallPath -IsElevated $IsElevated }
                    'project' { Install-ProjectRequirement }
                }
                return New-RequirementResult -Id $Definition.Id -Name $Definition.Name -State 'Installed'
            } catch {
                return New-RequirementResult -Id $Definition.Id -Name $Definition.Name `
                    -State 'Failed' -Detail $_.Exception.Message
            }
        }
    }
}

function Invoke-DevEnvironmentSetup {
    <#
    .SYNOPSIS
        Runs every requirement check in order and returns the result records.
    #>
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

# ---------------------------------------------------------------------------
# Entrypoint (guarded so the script can be dot-sourced for testing)
# ---------------------------------------------------------------------------

if ($MyInvocation.InvocationName -eq '.') {
    return
}

$dryRunEffective = [bool]($DryRun -or $WhatIfPreference)
$shouldProcessCallback = { param($target) $PSCmdlet.ShouldProcess($target, 'Install') }

$results = Invoke-DevEnvironmentSetup `
    -IsDryRun $dryRunEffective `
    -AutoApprove ([bool]$AutoApprove) `
    -ShouldProcessCallback $shouldProcessCallback `
    -IsElevated (Test-IsElevated)

foreach ($line in (Get-DevEnvironmentSummary -Result $results)) {
    Write-Host $line
}

if ($results | Where-Object { $_.State -eq 'Failed' }) {
    exit 1
}

exit 0
