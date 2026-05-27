#Requires -Version 7.0
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.0.0' }

<#
.SYNOPSIS
    Pester v5 tests for .claude/hooks/enforce-pr-author-skill.ps1.

.DESCRIPTION
    Verifies the shape-only block cases (A, B, C) are preserved and the provenance
    block cases (D, E, G, F, H) are enforced. The hook is dot-sourced (its entrypoint
    guard returns early under dot-source) so its functions are available in the test
    scope. All filesystem and clock dependencies are exercised through the adapter
    seams (Get-PrContextArtifactExistence, Get-PrContextWriteTime,
    Test-PrBodyReceiptPresence, Get-PrBodyReceipt, Get-PrBodyFileHash) which are mocked,
    so no real disk access, temp files, or wall-clock waits occur.
#>

BeforeAll {
    $script:HookPath = Join-Path $PSScriptRoot '..\..\..\.claude\hooks\enforce-pr-author-skill.ps1'
    $script:HookPath = (Resolve-Path -LiteralPath $script:HookPath).Path

    # Dot-source the hook. Its entrypoint guard returns early under dot-source.
    . $script:HookPath

    # A reference UTC instant used to anchor freshness comparisons.
    $script:ContextWrite = [datetime]::new(2026, 5, 26, 12, 0, 0, [System.DateTimeKind]::Utc)
    $script:FreshCreatedAt = '2026-05-26T12:00:01Z'   # strictly newer than context write
    $script:StaleCreatedAt = '2026-05-26T11:59:59Z'   # older than context write
    $script:EqualCreatedAt = '2026-05-26T12:00:00Z'   # equal to context write (not strictly newer)
    $script:BodyHash = 'a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00'

    # Build a receipt object matching the schema the orchestrator writes.
    function script:New-Receipt {
        param(
            [int] $Number = 9,
            [string] $Sha256 = $script:BodyHash,
            [string] $CreatedAt = $script:FreshCreatedAt
        )
        return [pscustomobject]@{
            skill                = 'pr-author'
            pr_body_path         = "artifacts/pr_body_$Number.md"
            number               = $Number
            sha256               = $Sha256
            context_summary_path = 'artifacts/pr_context.summary.txt'
            created_at           = $CreatedAt
        }
    }
}

Describe 'Get-PrBodyFilePath (pure parser)' {
    It 'parses --body-file <value> (space separated)' {
        Get-PrBodyFilePath -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' |
            Should -Be 'artifacts/pr_body_9.md'
    }
    It 'parses --body-file=<value> (equals separated)' {
        Get-PrBodyFilePath -CommandText 'gh pr create --body-file=artifacts/pr_body_9.md' |
            Should -Be 'artifacts/pr_body_9.md'
    }
    It 'parses a double-quoted value' {
        Get-PrBodyFilePath -CommandText 'gh pr create --body-file "artifacts/pr_body_9.md"' |
            Should -Be 'artifacts/pr_body_9.md'
    }
    It 'parses a single-quoted value' {
        Get-PrBodyFilePath -CommandText "gh pr create --body-file 'artifacts/pr_body_9.md'" |
            Should -Be 'artifacts/pr_body_9.md'
    }
    It 'parses a double-quoted value after equals' {
        Get-PrBodyFilePath -CommandText 'gh pr create --body-file="artifacts/pr_body_9.md"' |
            Should -Be 'artifacts/pr_body_9.md'
    }
    It 'returns $null when no --body-file is present' {
        Get-PrBodyFilePath -CommandText 'gh pr create --title x' | Should -BeNullOrEmpty
    }
    It 'returns $null when --body-file has no following value' {
        Get-PrBodyFilePath -CommandText 'gh pr create --body-file' | Should -BeNullOrEmpty
    }
}

