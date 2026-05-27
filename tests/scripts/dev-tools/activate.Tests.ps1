#Requires -Version 7.0
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }

<#
.SYNOPSIS
    Pester v5 tests for scripts/dev-tools/activate.ps1.

.DESCRIPTION
    Exercises the pure logic of activate.ps1 through real code paths with no real
    venv, PATH dependence, live executables, or temp files:
      - Resolve-RepoRoot     (depth-robust ancestor walk via an injected probe)
      - Get-RepoRelativePrompt (prompt-string construction for all path cases)
      - Get-DefaultPrompt    (no-venv fallback form)
      - Test-IsDotSourced / Get-NotDotSourcedMessage (non-dot-source guard)

    The script's function definitions are imported via AST extraction (per
    .claude/rules/powershell.md Mocking Rules #4): the script is parsed with
    [System.Management.Automation.Language.Parser]::ParseFile, only the
    FunctionDefinitionAst nodes are selected, and those definitions are
    dot-sourced into the test scope. This imports the pure and seam functions
    without executing the entrypoint, so no test-only switch is required in
    production code.
#>

BeforeAll {
    $script:ScriptPath = Join-Path $PSScriptRoot '..\..\..\scripts\dev-tools\activate.ps1'
    $script:ScriptPath = (Resolve-Path -LiteralPath $script:ScriptPath).Path

    # Parse the script and import only its function definitions (AST extraction),
    # so the entrypoint side effects (venv activation, prompt install) never run.
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $script:ScriptPath, [ref] $tokens, [ref] $parseErrors)
    if ($parseErrors) {
        throw "Failed to parse $($script:ScriptPath): $($parseErrors -join '; ')"
    }

    $functionAsts = $ast.FindAll(
        { param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] },
        $false)

    # Define each function in the test scope from its own AST. Using the AST's
    # ScriptBlock (rather than rebuilt text) preserves the original file/line
    # mapping, so Pester attributes executed lines back to activate.ps1 for
    # coverage. Only the function definitions are imported; the entrypoint
    # statements are never executed.
    foreach ($fn in $functionAsts) {
        Set-Item -Path ("Function:\{0}" -f $fn.Name) -Value $fn.Body.GetScriptBlock()
    }

    # Reliable global:prompt restore for tests that install a global prompt.
    # Recreating from captured source text (rather than reassigning a captured
    # ScriptBlock) restores the original global function deterministically from
    # the nested AfterEach scope, preventing prompt leakage across tests/host.
    function Restore-GlobalPrompt {
        param([Parameter()][AllowNull()][string] $SavedPromptText)

        Remove-Item -Path Function:\prompt -Force -ErrorAction SilentlyContinue
        if ($SavedPromptText) {
            $null = New-Item -Path Function:\global:prompt `
                -Value ([scriptblock]::Create($SavedPromptText))
        }
    }
}

Describe 'Get-RepoRelativePrompt (pure logic)' {
    It 'renders the at-root case with no relative segment' {
        Get-RepoRelativePrompt -CurrentPath 'C:\repo\mix-calculator' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator)> '
    }

    It 'renders a one-level descendant with a leading backslash' {
        Get-RepoRelativePrompt -CurrentPath 'C:\repo\mix-calculator\.claude' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator)\.claude> '
    }

    It 'renders deeper nesting with the full relative subpath' {
        Get-RepoRelativePrompt -CurrentPath 'C:\repo\mix-calculator\scripts\dev-tools' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator)\scripts\dev-tools> '
    }

    It 'renders the outside-tree case with a space-prefixed absolute path' {
        Get-RepoRelativePrompt -CurrentPath 'D:\elsewhere' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator) D:\elsewhere> '
    }

    It 'treats a sibling whose name shares the root prefix as outside the tree' {
        # 'C:\repo\mix-calculator-extra' must not be treated as a descendant of
        # 'C:\repo\mix-calculator'; the trailing-separator check guards this.
        Get-RepoRelativePrompt -CurrentPath 'C:\repo\mix-calculator-extra' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator) C:\repo\mix-calculator-extra> '
    }

    It 'compares paths case-insensitively for the at-root case' {
        Get-RepoRelativePrompt -CurrentPath 'c:\REPO\Mix-Calculator' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator)> '
    }

    It 'compares paths case-insensitively for the descendant case' {
        Get-RepoRelativePrompt -CurrentPath 'C:\REPO\MIX-CALCULATOR\.claude' -VenvRoot 'C:\repo\mix-calculator' |
            Should -Be '(mix-calculator)\.claude> '
    }
}

Describe 'Get-DefaultPrompt (no-venv fallback)' {
    It 'renders the default PS-prefixed path form' {
        Get-DefaultPrompt -CurrentPath 'C:\repo\mix-calculator' |
            Should -Be 'PS C:\repo\mix-calculator> '
    }
}

Describe 'Get-VenvAwarePrompt (prompt decision used by the shim)' {
    It 'falls back to the default form when the venv value is empty' {
        Get-VenvAwarePrompt -CurrentPath 'C:\repo\mix-calculator' -VenvEnv '' |
            Should -Be 'PS C:\repo\mix-calculator> '
    }

    It 'falls back to the default form when the venv value is null' {
        Get-VenvAwarePrompt -CurrentPath 'C:\repo\mix-calculator' -VenvEnv $null |
            Should -Be 'PS C:\repo\mix-calculator> '
    }

    It 'derives the repo root from the venv parent and renders the at-root prompt' {
        # VIRTUAL_ENV points at <repoRoot>\.venv, so its parent is the repo root.
        Get-VenvAwarePrompt -CurrentPath 'C:\repo\mix-calculator' -VenvEnv 'C:\repo\mix-calculator\.venv' |
            Should -Be '(mix-calculator)> '
    }

    It 'renders a descendant prompt from the venv parent' {
        Get-VenvAwarePrompt -CurrentPath 'C:\repo\mix-calculator\.claude' -VenvEnv 'C:\repo\mix-calculator\.venv' |
            Should -Be '(mix-calculator)\.claude> '
    }
}

Describe 'Resolve-RepoRoot (depth-robust ancestor walk)' {
    It 'returns the start directory when it directly contains .venv' {
        $probe = { param([string] $Path) $Path -eq 'C:\repo\mix-calculator\.venv' }
        Resolve-RepoRoot -StartDir 'C:\repo\mix-calculator' -PathExists $probe |
            Should -Be 'C:\repo\mix-calculator'
    }

    It 'walks up from a two-level-deep start to the ancestor containing .venv' {
        $probe = { param([string] $Path) $Path -eq 'C:\repo\mix-calculator\.venv' }
        Resolve-RepoRoot -StartDir 'C:\repo\mix-calculator\scripts\dev-tools' -PathExists $probe |
            Should -Be 'C:\repo\mix-calculator'
    }

    It 'walks up from a deeper start regardless of depth' {
        $probe = { param([string] $Path) $Path -eq 'C:\repo\mix-calculator\.venv' }
        Resolve-RepoRoot -StartDir 'C:\repo\mix-calculator\a\b\c\d' -PathExists $probe |
            Should -Be 'C:\repo\mix-calculator'
    }

    It 'returns the nearest qualifying ancestor when multiple ancestors contain .venv' {
        $probe = {
            param([string] $Path)
            $Path -eq 'C:\repo\mix-calculator\.venv' -or $Path -eq 'C:\repo\.venv'
        }
        Resolve-RepoRoot -StartDir 'C:\repo\mix-calculator\scripts' -PathExists $probe |
            Should -Be 'C:\repo\mix-calculator'
    }

    It 'returns an empty string when no ancestor contains .venv' {
        # Probe never matches any path; -PathExists references $Path so no
        # candidate ever qualifies and the walk exhausts to the drive root.
        $probe = { param([string] $Path) $Path -eq '\\never\matches' }
        Resolve-RepoRoot -StartDir 'C:\repo\mix-calculator\scripts\dev-tools' -PathExists $probe |
            Should -Be ''
    }
}

Describe 'Test-IsDotSourced (non-dot-source guard predicate)' {
    It 'returns true when the invocation name is the dot operator' {
        Test-IsDotSourced -InvocationName '.' | Should -BeTrue
    }

    It 'returns false when the invocation name is the script name' {
        Test-IsDotSourced -InvocationName 'activate.ps1' | Should -BeFalse
    }

    It 'returns false when the invocation name is the ampersand operator' {
        Test-IsDotSourced -InvocationName '&' | Should -BeFalse
    }

    It 'returns false when the invocation name is empty' {
        Test-IsDotSourced -InvocationName '' | Should -BeFalse
    }
}

Describe 'Get-NotDotSourcedMessage (corrective guidance)' {
    It 'states that the script must be dot-sourced' {
        Get-NotDotSourcedMessage | Should -Match 'must be dot-sourced'
    }

    It 'includes the correct dot-source command' {
        Get-NotDotSourcedMessage | Should -Match '\. \.\\scripts\\dev-tools\\activate\.ps1'
    }
}

Describe 'Invoke-VenvActivation (orchestration; seams mocked)' {
    BeforeEach {
        # Capture the prompt's source text so installing global:prompt during a
        # test can be fully reverted afterward and does not leak into other tests
        # or the test host. Source text (not the ScriptBlock object) is captured
        # because recreating from text restores reliably from this nested scope.
        $existingPrompt = Get-Command -Name 'prompt' -CommandType Function -ErrorAction SilentlyContinue
        $script:SavedPromptText = if ($existingPrompt) { $existingPrompt.ScriptBlock.ToString() } else { $null }
        $script:SavedVirtualEnv = $env:VIRTUAL_ENV
        $script:SavedDisablePrompt = $env:VIRTUAL_ENV_DISABLE_PROMPT
    }

    AfterEach {
        Restore-GlobalPrompt -SavedPromptText $script:SavedPromptText
        if ($null -eq $script:SavedVirtualEnv) {
            Remove-Item Env:\VIRTUAL_ENV -ErrorAction SilentlyContinue
        }
        else {
            $env:VIRTUAL_ENV = $script:SavedVirtualEnv
        }
        if ($null -eq $script:SavedDisablePrompt) {
            Remove-Item Env:\VIRTUAL_ENV_DISABLE_PROMPT -ErrorAction SilentlyContinue
        }
        else {
            $env:VIRTUAL_ENV_DISABLE_PROMPT = $script:SavedDisablePrompt
        }
    }

    It 'activates the venv and installs the prompt when a .venv ancestor exists' {
        # Test-Path returns $true for both the .venv probe (via Resolve-RepoRoot)
        # and the Activate.ps1 existence check.
        Mock Test-Path { $true }
        Mock Invoke-VenvActivateScript { }

        Invoke-VenvActivation -ScriptRoot 'C:\repo\mix-calculator\scripts\dev-tools'

        $env:VIRTUAL_ENV_DISABLE_PROMPT | Should -Be '1'
        Should -Invoke Invoke-VenvActivateScript -Times 1 -ParameterFilter {
            $ActivatePath -match '\.venv\\Scripts\\Activate\.ps1$'
        }
        Get-Command -Name 'prompt' -CommandType Function | Should -Not -BeNullOrEmpty
    }

    It 'throws guidance when no .venv ancestor is found' {
        Mock Test-Path { $false }
        Mock Invoke-VenvActivateScript { }

        { Invoke-VenvActivation -ScriptRoot 'C:\repo\mix-calculator\scripts\dev-tools' } |
            Should -Throw "*Could not locate a '.venv' directory*"
        Should -Invoke Invoke-VenvActivateScript -Times 0
    }

    It 'throws when the resolved Activate.ps1 is missing' {
        # The .venv directory probe succeeds (Resolve-RepoRoot finds the root),
        # but the Activate.ps1 file probe fails.
        Mock Test-Path {
            param([string] $LiteralPath)
            $LiteralPath -notmatch 'Activate\.ps1$'
        }
        Mock Invoke-VenvActivateScript { }

        { Invoke-VenvActivation -ScriptRoot 'C:\repo\mix-calculator\scripts\dev-tools' } |
            Should -Throw '*venv missing at*'
        Should -Invoke Invoke-VenvActivateScript -Times 0
    }

    It 'installs a prompt that delegates to the venv-aware builder' {
        Mock Test-Path { $true }
        Mock Invoke-VenvActivateScript { }

        Invoke-VenvActivation -ScriptRoot 'C:\repo\mix-calculator\scripts\dev-tools'

        # Drive the installed prompt with a known venv value and verify delegation.
        $env:VIRTUAL_ENV = 'C:\repo\mix-calculator\.venv'
        prompt | Should -Match '^\(mix-calculator\)'
    }
}

Describe 'Invoke-VenvActivateScript (dot-source seam)' {
    It 'fails fast when the Activate.ps1 path does not exist' {
        # The real body dot-sources $ActivatePath; a nonexistent path makes the
        # dot-source fail under the script''s Stop preference, so no real
        # Activate.ps1 is executed. The path is deterministic and never created.
        $missing = 'C:\repo\mix-calculator\.venv\Scripts\DoesNotExist-Activate.ps1'
        { Invoke-VenvActivateScript -ActivatePath $missing } | Should -Throw
    }
}

Describe 'Entrypoint guard (script run without dot-sourcing)' {
    BeforeEach {
        # Preserve session prompt/venv state; the guard path does not modify it,
        # but restoring guarantees independence even if behavior regresses.
        $existingPrompt = Get-Command -Name 'prompt' -CommandType Function -ErrorAction SilentlyContinue
        $script:SavedPromptText = if ($existingPrompt) { $existingPrompt.ScriptBlock.ToString() } else { $null }
        $script:SavedVirtualEnv = $env:VIRTUAL_ENV
    }

    AfterEach {
        Restore-GlobalPrompt -SavedPromptText $script:SavedPromptText
        if ($null -eq $script:SavedVirtualEnv) {
            Remove-Item Env:\VIRTUAL_ENV -ErrorAction SilentlyContinue
        }
        else {
            $env:VIRTUAL_ENV = $script:SavedVirtualEnv
        }
    }

    It 'surfaces corrective guidance instead of activating when not dot-sourced' {
        # Invoking with the call operator (not dot-sourcing) runs the entrypoint.
        # Test-IsDotSourced returns false, so the script writes the guidance error
        # and returns before reaching Invoke-VenvActivation - no venv side effects.
        { & $script:ScriptPath } | Should -Throw '*must be dot-sourced*'
    }
}
