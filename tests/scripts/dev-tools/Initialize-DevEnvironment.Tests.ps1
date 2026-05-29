#Requires -Version 7.0
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }

<#
.SYNOPSIS
    Pester v5 tests for Initialize-DevEnvironment.ps1 + DevEnvironment.psm1. Pure
    decision logic exercises real code paths; detection / install / orchestration
    use mocked wrappers so no real winget, py, python, Poetry, vswhere, dotnet,
    VS Installer, elevation, PATH, or filesystem is touched.
#>

BeforeAll {
    $script:ScriptPath = Join-Path $PSScriptRoot '..\..\..\scripts\dev-tools\Initialize-DevEnvironment.ps1'
    $script:ScriptPath = (Resolve-Path -LiteralPath $script:ScriptPath).Path

    # Dot-source the script. Its entrypoint guard returns early under dot-source, and
    # the script imports DevEnvironment.psm1, so module functions are also available.
    . $script:ScriptPath

    # A ShouldProcess callback that always approves, for orchestration tests that do not
    # exercise the decline path.
    $script:ApproveAll = { param($target) [void]$target; $true }
    $script:DeclineAll = { param($target) [void]$target; $false }
}

Describe 'Test-PythonVersionInBand (pure logic)' {
    It 'accepts in-band <Version>' -ForEach @(
        @{ Version = '3.12' }
        @{ Version = '3.12.0' }
        @{ Version = '3.13.12' }
        @{ Version = '3.14.99' }
        @{ Version = 'Python 3.13.12' }
    ) {
        Test-PythonVersionInBand -VersionText $Version | Should -BeTrue
    }
    It 'rejects out-of-band <Version>' -ForEach @(
        @{ Version = '3.11.9' }
        @{ Version = '3.15.0' }
        @{ Version = '3.15' }
        @{ Version = '4.0.0' }
        @{ Version = '2.7.18' }
    ) {
        Test-PythonVersionInBand -VersionText $Version | Should -BeFalse
    }
    It 'returns false for an empty string' {
        Test-PythonVersionInBand -VersionText '' | Should -BeFalse
    }
    It 'returns false when no version token is present' {
        Test-PythonVersionInBand -VersionText 'no version here' | Should -BeFalse
    }
}

Describe 'Select-PythonBandSatisfied (pure logic)' {
    It 'returns true when any candidate is in band' {
        Select-PythonBandSatisfied -VersionText @('3.11.0', '3.13.12', '2.7') | Should -BeTrue
    }
    It 'returns false when no candidate is in band' {
        Select-PythonBandSatisfied -VersionText @('3.11.0', '3.15.0') | Should -BeFalse
    }
    It 'returns false for an empty collection' {
        Select-PythonBandSatisfied -VersionText @() | Should -BeFalse
    }
}

Describe 'Resolve-InstallDecision (pure logic)' {
    It 'returns <Expected> for (present=<IsPresent>, dryrun=<IsDryRun>, confirmed=<IsConfirmed>)' -ForEach @(
        @{ IsPresent = $true; IsDryRun = $false; IsConfirmed = $true; Expected = 'Skip' }
        @{ IsPresent = $false; IsDryRun = $true; IsConfirmed = $true; Expected = 'WouldInstall' }
        @{ IsPresent = $false; IsDryRun = $false; IsConfirmed = $true; Expected = 'Install' }
        @{ IsPresent = $false; IsDryRun = $false; IsConfirmed = $false; Expected = 'Declined' }
        @{ IsPresent = $true; IsDryRun = $true; IsConfirmed = $false; Expected = 'Skip' }
    ) {
        Resolve-InstallDecision -IsPresent $IsPresent -IsDryRun $IsDryRun -IsConfirmed $IsConfirmed | Should -Be $Expected
    }
}

Describe 'Get-DevRequirementDefinition (pure logic)' {
    It 'returns the five requirements in order' {
        $ids = (Get-DevRequirementDefinition).Id
        $ids | Should -Be @('python', 'poetry', 'msvc', 'project', 'vpk')
    }
    It 'marks only msvc as requiring elevation' {
        $defs = Get-DevRequirementDefinition
        ($defs | Where-Object { $_.RequiresElevation }).Id | Should -Be 'msvc'
    }
    It 'includes a vpk entry with the expected display name (issue #31)' {
        $defs = Get-DevRequirementDefinition
        $vpk = $defs | Where-Object { $_.Id -eq 'vpk' }
        $vpk | Should -Not -BeNullOrEmpty
        $vpk.Name | Should -Be 'Velopack CLI (vpk)'
        $vpk.RequiresElevation | Should -Be $false
    }
}