Describe 'I/O adapter seams (real committed files, no temp files)' {
    BeforeAll {
        # A small committed JSON file used to exercise the read/hash/existence seams.
        $script:CommittedJson = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\.mcp.json')).Path
    }

    It 'Get-PrContextArtifactExistence returns a boolean for the configured path' {
        # Point the configured context path at a committed file so the wrapper body runs.
        $original = $script:PrContextArtifactPath
        try {
            $script:PrContextArtifactPath = $script:CommittedJson
            Get-PrContextArtifactExistence | Should -BeTrue
        }
        finally {
            $script:PrContextArtifactPath = $original
        }
    }
    It 'Get-PrContextArtifactExistence returns $false for an absent path' {
        $original = $script:PrContextArtifactPath
        try {
            $script:PrContextArtifactPath = (Join-Path $script:CommittedJson 'does-not-exist.txt')
            Get-PrContextArtifactExistence | Should -BeFalse
        }
        finally {
            $script:PrContextArtifactPath = $original
        }
    }
    It 'Get-PrContextWriteTime returns a UTC datetime for the configured path' {
        $original = $script:PrContextArtifactPath
        try {
            $script:PrContextArtifactPath = $script:CommittedJson
            $writeTime = Get-PrContextWriteTime
            $writeTime | Should -BeOfType [datetime]
            $writeTime.Kind | Should -Be ([System.DateTimeKind]::Utc)
        }
        finally {
            $script:PrContextArtifactPath = $original
        }
    }
    It 'Test-PrBodyReceiptPresence returns $true for a present file' {
        Test-PrBodyReceiptPresence -Path $script:CommittedJson | Should -BeTrue
    }
    It 'Test-PrBodyReceiptPresence returns $false for an absent file' {
        Test-PrBodyReceiptPresence -Path (Join-Path $script:CommittedJson 'absent.json') | Should -BeFalse
    }
    It 'Get-PrBodyReceipt parses JSON from a committed file' {
        $parsed = Get-PrBodyReceipt -Path $script:CommittedJson
        $parsed | Should -Not -BeNullOrEmpty
    }
    It 'Get-PrBodyFileHash returns a lowercase hex SHA-256' {
        $hash = Get-PrBodyFileHash -Path $script:CommittedJson
        $hash | Should -Match '^[0-9a-f]{64}$'
    }
}

Describe 'Get-PrAuthorProvenanceReason (pure decision core)' {
    Context 'Case D - non-canonical path' {
        It 'blocks a /tmp path' {
            Get-PrAuthorProvenanceReason -BodyFilePath '/tmp/pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt) -BodyFileHash $script:BodyHash -ContextWriteTime $script:ContextWrite |
                Should -Match '^PR_BODY_PATH_NONCANONICAL'
        }
        It 'blocks artifacts/pr_body.md (no number)' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body.md' -ReceiptExists $true `
                -Receipt (New-Receipt) -BodyFileHash $script:BodyHash -ContextWriteTime $script:ContextWrite |
                Should -Match '^PR_BODY_PATH_NONCANONICAL'
        }
        It 'blocks an empty path' {
            Get-PrAuthorProvenanceReason -BodyFilePath '' -ReceiptExists $false `
                -Receipt $null -BodyFileHash $null -ContextWriteTime $null |
                Should -Match '^PR_BODY_PATH_NONCANONICAL'
        }
    }
    Context 'Case E - receipt missing' {
        It 'blocks when the sibling receipt does not exist' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $false `
                -Receipt $null -BodyFileHash $null -ContextWriteTime $null |
                Should -Match '^PR_AUTHOR_RECEIPT_MISSING'
        }
        It 'names the expected receipt path in the reason' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_42.md' -ReceiptExists $false `
                -Receipt $null -BodyFileHash $null -ContextWriteTime $null |
                Should -Match 'artifacts/pr_body_42\.receipt\.json'
        }
    }
    Context 'Case G - receipt number mismatch' {
        It 'blocks when receipt number differs from the filename number' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt -Number 8) -BodyFileHash $script:BodyHash -ContextWriteTime $script:ContextWrite |
                Should -Match '^PR_AUTHOR_RECEIPT_NUMBER_MISMATCH'
        }
    }
    Context 'Case F - hash mismatch' {
        It 'blocks when the body hash differs from the receipt sha256' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt) -BodyFileHash 'deadbeef' -ContextWriteTime $script:ContextWrite |
                Should -Match '^PR_AUTHOR_RECEIPT_HASH_MISMATCH'
        }
        It 'treats uppercase receipt sha256 as equal to lowercase body hash' {
            $receipt = New-Receipt -Sha256 $script:BodyHash.ToUpperInvariant()
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $true `
                -Receipt $receipt -BodyFileHash $script:BodyHash -ContextWriteTime $script:ContextWrite |
                Should -BeNullOrEmpty
        }
    }
    Context 'Case H - stale receipt' {
        It 'blocks when created_at is older than the context write time' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt -CreatedAt $script:StaleCreatedAt) -BodyFileHash $script:BodyHash `
                -ContextWriteTime $script:ContextWrite |
                Should -Match '^PR_AUTHOR_RECEIPT_STALE'
        }
        It 'blocks when created_at equals the context write time (not strictly newer)' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt -CreatedAt $script:EqualCreatedAt) -BodyFileHash $script:BodyHash `
                -ContextWriteTime $script:ContextWrite |
                Should -Match '^PR_AUTHOR_RECEIPT_STALE'
        }
    }
    Context 'all checks pass' {
        It 'returns $null for a canonical, present, matching, fresh receipt' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts/pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt) -BodyFileHash $script:BodyHash -ContextWriteTime $script:ContextWrite |
                Should -BeNullOrEmpty
        }
        It 'accepts a backslash-separated canonical path' {
            Get-PrAuthorProvenanceReason -BodyFilePath 'artifacts\pr_body_9.md' -ReceiptExists $true `
                -Receipt (New-Receipt) -BodyFileHash $script:BodyHash -ContextWriteTime $script:ContextWrite |
                Should -BeNullOrEmpty
        }
    }
}

