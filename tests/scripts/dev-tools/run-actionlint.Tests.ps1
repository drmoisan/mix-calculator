#Requires -Version 7.0
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }

<#
.SYNOPSIS
    Pester v5 tests for scripts/dev-tools/run-actionlint.ps1.

.DESCRIPTION
    Pure logic (path resolution, the missing-tool message) is exercised through
    real code paths. The orchestration entrypoint is exercised with the external
    executable wrapper (Invoke-ActionlintExe) and the host/filesystem adapter
    seams (Get-ActionlintSource, Get-WorkflowFile, Test-Path) mocked, so no real
    actionlint, PATH, or workflow files are required. The script is dot-sourced
    (its entrypoint is guarded) so its functions are available in the test scope.
#>

BeforeAll {
    $script:ScriptPath = Join-Path $PSScriptRoot '..\..\..\scripts\dev-tools\run-actionlint.ps1'
    $script:ScriptPath = (Resolve-Path -LiteralPath $script:ScriptPath).Path

    # Dot-source the script. Its entrypoint guard returns early under dot-source.
    . $script:ScriptPath

    # A stable script root used by path-resolution tests.
    $script:FakeScriptRoot = Join-Path (Join-Path 'C:\repo' 'scripts') 'dev-tools'
}

Describe 'Resolve-WorkflowPath (pure logic)' {
    It 'returns the requested path verbatim when one is supplied' {
        Resolve-WorkflowPath -RequestedPath 'D:\custom\workflows' -ScriptRoot $FakeScriptRoot |
            Should -Be 'D:\custom\workflows'
    }
    It 'derives the repo .github/workflows path from the script root when no path is supplied' {
        $resolved = Resolve-WorkflowPath -RequestedPath '' -ScriptRoot $FakeScriptRoot
        # Two levels up from scripts/dev-tools is the repo root.
        $resolved | Should -Be (Join-Path 'C:\repo' '.github/workflows')
    }
}

Describe 'Get-ActionlintMissingMessage (pure logic)' {
    It 'names the tool and includes an install hint' {
        $message = Get-ActionlintMissingMessage
        $message | Should -Match 'actionlint was not found'
        $message | Should -Match 'winget install'
    }
}

Describe 'Get-ActionlintSource (adapter seam)' {
    It 'returns a string (resolved path or empty)' {
        Get-ActionlintSource | Should -BeOfType [string]
    }
}

Describe 'Get-WorkflowFile (adapter seam)' {
    It 'returns only .yml/.yaml files from the repository workflows directory' {
        # Reads existing repository files (no temp files); the CI workflow set is committed.
        $workflowDir = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\.github\workflows')).Path
        $files = Get-WorkflowFile -Path $workflowDir

        $files | Should -Not -BeNullOrEmpty
        ($files | Where-Object { $_ -notmatch '\.ya?ml$' }) | Should -BeNullOrEmpty
        ($files | Where-Object { $_ -match 'ci\.yml$' }) | Should -Not -BeNullOrEmpty
    }
}

Describe 'Invoke-WorkflowLintMain (entrypoint logic; seams mocked)' {
    It 'returns 0 when actionlint resolves, files are found, and the linter is clean' {
        Mock Test-Path { $true }
        Mock Get-ActionlintSource { 'C:\tools\actionlint.exe' }
        Mock Get-WorkflowFile { @('C:\repo\.github\workflows\ci.yml') }
        Mock Invoke-ActionlintExe { 0 }
        Mock Write-Information { }

        Invoke-WorkflowLintMain -WorkflowPath '' -ScriptRoot $FakeScriptRoot | Should -Be 0
        Should -Invoke Invoke-ActionlintExe -Times 1 -ParameterFilter {
            $ActionlintArgs -contains '-color' -and $ActionlintArgs -contains 'C:\repo\.github\workflows\ci.yml'
        }
    }
    It 'throws when actionlint reports problems' {
        Mock Test-Path { $true }
        Mock Get-ActionlintSource { 'C:\tools\actionlint.exe' }
        Mock Get-WorkflowFile { @('C:\repo\.github\workflows\ci.yml') }
        Mock Invoke-ActionlintExe { 1 }
        Mock Write-Information { }

        { Invoke-WorkflowLintMain -WorkflowPath '' -ScriptRoot $FakeScriptRoot } |
            Should -Throw '*actionlint reported problems*'
    }
    It 'throws installation guidance when actionlint is not on PATH' {
        Mock Test-Path { $true }
        Mock Get-ActionlintSource { '' }
        Mock Invoke-ActionlintExe { 0 }

        { Invoke-WorkflowLintMain -WorkflowPath '' -ScriptRoot $FakeScriptRoot } |
            Should -Throw '*actionlint was not found*'
        Should -Invoke Invoke-ActionlintExe -Times 0
    }
    It 'throws when the workflow directory does not exist' {
        Mock Test-Path { $false }
        Mock Get-ActionlintSource { 'C:\tools\actionlint.exe' }

        { Invoke-WorkflowLintMain -WorkflowPath 'D:\missing' -ScriptRoot $FakeScriptRoot } |
            Should -Throw '*Workflow directory not found*'
    }
    It 'returns 0 and warns when the directory has no workflow files' {
        Mock Test-Path { $true }
        Mock Get-ActionlintSource { 'C:\tools\actionlint.exe' }
        Mock Get-WorkflowFile { @() }
        Mock Invoke-ActionlintExe { 0 }
        Mock Write-Information { }
        Mock Write-Warning { }

        Invoke-WorkflowLintMain -WorkflowPath 'D:\empty' -ScriptRoot $FakeScriptRoot | Should -Be 0
        Should -Invoke Write-Warning -Times 1
        Should -Invoke Invoke-ActionlintExe -Times 0
    }
}