Describe 'Get-RequirementResult and Resolve-RequirementOutcome (pure logic)' {
    It 'builds a record with the supplied fields' {
        $r = Get-RequirementResult -Id 'python' -Name 'Python' -State 'Satisfied' -Detail 'detail'
        $r.Id | Should -Be 'python'
        $r.State | Should -Be 'Satisfied'
        $r.Detail | Should -Be 'detail'
    }
    It 'rejects an invalid state via ValidateSet' {
        { Get-RequirementResult -Id 'x' -Name 'X' -State 'Bogus' } | Should -Throw
    }
    It 'maps <Decision> to a <ExpectedState> record matching <ExpectedDetail>' -ForEach @(
        @{ Decision = 'WouldInstall'; ExpectedState = 'WouldInstall'; ExpectedDetail = 'dry-run' }
        @{ Decision = 'Declined'; ExpectedState = 'Declined'; ExpectedDetail = 'not confirmed' }
    ) {
        $r = Resolve-RequirementOutcome -Decision $Decision -Id 'poetry' -Name 'Poetry'
        $r.State | Should -Be $ExpectedState
        $r.Detail | Should -Match $ExpectedDetail
    }
    It 'returns null for the Install decision' {
        Resolve-RequirementOutcome -Decision 'Install' -Id 'poetry' -Name 'Poetry' | Should -BeNullOrEmpty
    }
}

Describe 'Get-DevEnvironmentSummary (pure logic)' {
    It 'emits a header and one line per record' {
        $records = @(
            (Get-RequirementResult -Id 'python' -Name 'Python' -State 'Satisfied'),
            (Get-RequirementResult -Id 'poetry' -Name 'Poetry' -State 'Installed' -Detail 'ok')
        )
        $lines = Get-DevEnvironmentSummary -Result $records
        $lines[0] | Should -Be 'Development environment summary:'
        $lines.Count | Should -Be 3
        $lines[1] | Should -Match '\[Satisfied\] Python - python'
        $lines[2] | Should -Match '\[Installed\] Poetry - poetry \(ok\)'
    }
    It 'emits only the header for an empty result set' {
        (Get-DevEnvironmentSummary -Result @()).Count | Should -Be 1
    }
}

Describe 'Approve-RequirementInstall (confirmation seam)' {
    It 'approves unconditionally when AutoApprove is set' {
        Approve-RequirementInstall -Target 'X' -ShouldProcessResult $false -AutoApprove $true | Should -BeTrue
    }
    It 'defers to ShouldProcess when AutoApprove is not set' {
        Approve-RequirementInstall -Target 'X' -ShouldProcessResult $true -AutoApprove $false | Should -BeTrue
        Approve-RequirementInstall -Target 'X' -ShouldProcessResult $false -AutoApprove $false | Should -BeFalse
    }
}

Describe 'Get-DetectedPythonVersion (detection; wrappers mocked)' {
    It 'parses py -0p output and python --version' {
        Mock Test-CommandAvailable { $true } -ParameterFilter { $Name -eq 'py' }
        Mock Test-CommandAvailable { $true } -ParameterFilter { $Name -eq 'python' }
        Mock Invoke-PyLauncherExe { " -V:3.13 *        C:\Python313\python.exe`n -V:3.11          C:\Python311\python.exe" }
        Mock Invoke-PythonExe { 'Python 3.13.12' }
        $versions = Get-DetectedPythonVersion
        $versions | Should -Contain '3.13'
        $versions | Should -Contain '3.11'
        $versions | Should -Contain 'Python 3.13.12'
    }
    It 'returns nothing when neither launcher nor python is available' {
        Mock Test-CommandAvailable { $false }
        Mock Invoke-PyLauncherExe { '' }
        Mock Invoke-PythonExe { '' }
        Get-DetectedPythonVersion | Should -BeNullOrEmpty
        Should -Invoke Invoke-PyLauncherExe -Times 0
        Should -Invoke Invoke-PythonExe -Times 0
    }
}

Describe 'Test-PythonRequirementSatisfied (detection; wrappers mocked)' {
    It 'is satisfied when an in-band interpreter is detected' {
        Mock Get-DetectedPythonVersion { @('3.13.12') }
        Test-PythonRequirementSatisfied | Should -BeTrue
    }
    It 'is not satisfied when only out-of-band interpreters are detected' {
        Mock Get-DetectedPythonVersion { @('3.11.0', '3.15.0') }
        Test-PythonRequirementSatisfied | Should -BeFalse
    }
}