Describe 'Get-PrAuthorBypassReason (orchestration over seams)' {
    Context 'Allowed commands' {
        It 'allows a non-gh-pr command' {
            Get-PrAuthorBypassReason -CommandText 'git status' -ContextExists $true | Should -BeNullOrEmpty
        }
        It 'allows gh pr edit --title with no body flags' {
            Get-PrAuthorBypassReason -CommandText 'gh pr edit 5 --title "New title"' -ContextExists $true |
                Should -BeNullOrEmpty
        }
        It 'allows a valid gh pr create with a present, matching, fresh receipt' {
            Mock Test-PrBodyReceiptPresence { $true }
            Mock Get-PrBodyReceipt { New-Receipt }
            Mock Get-PrBodyFileHash { $script:BodyHash }
            Mock Get-PrContextWriteTime { $script:ContextWrite }

            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' -ContextExists $true |
                Should -BeNullOrEmpty
        }
    }

    Context 'Shape-only block cases (preserved)' {
        It 'Case A - blocks inline --body on create' {
            Get-PrAuthorBypassReason -CommandText 'gh pr create --body "hi"' -ContextExists $true |
                Should -Match '^PR_AUTHOR_SKILL_BLOCKED'
        }
        It 'Case B - blocks create with no body flag' {
            Get-PrAuthorBypassReason -CommandText 'gh pr create --title x' -ContextExists $true |
                Should -Match '^PR_AUTHOR_SKILL_BLOCKED'
        }
        It 'Case C - blocks --body-file when context artifact is absent' {
            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' -ContextExists $false |
                Should -Match '^PR_CONTEXT_MISSING'
        }
    }

    Context 'Provenance block cases through seams' {
        It 'Case D - blocks a /tmp path' {
            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file /tmp/pr_body_9.md' -ContextExists $true |
                Should -Match '^PR_BODY_PATH_NONCANONICAL'
        }
        It 'Case D - blocks artifacts/pr_body.md (no number)' {
            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body.md' -ContextExists $true |
                Should -Match '^PR_BODY_PATH_NONCANONICAL'
        }
        It 'Case D - blocks a --body-file flag with no parseable value' {
            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file' -ContextExists $true |
                Should -Match '^PR_BODY_PATH_NONCANONICAL'
        }
        It 'Case E - blocks when the receipt is missing' {
            Mock Test-PrBodyReceiptPresence { $false }

            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' -ContextExists $true |
                Should -Match '^PR_AUTHOR_RECEIPT_MISSING'
            Should -Invoke Test-PrBodyReceiptPresence -Times 1 -ParameterFilter {
                $Path -eq 'artifacts/pr_body_9.receipt.json'
            }
        }
        It 'Case G - blocks on number mismatch' {
            Mock Test-PrBodyReceiptPresence { $true }
            Mock Get-PrBodyReceipt { New-Receipt -Number 8 }
            Mock Get-PrBodyFileHash { $script:BodyHash }
            Mock Get-PrContextWriteTime { $script:ContextWrite }

            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' -ContextExists $true |
                Should -Match '^PR_AUTHOR_RECEIPT_NUMBER_MISMATCH'
        }
        It 'Case F - blocks on hash mismatch' {
            Mock Test-PrBodyReceiptPresence { $true }
            Mock Get-PrBodyReceipt { New-Receipt }
            Mock Get-PrBodyFileHash { 'deadbeef' }
            Mock Get-PrContextWriteTime { $script:ContextWrite }

            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' -ContextExists $true |
                Should -Match '^PR_AUTHOR_RECEIPT_HASH_MISMATCH'
        }
        It 'Case H - blocks on a stale receipt' {
            Mock Test-PrBodyReceiptPresence { $true }
            Mock Get-PrBodyReceipt { New-Receipt -CreatedAt $script:StaleCreatedAt }
            Mock Get-PrBodyFileHash { $script:BodyHash }
            Mock Get-PrContextWriteTime { $script:ContextWrite }

            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file artifacts/pr_body_9.md' -ContextExists $true |
                Should -Match '^PR_AUTHOR_RECEIPT_STALE'
        }
        It 'allows gh pr edit --body-file with a valid receipt' {
            Mock Test-PrBodyReceiptPresence { $true }
            Mock Get-PrBodyReceipt { New-Receipt }
            Mock Get-PrBodyFileHash { $script:BodyHash }
            Mock Get-PrContextWriteTime { $script:ContextWrite }

            Get-PrAuthorBypassReason -CommandText 'gh pr edit 9 --body-file artifacts/pr_body_9.md' -ContextExists $true |
                Should -BeNullOrEmpty
        }
        It 'resolves a quoted --body-file path through the seams' {
            Mock Test-PrBodyReceiptPresence { $true }
            Mock Get-PrBodyReceipt { New-Receipt }
            Mock Get-PrBodyFileHash { $script:BodyHash }
            Mock Get-PrContextWriteTime { $script:ContextWrite }

            Get-PrAuthorBypassReason -CommandText 'gh pr create --body-file="artifacts/pr_body_9.md"' -ContextExists $true |
                Should -BeNullOrEmpty
        }
    }
}

