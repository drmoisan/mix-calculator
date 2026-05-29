#Requires -Version 7.0
<#
.SYNOPSIS
    Pure decision logic for Initialize-DevEnvironment.ps1.
.DESCRIPTION
    Contains the I/O-free decision logic for the dev-environment bootstrap: the Python
    version-band check, the install-vs-skip decision, the ordered requirement
    definitions, and the result/summary builders. These functions are deterministic and
    unit-testable without mocks. The external-process wrapper seams, detection, install
    actions, and orchestration live in the sibling script Initialize-DevEnvironment.ps1.
.NOTES
    Compatible with PowerShell 7+. Tier T4 (dev tooling).
#>

$script:PythonMinVersion = [version]'3.12'
$script:PythonMaxExclusiveVersion = [version]'3.15'

function Test-PythonVersionInBand {
    <#
    .SYNOPSIS
        Tests whether a version string falls in the half-open band [3.12, 3.15).
    .DESCRIPTION
        Parses the first major.minor token from the supplied text (e.g. '3.13.12',
        'Python 3.13.12', or '3.12') and returns $true when it is >= 3.12 and < 3.15.
    .PARAMETER VersionText
        The version string to test.
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
        Tests whether any of the supplied version strings is in the supported band.
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
        Decides the action for one requirement.
    .DESCRIPTION
        Returns 'Skip' when present, 'WouldInstall' when missing under a dry run,
        'Install' when missing and confirmed, or 'Declined' when missing and not
        confirmed.
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
        Returns the ordered prerequisite definitions.
    .DESCRIPTION
        Each definition is a hashtable with Id, Name, and RequiresElevation. The array
        order is the order in which requirements are checked.
    .OUTPUTS
        System.Object[] of hashtable definitions.
    #>
    [CmdletBinding()]
    [OutputType([System.Object[]])]
    param()

    return @(
        @{ Id = 'python'; Name = 'Python 3.12-3.14'; RequiresElevation = $false },
        @{ Id = 'poetry'; Name = 'Poetry'; RequiresElevation = $false },
        @{ Id = 'msvc'; Name = 'MSVC C++ build tools'; RequiresElevation = $true },
        @{ Id = 'project'; Name = 'Project environment (poetry install)'; RequiresElevation = $false },
        # Velopack CLI (issue #31): installed via `dotnet tool install -g vpk`;
        # no elevation required because the install is per-user.
        @{ Id = 'vpk'; Name = 'Velopack CLI (vpk)'; RequiresElevation = $false }
    )
}

function Get-RequirementResult {
    <#
    .SYNOPSIS
        Builds a single requirement-result record.
    .PARAMETER Id
        Stable requirement identifier.
    .PARAMETER Name
        Human-readable requirement name.
    .PARAMETER State
        Final state of the requirement.
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

function Resolve-RequirementOutcome {
    <#
    .SYNOPSIS
        Maps an install decision to a terminal result record for non-Install actions.
    .DESCRIPTION
        Returns a result record for 'WouldInstall' and 'Declined'. Returns $null for the
        'Install' decision (the caller performs the install and records the Installed or
        Failed outcome). 'Skip' is handled by the caller before this is reached.
    .PARAMETER Decision
        The install decision from Resolve-InstallDecision.
    .PARAMETER Id
        Stable requirement identifier.
    .PARAMETER Name
        Human-readable requirement name.
    #>
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [Parameter(Mandatory)] [string] $Decision,
        [Parameter(Mandatory)] [string] $Id,
        [Parameter(Mandatory)] [string] $Name
    )

    switch ($Decision) {
        'WouldInstall' {
            return Get-RequirementResult -Id $Id -Name $Name -State 'WouldInstall' -Detail 'dry-run: no changes made'
        }
        'Declined' {
            return Get-RequirementResult -Id $Id -Name $Name -State 'Declined' -Detail 'install not confirmed'
        }
        default { return $null }
    }
}

function Get-DevEnvironmentSummary {
    <#
    .SYNOPSIS
        Formats requirement-result records into summary text lines.
    .PARAMETER Result
        One or more records produced by Get-RequirementResult.
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

Export-ModuleMember -Function `
    'Test-PythonVersionInBand', 'Select-PythonBandSatisfied', 'Resolve-InstallDecision', `
    'Get-DevRequirementDefinition', 'Get-RequirementResult', 'Resolve-RequirementOutcome', `
    'Get-DevEnvironmentSummary'