Describe 'Test-PoetryRequirementSatisfied (detection; wrappers mocked)' {
    It 'is satisfied when poetry resolves and reports a version' {
        Mock Test-CommandAvailable { $true } -ParameterFilter { $Name -eq 'poetry' }
        Mock Invoke-PoetryExe { 'Poetry (version 2.3.2)' }
        Test-PoetryRequirementSatisfied | Should -BeTrue
    }
    It 'is not satisfied when poetry is not on the path' {
        Mock Test-CommandAvailable { $false } -ParameterFilter { $Name -eq 'poetry' }
        Mock Invoke-PoetryExe { '' }
        Test-PoetryRequirementSatisfied | Should -BeFalse
        Should -Invoke Invoke-PoetryExe -Times 0
    }
}

Describe 'Test-MsvcRequirementSatisfied (detection; wrappers mocked)' {
    It 'reports not satisfied with empty path when vswhere is absent' {
        Mock Get-VsWhereLocation { '' }
        Mock Invoke-VsWhereExe { '' }
        $r = Test-MsvcRequirementSatisfied
        $r.Satisfied | Should -BeFalse
        $r.VsInstallPath | Should -Be ''
        Should -Invoke Invoke-VsWhereExe -Times 0
    }
    It 'reports the VS path but not satisfied when the VC tools workload is absent' {
        Mock Get-VsWhereLocation { 'C:\vswhere.exe' }
        Mock Invoke-VsWhereExe { 'C:\Program Files\Microsoft Visual Studio\18\Community' } `
            -ParameterFilter { $VsWhereArgs -notcontains '-requires' }
        Mock Invoke-VsWhereExe { '' } -ParameterFilter { $VsWhereArgs -contains '-requires' }
        $r = Test-MsvcRequirementSatisfied
        $r.Satisfied | Should -BeFalse
        $r.VsInstallPath | Should -Be 'C:\Program Files\Microsoft Visual Studio\18\Community'
    }
    It 'reports satisfied when the VC tools workload is present' {
        Mock Get-VsWhereLocation { 'C:\vswhere.exe' }
        Mock Invoke-VsWhereExe { 'C:\VS\Community' }
        $r = Test-MsvcRequirementSatisfied
        $r.Satisfied | Should -BeTrue
        $r.VsInstallPath | Should -Be 'C:\VS\Community'
    }
}

Describe 'Test-RequirementPresent (orchestration; detection mocked)' {
    It 'reports project as never present (poetry install is idempotent)' {
        (Test-RequirementPresent -Id 'project').IsPresent | Should -BeFalse
    }
    It 'throws on an unknown id' {
        { Test-RequirementPresent -Id 'nope' } | Should -Throw '*Unknown requirement id*'
    }
    It 'returns the MSVC detection state for the msvc id' {
        Mock Test-MsvcRequirementSatisfied { [pscustomobject]@{ Satisfied = $true; VsInstallPath = 'C:\VS' } }
        $state = Test-RequirementPresent -Id 'msvc'
        $state.IsPresent | Should -BeTrue
        $state.MsvcState.VsInstallPath | Should -Be 'C:\VS'
    }
}

Describe 'Install actions (seams mocked; no real executables)' {
    It 'Install-PythonRequirement uses winget when available' {
        Mock Test-WingetAvailable { $true }
        Mock Invoke-WingetExe { '' }
        Install-PythonRequirement
        Should -Invoke Invoke-WingetExe -Times 1 -ParameterFilter { $WingetArgs -contains 'Python.Python.3.12' }
    }
    It 'Install-PythonRequirement throws when winget is absent' {
        Mock Test-WingetAvailable { $false }
        Mock Invoke-WingetExe { '' }
        { Install-PythonRequirement } | Should -Throw '*winget is not available*'
        Should -Invoke Invoke-WingetExe -Times 0
    }
    It 'Install-PoetryRequirement runs the official installer' {
        Mock Invoke-PoetryInstaller { '' }
        Install-PoetryRequirement
        Should -Invoke Invoke-PoetryInstaller -Times 1
    }
    It 'Install-MsvcRequirement modifies an existing VS install via the elevated VS setup' {
        Mock Invoke-ElevatedProcess { 0 }
        Install-MsvcRequirement -VsInstallPath 'C:\VS\Community' -IsElevated $false
        Should -Invoke Invoke-ElevatedProcess -Times 1 -ParameterFilter {
            $FilePath -match 'setup\.exe$' -and $ArgumentList -contains 'Microsoft.VisualStudio.Workload.NativeDesktop'
        }
    }
    It 'Install-MsvcRequirement falls back to winget BuildTools when no VS install exists' {
        Mock Test-WingetAvailable { $true }
        Mock Invoke-ElevatedProcess { 0 }
        Install-MsvcRequirement -VsInstallPath '' -IsElevated $false
        Should -Invoke Invoke-ElevatedProcess -Times 1 -ParameterFilter {
            $FilePath -eq 'winget' -and ($ArgumentList -contains 'Microsoft.VisualStudio.2022.BuildTools')
        }
    }
    It 'Install-MsvcRequirement throws when no VS install and no winget' {
        Mock Test-WingetAvailable { $false }
        Mock Invoke-ElevatedProcess { 0 }
        { Install-MsvcRequirement -VsInstallPath '' -IsElevated $false } | Should -Throw '*winget is not available*'
        Should -Invoke Invoke-ElevatedProcess -Times 0
    }
    It 'Install-ProjectRequirement clears VIRTUAL_ENV around poetry install and restores it' {
        Mock Get-EnvironmentVariableValue { 'C:\global\python' } -ParameterFilter { $Name -eq 'VIRTUAL_ENV' }
        Mock Set-EnvironmentVariableValue { }
        Mock Invoke-PoetryExe { '' }
        Install-ProjectRequirement
        # VIRTUAL_ENV cleared before the poetry call and restored to the prior value after.
        Should -Invoke Set-EnvironmentVariableValue -Times 1 -ParameterFilter {
            $Name -eq 'VIRTUAL_ENV' -and [string]::IsNullOrEmpty($Value)
        }
        Should -Invoke Set-EnvironmentVariableValue -Times 1 -ParameterFilter {
            $Name -eq 'VIRTUAL_ENV' -and $Value -eq 'C:\global\python'
        }
        Should -Invoke Invoke-PoetryExe -Times 1 -ParameterFilter { $PoetryArgs -contains 'install' }
    }
}

Describe 'Invoke-RequirementInstall (dispatch; install actions mocked)' {
    It 'dispatches python to Install-PythonRequirement' {
        Mock Install-PythonRequirement { }
        Invoke-RequirementInstall -Id 'python' -IsElevated $false
        Should -Invoke Install-PythonRequirement -Times 1
    }
    It 'passes the MSVC install path through to Install-MsvcRequirement' {
        Mock Install-MsvcRequirement { }
        $msvc = [ordered]@{ Satisfied = $false; VsInstallPath = 'C:\VS' }
        Invoke-RequirementInstall -Id 'msvc' -MsvcState $msvc -IsElevated $true
        Should -Invoke Install-MsvcRequirement -Times 1 -ParameterFilter {
            $VsInstallPath -eq 'C:\VS' -and $IsElevated -eq $true
        }
    }
    It 'throws on an unknown id' {
        { Invoke-RequirementInstall -Id 'nope' -IsElevated $false } | Should -Throw '*Unknown requirement id*'
    }
}

Describe 'Invoke-RequirementCheck (orchestration of one requirement)' {
    BeforeEach {
        $script:Def = @{ Id = 'poetry'; Name = 'Poetry'; RequiresElevation = $false }
    }
    It 'returns Satisfied without installing when already present' {
        Mock Test-RequirementPresent { [pscustomobject]@{ IsPresent = $true; MsvcState = $null } }
        Mock Invoke-RequirementInstall { }
        $r = Invoke-RequirementCheck -Definition $Def -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $r.State | Should -Be 'Satisfied'
        Should -Invoke Invoke-RequirementInstall -Times 0
    }
    It 'returns WouldInstall on a dry run without installing' {
        Mock Test-RequirementPresent { [pscustomobject]@{ IsPresent = $false; MsvcState = $null } }
        Mock Invoke-RequirementInstall { }
        $r = Invoke-RequirementCheck -Definition $Def -IsDryRun $true -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $r.State | Should -Be 'WouldInstall'
        Should -Invoke Invoke-RequirementInstall -Times 0
    }
    It 'returns Declined when not confirmed and not auto-approved' {
        Mock Test-RequirementPresent { [pscustomobject]@{ IsPresent = $false; MsvcState = $null } }
        Mock Invoke-RequirementInstall { }
        $r = Invoke-RequirementCheck -Definition $Def -IsDryRun $false -AutoApprove $false `
            -ShouldProcessCallback $DeclineAll -IsElevated $false
        $r.State | Should -Be 'Declined'
        Should -Invoke Invoke-RequirementInstall -Times 0
    }
    It 'returns Installed after a confirmed install' {
        Mock Test-RequirementPresent { [pscustomobject]@{ IsPresent = $false; MsvcState = $null } }
        Mock Invoke-RequirementInstall { }
        $r = Invoke-RequirementCheck -Definition $Def -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $r.State | Should -Be 'Installed'
        Should -Invoke Invoke-RequirementInstall -Times 1
    }
    It 'returns Failed with the error detail when the install throws' {
        Mock Test-RequirementPresent { [pscustomobject]@{ IsPresent = $false; MsvcState = $null } }
        Mock Invoke-RequirementInstall { throw 'install boom' }
        $r = Invoke-RequirementCheck -Definition $Def -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $r.State | Should -Be 'Failed'
        $r.Detail | Should -Match 'install boom'
    }
}