Describe 'Invoke-PrAuthorSkillDecision (entrypoint logic)' {
    It 'allows when tool input is empty' {
        (Invoke-PrAuthorSkillDecision -ToolInputRaw '').decision | Should -Be 'allow'
    }
    It 'allows when command text is missing from the payload' {
        $json = '{"tool":"Bash"}'
        (Invoke-PrAuthorSkillDecision -ToolInputRaw $json).decision | Should -Be 'allow'
    }
    It 'throws on malformed JSON' {
        { Invoke-PrAuthorSkillDecision -ToolInputRaw '{not json' } |
            Should -Throw '*malformed JSON*'
    }
    It 'returns a block decision with a reason for Case B' {
        $json = '{"command":"gh pr create --title x"}'
        Mock Get-PrContextArtifactExistence { $true }

        $decision = Invoke-PrAuthorSkillDecision -ToolInputRaw $json
        $decision.decision | Should -Be 'block'
        $decision.reason | Should -Match '^PR_AUTHOR_SKILL_BLOCKED'
    }
    It 'returns a block decision for a non-canonical body-file path' {
        $json = '{"command":"gh pr create --body-file /tmp/pr_body_9.md"}'
        Mock Get-PrContextArtifactExistence { $true }

        $decision = Invoke-PrAuthorSkillDecision -ToolInputRaw $json
        $decision.decision | Should -Be 'block'
        $decision.reason | Should -Match '^PR_BODY_PATH_NONCANONICAL'
    }
    It 'returns an allow decision for a valid canonical body-file path' {
        $json = '{"command":"gh pr create --body-file artifacts/pr_body_9.md"}'
        Mock Get-PrContextArtifactExistence { $true }
        Mock Test-PrBodyReceiptPresence { $true }
        Mock Get-PrBodyReceipt { New-Receipt }
        Mock Get-PrBodyFileHash { $script:BodyHash }
        Mock Get-PrContextWriteTime { $script:ContextWrite }

        (Invoke-PrAuthorSkillDecision -ToolInputRaw $json).decision | Should -Be 'allow'
    }
}

Describe 'Test-PrAuthorBypassRequired' {
    It 'returns $false for an allowed command' {
        Test-PrAuthorBypassRequired -CommandText 'git status' -ContextExists $true | Should -BeFalse
    }
    It 'returns $true for a blocked command' {
        Test-PrAuthorBypassRequired -CommandText 'gh pr create --title x' -ContextExists $true | Should -BeTrue
    }
}

Describe 'Entrypoint contract (child process)' {
    # The script entrypoint calls exit and is guarded against dot-source, so it cannot
    # be exercised in-process. These tests run the hook as a child pwsh process to verify
    # the JSON stdout contract and exit codes. They are deterministic and use no network,
    # no temp files, and no real gh/git executables.
    BeforeAll {
        $script:RunHook = {
            param([string] $ToolInput)
            $envBlock = if ($null -eq $ToolInput) { '$env:CLAUDE_TOOL_INPUT = $null' } else { "`$env:CLAUDE_TOOL_INPUT = @'`n$ToolInput`n'@" }
            $script = "$envBlock; & '$($script:HookPath)'"
            $stdout = pwsh -NoProfile -Command $script
            return [pscustomobject]@{ Stdout = ($stdout -join "`n"); ExitCode = $LASTEXITCODE }
        }
    }

    It 'emits {"decision":"allow"} and exit 0 when tool input is empty' {
        $result = & $script:RunHook -ToolInput $null
        $result.ExitCode | Should -Be 0
        $result.Stdout | Should -Match '"decision":"allow"'
    }
    It 'emits a block decision and exit 0 for a Case B command' {
        $result = & $script:RunHook -ToolInput '{"command":"gh pr create --title x"}'
        $result.ExitCode | Should -Be 0
        $result.Stdout | Should -Match '"decision":"block"'
        $result.Stdout | Should -Match 'PR_AUTHOR_SKILL_BLOCKED'
    }
    It 'exits 1 on malformed JSON' {
        $result = & $script:RunHook -ToolInput '{not json'
        $result.ExitCode | Should -Be 1
    }
}
