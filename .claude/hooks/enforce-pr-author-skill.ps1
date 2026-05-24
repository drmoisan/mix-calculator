<#
.SYNOPSIS
    Pre-tool-use hook that enforces the pr-author skill is used before gh pr create or gh pr edit.

.DESCRIPTION
    Invoked by the Claude Code PreToolUse hook before any Bash command runs. Reads
    tool input JSON from the CLAUDE_TOOL_INPUT environment variable, inspects the
    attempted command, and blocks gh pr create / gh pr edit commands that bypass the
    pr-author skill workflow.

    Required sequence:
      1. mcp__drm-copilot__collect_pr_context writes artifacts/pr_context.summary.txt
      2. pr-author skill reads that file and writes artifacts/pr_body_<N>.md
      3. gh pr create --body-file artifacts/pr_body_<N>.md
         (or gh pr edit --body-file ...)

    Three block cases:
      Case A - gh pr create with --body (inline, no --body-file): blocked.
      Case B - gh pr create with neither --body nor --body-file: blocked.
      Case C - gh pr create or gh pr edit with --body-file but context artifact absent: blocked.

.NOTES
    Compatible with PowerShell 7+. No external module dependencies.
#>
[CmdletBinding()]
param()

$script:PrContextArtifactPath = 'artifacts/pr_context.summary.txt'

function Get-PrContextArtifactExistence {
    <#
    .SYNOPSIS
        Wrapper around Test-Path for the PR context artifact. Tests mock this function.
    .OUTPUTS
        System.Boolean
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param()

    return [bool](Test-Path -LiteralPath $script:PrContextArtifactPath)
}

function Get-PrAuthorBypassReason {
    <#
    .SYNOPSIS
        Inspect the command text and return a block reason string, or $null when the command is allowed.
    .DESCRIPTION
        Returns PR_AUTHOR_SKILL_BLOCKED when gh pr create is run with --body (inline) or with no body
        flag at all. Returns PR_CONTEXT_MISSING when --body-file is present but the context artifact
        does not exist on disk. Returns $null for all allowed patterns.
    .PARAMETER CommandText
        The Bash command text extracted from CLAUDE_TOOL_INPUT.
    .PARAMETER ContextExists
        Whether artifacts/pr_context.summary.txt currently exists on disk.
    .OUTPUTS
        System.String or $null
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory)]
        [string] $CommandText,

        [Parameter(Mandatory)]
        [bool] $ContextExists
    )

    # Only act on gh pr create or gh pr edit subcommands.
    $isPrCreate = $CommandText -match '(?i)\bgh\s+pr\s+create\b'
    $isPrEdit = $CommandText -match '(?i)\bgh\s+pr\s+edit\b'

    if (-not $isPrCreate -and -not $isPrEdit) {
        return $null
    }

    $hasBodyFile = $CommandText -match '(?i)--body-file\b'
    $hasInlineBody = $CommandText -match '(?i)--body(?!-file)\b'

    if ($isPrCreate) {
        # Case A: gh pr create with inline --body (not --body-file).
        if ($hasInlineBody -and -not $hasBodyFile) {
            return "PR_AUTHOR_SKILL_BLOCKED: ``gh pr create`` must use ``--body-file`` with a file produced by the pr-author skill from ``$script:PrContextArtifactPath``. Run ``mcp__drm-copilot__collect_pr_context`` to generate the context file, apply the pr-author skill to produce ``artifacts/pr_body_<N>.md``, then pass that file via ``--body-file``."
        }

        # Case B: gh pr create with no body flag at all.
        if (-not $hasInlineBody -and -not $hasBodyFile) {
            return "PR_AUTHOR_SKILL_BLOCKED: New PRs require ``--body-file``. Run ``mcp__drm-copilot__collect_pr_context`` to generate ``$script:PrContextArtifactPath``, apply the pr-author skill to produce ``artifacts/pr_body_<N>.md``, then pass that file via ``--body-file``."
        }
    }

    if ($isPrEdit) {
        # gh pr edit with no --body or --body-file (e.g., --title, --add-label, --reviewer) is allowed.
        if (-not $hasInlineBody -and -not $hasBodyFile) {
            return $null
        }
    }

    # Case C: --body-file present but context artifact is absent.
    if ($hasBodyFile -and -not $ContextExists) {
        return "PR_CONTEXT_MISSING: ``$script:PrContextArtifactPath`` is absent. Run ``mcp__drm-copilot__collect_pr_context`` before creating or editing the PR body."
    }

    return $null
}

function Invoke-PrAuthorSkillDecision {
    <#
    .SYNOPSIS
        Parse CLAUDE_TOOL_INPUT and return an allow-or-block decision.
    .PARAMETER ToolInputRaw
        The raw JSON tool payload supplied by Claude Code.
    .OUTPUTS
        System.Collections.Specialized.OrderedDictionary
    .NOTES
        Missing tool input or missing command text is treated as allow.
    #>
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param(
        [string] $ToolInputRaw
    )

    if (-not $ToolInputRaw) {
        return [ordered]@{ decision = 'allow' }
    }

    try {
        $toolInput = $ToolInputRaw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        throw "enforce-pr-author-skill hook received malformed JSON in CLAUDE_TOOL_INPUT: $_"
    }

    $commandText = $toolInput.command
    if (-not $commandText) {
        return [ordered]@{ decision = 'allow' }
    }

    $contextExists = Get-PrContextArtifactExistence
    $reason = Get-PrAuthorBypassReason -CommandText $commandText -ContextExists $contextExists

    if ($reason) {
        return [ordered]@{
            decision = 'block'
            reason   = $reason
        }
    }

    return [ordered]@{ decision = 'allow' }
}

function Test-PrAuthorBypassRequired {
    <#
    .SYNOPSIS
        Return $true when a Bash command requires the pr-author skill to run first.
    .PARAMETER CommandText
        The Bash command text extracted from CLAUDE_TOOL_INPUT.
    .PARAMETER ContextExists
        Whether artifacts/pr_context.summary.txt currently exists on disk.
    .OUTPUTS
        System.Boolean
    #>
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)]
        [string] $CommandText,

        [Parameter(Mandatory)]
        [bool] $ContextExists
    )

    return ($null -ne (Get-PrAuthorBypassReason -CommandText $CommandText -ContextExists $ContextExists))
}

# Allow dot-sourcing in tests without executing the entrypoint.
if ($MyInvocation.InvocationName -eq '.') {
    return
}

try {
    $decision = Invoke-PrAuthorSkillDecision -ToolInputRaw $env:CLAUDE_TOOL_INPUT
} catch {
    Write-Error $_
    exit 1
}

$decision | ConvertTo-Json -Compress | Write-Output

exit 0