Describe 'Invoke-DevEnvironmentSetup (full orchestration; seams mocked)' {
    It 'runs every requirement in order and returns one record each' {
        # All host tools present; project is always (re)provisioned.
        Mock Test-PythonRequirementSatisfied { $true }
        Mock Test-PoetryRequirementSatisfied { $true }
        Mock Test-MsvcRequirementSatisfied { [pscustomobject]@{ Satisfied = $true; VsInstallPath = 'C:\VS' } }
        Mock Test-VpkRequirementSatisfied { $true }
        Mock Invoke-RequirementInstall { }
        $results = Invoke-DevEnvironmentSetup -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $results.Id | Should -Be @('python', 'poetry', 'msvc', 'project', 'vpk')
        ($results | Where-Object { $_.Id -eq 'python' }).State | Should -Be 'Satisfied'
        ($results | Where-Object { $_.Id -eq 'project' }).State | Should -Be 'Installed'
        ($results | Where-Object { $_.Id -eq 'vpk' }).State | Should -Be 'Satisfied'
        Should -Invoke Invoke-RequirementInstall -Times 1 -ParameterFilter { $Id -eq 'project' }
    }
    It 'reports WouldInstall for every missing requirement on a dry run' {
        Mock Test-PythonRequirementSatisfied { $false }
        Mock Test-PoetryRequirementSatisfied { $false }
        Mock Test-MsvcRequirementSatisfied { [pscustomobject]@{ Satisfied = $false; VsInstallPath = '' } }
        Mock Test-VpkRequirementSatisfied { $false }
        Mock Invoke-RequirementInstall { }
        $results = Invoke-DevEnvironmentSetup -IsDryRun $true -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        ($results | Where-Object { $_.State -ne 'WouldInstall' }) | Should -BeNullOrEmpty
        Should -Invoke Invoke-RequirementInstall -Times 0
    }
}

