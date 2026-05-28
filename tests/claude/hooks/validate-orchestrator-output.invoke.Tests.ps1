#Requires -Version 7.0
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }

<#
.SYNOPSIS
    Pester v5 tests for Invoke-OrchestratorOutputValidation in
    .claude/hooks/validate-orchestrator-output.ps1 (issue #25 cycle 1, AC#9).

.DESCRIPTION
    Dot-sources the hook (its entrypoint guard returns early under dot-source)
    and exercises Invoke-OrchestratorOutputValidation across the 13 payload
    and checkpoint scenarios enumerated in
    docs/features/active/remediation-loop-protocol-25/remediation-inputs.2026-05-28T17-31.md.
    Filesystem reads via Get-CheckpointFileContent are mocked so no temp files
    or real checkpoint files are required. The sibling cycle-0 fixture file
    validate-orchestrator-output.remediation-loop.Tests.ps1 continues to cover
    Test-RemediationLoopShape directly; this file covers the entrypoint.
#>

BeforeAll {
    $script:HookPath = Join-Path $PSScriptRoot '..\..\..\.claude\hooks\validate-orchestrator-output.ps1'
    $script:HookPath = (Resolve-Path -LiteralPath $script:HookPath).Path
    . $script:HookPath

    function script:New-ConformantCheckpointJson {
        <#
        .SYNOPSIS
            Returns a JSON string for a minimal valid orchestrator-state checkpoint.
        .DESCRIPTION
            Keys produced: objective, completed_steps, next_step, last_updated,
            and optionally remediation_loop. The remediation_loop block (when
            included) carries a single cycle whose fields can be overridden via
            parameters so tests can synthesize each rejection scenario without
            building objects by hand.
        #>
        param(
            [string] $Objective = 'Bug remediation for issue 25',
            [switch] $IncludeRemediationLoop,
            [bool] $OmitPlanPath = $false,
            [string] $PlanPath = 'docs/features/active/example-feature-99/remediation-plan.2026-06-01T09-15.md',
            [string] $ExecutionStatus = 'complete',
            [int] $BlockingCount = 0,
            [bool] $ExitConditionMet = $true,
            [string] $PreflightFinalStatus = 'clear'
        )

        $cycleParts = @()
        $cycleParts += '"entry_timestamp":"2026-06-01T09-15"'
        $cycleParts += '"inputs_path":"docs/features/active/example-feature-99/remediation-inputs.2026-06-01T09-15.md"'
        if (-not $OmitPlanPath) {
            $cycleParts += ('"plan_path":"' + $PlanPath + '"')
        }
        $cycleParts += ('"preflight":{"iterations":2,"final_status":"' + $PreflightFinalStatus + '"}')
        $cycleParts += ('"execution_status":"' + $ExecutionStatus + '"')
        $cycleParts += '"audit_paths":{"code_review":"a.md","feature_audit":"b.md","policy_audit":"c.md"}'
        $cycleParts += ('"blocking_count":' + $BlockingCount)
        $cycleParts += ('"exit_condition_met":' + ($(if ($ExitConditionMet) { 'true' } else { 'false' })))
        $cycle = '{' + ($cycleParts -join ',') + '}'

        $parts = @()
        $parts += ('"objective":"' + $Objective + '"')
        $parts += '"completed_steps":["s1"]'
        $parts += '"next_step":"s2"'
        $parts += '"last_updated":"2026-05-28T17-31"'
        if ($IncludeRemediationLoop) {
            $parts += ('"remediation_loop":{"current_cycle":1,"cycles":[' + $cycle + ']}')
        }

        return '{' + ($parts -join ',') + '}'
    }
}

Describe 'Invoke-OrchestratorOutputValidation — payload rejection paths' {
    It 'returns Ok=false when CLAUDE_HOOK_INPUT is empty' {
        # Arrange
        $payload = ''

        # Act
        $result = Invoke-OrchestratorOutputValidation -RawPayload $payload

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'CLAUDE_HOOK_INPUT is empty'
    }

    It 'returns Ok=false when payload is not JSON' {
        # Arrange
        $payload = 'not-json{'

        # Act
        $result = Invoke-OrchestratorOutputValidation -RawPayload $payload

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'failed to parse'
    }

    It 'returns Ok=false when payload output field is empty' {
        # Arrange
        $payload = '{ "output": "" }'

        # Act
        $result = Invoke-OrchestratorOutputValidation -RawPayload $payload

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'agent output is empty'
    }
}

Describe 'Invoke-OrchestratorOutputValidation — checkpoint rejection paths' {
    It 'returns Ok=false when the checkpoint file does not exist' {
        # Arrange
        Mock Get-CheckpointFileContent { return @{ Exists = $false; Content = $null } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'does not exist'
    }

    It 'returns Ok=false when the checkpoint file is empty' {
        # Arrange
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = '' } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'is empty'
    }

    It 'returns Ok=false when the checkpoint content is not valid JSON' {
        # Arrange
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = 'not-json{' } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'is not valid JSON'
    }

    It 'returns Ok=false when checkpoint is missing required fields' {
        # Arrange
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = '{ "objective": "x" }' } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match 'missing required field\(s\)'
    }

    It 'returns Ok=false when checkpoint objective is empty' {
        # Arrange
        $json = New-ConformantCheckpointJson -Objective ''
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = $json } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "empty 'objective' field"
    }
}

Describe 'Invoke-OrchestratorOutputValidation — checkpoint acceptance paths' {
    It 'returns Ok=true when checkpoint has no remediation_loop field' {
        # Arrange
        $json = New-ConformantCheckpointJson
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = $json } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeTrue
        $result.Message | Should -BeNullOrEmpty
    }

    It 'returns Ok=true when checkpoint has a conformant remediation_loop' {
        # Arrange
        $json = New-ConformantCheckpointJson -IncludeRemediationLoop
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = $json } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeTrue
        $result.Message | Should -BeNullOrEmpty
    }
}

Describe 'Invoke-OrchestratorOutputValidation — remediation_loop rejection paths' {
    It 'returns Ok=false when a cycle is missing plan_path' {
        # Arrange
        $json = New-ConformantCheckpointJson -IncludeRemediationLoop -OmitPlanPath $true
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = $json } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "missing required field 'plan_path'"
    }

    It 'returns Ok=false when a cycle has exit_condition_met true and blocking_count 2' {
        # Arrange
        $json = New-ConformantCheckpointJson -IncludeRemediationLoop `
            -ExitConditionMet $true -BlockingCount 2
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = $json } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "'exit_condition_met' is true"
        $result.Message | Should -Match "'blocking_count' is '2'"
    }

    It 'returns Ok=false when execution_status in_progress and preflight pending' {
        # Arrange
        $json = New-ConformantCheckpointJson -IncludeRemediationLoop `
            -ExecutionStatus 'in_progress' -PreflightFinalStatus 'pending' `
            -BlockingCount 0 -ExitConditionMet $false
        Mock Get-CheckpointFileContent { return @{ Exists = $true; Content = $json } }

        # Act
        $result = Invoke-OrchestratorOutputValidation `
            -RawPayload '{ "output": "summary" }' `
            -CheckpointPath 'artifacts/orchestration/orchestrator-state.json'

        # Assert
        $result.Ok | Should -BeFalse
        $result.Message | Should -Match "'execution_status' is 'in_progress'"
        $result.Message | Should -Match "'preflight.final_status' is 'pending'"
    }
}
