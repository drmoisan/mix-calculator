#Requires -Version 7.0
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }

<#
.SYNOPSIS
    Pester v5 fixture tests for the remediation_loop validator in
    .claude/hooks/validate-orchestrator-output.ps1 (issue #25, AC#9).

.DESCRIPTION
    Dot-sources the hook (its entrypoint guard returns early under dot-source)
    and exercises Test-RemediationLoopShape against fixture orchestrator-state
    objects. No real disk access, no temp files, no network. The fixtures are
    constructed in-memory via New-ConformantCycle and mutated to produce
    malformed variants for the negative-path cases.
#>

BeforeAll {
    $script:HookPath = Join-Path $PSScriptRoot '..\..\..\.claude\hooks\validate-orchestrator-output.ps1'
    $script:HookPath = (Resolve-Path -LiteralPath $script:HookPath).Path
    . $script:HookPath

    function script:New-ConformantCycle {
        param(
            [string] $EntryTs = '2026-06-01T09-15',
            [string] $ExitTs = '2026-06-01T10-45',
            [int] $PreflightIterations = 2,
            [string] $PreflightFinalStatus = 'clear',
            [string] $ExecutionStatus = 'complete',
            [int] $BlockingCount = 0,
            [bool] $ExitConditionMet = $true,
            [string] $PlanPath = 'docs/features/active/example-feature-99/remediation-plan.2026-06-01T09-15.md'
        )

        return [pscustomobject]@{
            entry_timestamp    = $EntryTs
            exit_timestamp     = $ExitTs
            inputs_path        = 'docs/features/active/example-feature-99/remediation-inputs.2026-06-01T09-15.md'
            plan_path          = $PlanPath
            preflight          = [pscustomobject]@{
                iterations   = $PreflightIterations
                final_status = $PreflightFinalStatus
            }
            execution_status   = $ExecutionStatus
            audit_paths        = [pscustomobject]@{
                code_review   = 'docs/features/active/example-feature-99/code-review.2026-06-01T10-45.md'
                feature_audit = 'docs/features/active/example-feature-99/feature-audit.2026-06-01T10-45.md'
                policy_audit  = 'docs/features/active/example-feature-99/policy-audit.2026-06-01T10-45.md'
            }
            blocking_count     = $BlockingCount
            exit_condition_met = $ExitConditionMet
        }
    }

    function script:New-ConformantLoop {
        param(
            [int] $CycleCount = 1
        )

        $cycles = @()
        for ($i = 1; $i -le $CycleCount; $i++) {
            $cycles += (New-ConformantCycle)
        }

        return [pscustomobject]@{
            current_cycle = $CycleCount
            cycles        = $cycles
        }
    }
}

Describe 'Test-RemediationLoopShape — positive paths' {
    It 'accepts a state with no remediation_loop field (null input)' {
        # Arrange
        $loop = $null

        # Act
        $result = Test-RemediationLoopShape -RemediationLoop $loop

        # Assert
        $result.Ok | Should -BeTrue
        $result.Message | Should -BeNullOrEmpty
    }

    It 'accepts a state with a single conformant cycle' {
        # Arrange
        $loop = New-ConformantLoop -CycleCount 1

        # Act
        $result = Test-RemediationLoopShape -RemediationLoop $loop

        # Assert
        $result.Ok | Should -BeTrue
        $result.Message | Should -BeNullOrEmpty
    }

    It 'accepts a state with multiple sequential conformant cycles' {
        # Arrange
        $loop = New-ConformantLoop -CycleCount 3

        # Act
        $result = Test-RemediationLoopShape -RemediationLoop $loop

        # Assert
        $result.Ok | Should -BeTrue
        $result.Message | Should -BeNullOrEmpty
    }
}

Describe 'Test-RemediationLoopShape — negative paths' {
    It 'rejects a cycle whose plan_path is missing' {
        # Arrange
        $cycle = New-ConformantCycle
        $cycle.PSObject.Properties.Remove('plan_path')
        $loop = [pscustomobject]@{ current_cycle = 1; cycles = @($cycle) }

        # Act
        $result = Test-RemediationLoopShape -RemediationLoop $loop

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "missing required field 'plan_path'"
    }

    It 'rejects a cycle where exit_condition_met is true and blocking_count is not 0' {
        # Arrange
        $cycle = New-ConformantCycle -BlockingCount 2 -ExitConditionMet $true
        $loop = [pscustomobject]@{ current_cycle = 1; cycles = @($cycle) }

        # Act
        $result = Test-RemediationLoopShape -RemediationLoop $loop

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "'exit_condition_met' is true"
        $result.Message | Should -Match "'blocking_count' is '2'"
    }

    It 'rejects a cycle where execution_status is in_progress and preflight.final_status is pending' {
        # Arrange
        $cycle = New-ConformantCycle -ExecutionStatus 'in_progress' -PreflightFinalStatus 'pending' `
            -BlockingCount 0 -ExitConditionMet $false
        $loop = [pscustomobject]@{ current_cycle = 1; cycles = @($cycle) }

        # Act
        $result = Test-RemediationLoopShape -RemediationLoop $loop

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "'execution_status' is 'in_progress'"
        $result.Message | Should -Match "'preflight.final_status' is 'pending'"
    }
}