Describe 'Wrapper seam contracts (no real executables invoked)' {
    It 'Test-WingetAvailable delegates to Test-CommandAvailable for winget' {
        Mock Test-CommandAvailable { $true } -ParameterFilter { $Name -eq 'winget' }
        Test-WingetAvailable | Should -BeTrue
        Should -Invoke Test-CommandAvailable -Times 1 -ParameterFilter { $Name -eq 'winget' }
    }
}

Describe 'Invoke-RequirementInstall dispatch for poetry and project (install actions mocked)' {
    It 'dispatches poetry to Install-PoetryRequirement' {
        Mock Install-PoetryRequirement { }
        Invoke-RequirementInstall -Id 'poetry' -IsElevated $false
        Should -Invoke Install-PoetryRequirement -Times 1
    }
    It 'dispatches project to Install-ProjectRequirement' {
        Mock Install-ProjectRequirement { }
        Invoke-RequirementInstall -Id 'project' -IsElevated $false
        Should -Invoke Install-ProjectRequirement -Times 1
    }
}

Describe 'Invoke-DevEnvironmentMain (entrypoint logic; setup mocked)' {
    It 'returns exit code 0 when no requirement failed' {
        Mock Invoke-DevEnvironmentSetup {
            @(
                (Get-RequirementResult -Id 'python' -Name 'Python' -State 'Satisfied'),
                (Get-RequirementResult -Id 'project' -Name 'Project' -State 'Installed')
            )
        }
        Mock Write-Information { }
        Invoke-DevEnvironmentMain -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false | Should -Be 0
        Should -Invoke Write-Information -Times 1 -ParameterFilter {
            $MessageData -eq 'Development environment summary:'
        }
    }
    It 'returns exit code 1 when any requirement failed' {
        Mock Invoke-DevEnvironmentSetup {
            @((Get-RequirementResult -Id 'msvc' -Name 'MSVC' -State 'Failed' -Detail 'boom'))
        }
        Mock Write-Information { }
        Invoke-DevEnvironmentMain -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false | Should -Be 1
    }
}

Describe 'Host adapter seams (no irreversible side effects)' {
    It 'Test-IsElevated returns a boolean' {
        Test-IsElevated | Should -BeOfType [bool]
    }
    It 'Test-CommandAvailable returns true for an always-present cmdlet' {
        Test-CommandAvailable -Name 'Get-Command' | Should -BeTrue
    }
    It 'Test-CommandAvailable returns false for a name that cannot resolve' {
        Test-CommandAvailable -Name 'definitely-not-a-real-command-xyz' | Should -BeFalse
    }
    It 'Get-VsWhereLocation returns a string (path or empty)' {
        Get-VsWhereLocation | Should -BeOfType [string]
    }
    It 'environment variable get/set round-trips a process-scoped value' {
        $name = 'MIXCALC_DEVENV_TEST_VAR'
        $original = Get-EnvironmentVariableValue -Name $name
        try {
            Set-EnvironmentVariableValue -Name $name -Value 'seam-value'
            Get-EnvironmentVariableValue -Name $name | Should -Be 'seam-value'
            Set-EnvironmentVariableValue -Name $name -Value $null
            Get-EnvironmentVariableValue -Name $name | Should -BeNullOrEmpty
        }
        finally { Set-EnvironmentVariableValue -Name $name -Value $original }
    }
}

Describe 'vpk requirement (issue #31)' {
    BeforeEach {
        $script:VpkDef = @{ Id = 'vpk'; Name = 'Velopack CLI (vpk)'; RequiresElevation = $false }
    }
    It 'Test-VpkRequirementSatisfied is true when vpk is on PATH' {
        Mock Test-CommandAvailable { $true } -ParameterFilter { $Name -eq 'vpk' }
        Test-VpkRequirementSatisfied | Should -BeTrue
    }
    It 'Test-VpkRequirementSatisfied is false when vpk is not on PATH' {
        Mock Test-CommandAvailable { $false } -ParameterFilter { $Name -eq 'vpk' }
        Test-VpkRequirementSatisfied | Should -BeFalse
    }
    It 'Install-VpkRequirement invokes dotnet tool install -g vpk' {
        Mock Invoke-DotnetExe { '' }
        Install-VpkRequirement
        Should -Invoke Invoke-DotnetExe -Times 1 -ParameterFilter {
            ($DotnetArgs -contains 'tool') -and ($DotnetArgs -contains 'install') -and `
            ($DotnetArgs -contains '-g') -and ($DotnetArgs -contains 'vpk')
        }
    }
    It 'Invoke-RequirementInstall dispatches vpk to Install-VpkRequirement' {
        Mock Install-VpkRequirement { }
        Invoke-RequirementInstall -Id 'vpk' -IsElevated $false
        Should -Invoke Install-VpkRequirement -Times 1
    }
    It 'Test-RequirementPresent returns the vpk detection state for the vpk id' {
        Mock Test-VpkRequirementSatisfied { $true }
        (Test-RequirementPresent -Id 'vpk').IsPresent | Should -BeTrue
    }
    It 'orchestrator records Installed when vpk is absent and confirmed' {
        Mock Test-VpkRequirementSatisfied { $false }
        Mock Install-VpkRequirement { }
        $r = Invoke-RequirementCheck -Definition $VpkDef -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $r.State | Should -Be 'Installed'
        Should -Invoke Install-VpkRequirement -Times 1
    }
    It 'orchestrator records Satisfied when vpk is present (no install)' {
        Mock Test-VpkRequirementSatisfied { $true }
        Mock Install-VpkRequirement { }
        $r = Invoke-RequirementCheck -Definition $VpkDef -IsDryRun $false -AutoApprove $true `
            -ShouldProcessCallback $ApproveAll -IsElevated $false
        $r.State | Should -Be 'Satisfied'
        Should -Invoke Install-VpkRequirement -Times 0
    }
}

