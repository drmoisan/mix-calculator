#!/bin/bash
# Post-create setup for the mix-calculator dev container.
#
# Runs once after the container is created (both local and Codespaces). It
# provisions the in-project Poetry virtual environment, writes a PowerShell
# profile that activates the venv, and verifies the Python and PowerShell
# toolchains. It is idempotent and safe to re-run.
set -euo pipefail

echo "==================================="
echo "Post-Create Container Setup"
echo "==================================="

# -----------------------------------------------------------------------------
# Resolve the workspace/repo root deterministically.
# -----------------------------------------------------------------------------
# Prefer the devcontainer-provided workspace folder; fall back to the git
# top-level; finally fall back to the current directory.
WORKSPACE_DIR="${WORKSPACE_FOLDER:-}"
if [ -n "$WORKSPACE_DIR" ] && [ -d "$WORKSPACE_DIR" ]; then
  if git -C "$WORKSPACE_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
    WORKSPACE_DIR="$(git -C "$WORKSPACE_DIR" rev-parse --show-toplevel)"
  fi
else
  WORKSPACE_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

cd "$WORKSPACE_DIR"
export WORKSPACE_DIR
echo "Workspace directory: $WORKSPACE_DIR"

# -----------------------------------------------------------------------------
# PowerShell profile: activate the venv and show a relative-path prompt.
# -----------------------------------------------------------------------------
# The profile is written with the resolved workspace path baked in so that
# pwsh sessions activate the correct in-project venv regardless of the
# container's workspace folder name.
echo ""
echo "Creating PowerShell profile..."
mkdir -p ~/.config/powershell
cat > ~/.config/powershell/Microsoft.PowerShell_profile.ps1 << PROFILE_END
\$env:WORKSPACE_DIR = '$WORKSPACE_DIR'

# Activate the in-project venv silently when present.
\$activateScript = "\$env:WORKSPACE_DIR/.venv/bin/Activate.ps1"
if (Test-Path \$activateScript) {
    \$null = & \$activateScript *>&1
}

# Prompt that shows the active venv and a workspace-relative path.
function prompt {
    \$venvName = if (\$env:VIRTUAL_ENV) { Split-Path -Leaf \$env:VIRTUAL_ENV } else { '' }
    \$venv = if (\$venvName) { "(\$venvName)" } else { "" }
    \$currentPath = \$PWD.Path
    \$workspaceDir = \$env:WORKSPACE_DIR

    if (\$currentPath -eq \$workspaceDir) {
        \$relativePath = "/"
    } elseif (\$currentPath.StartsWith(\$workspaceDir)) {
        \$relativePath = \$currentPath.Substring(\$workspaceDir.Length)
    } else {
        \$relativePath = \$currentPath
    }

    "\$venv\$relativePath> "
}
PROFILE_END

# Persist WORKSPACE_DIR for future bash sessions.
BASHRC="$HOME/.bashrc"
LINE="export WORKSPACE_DIR=\"$WORKSPACE_DIR\""
grep -qxF "$LINE" "$BASHRC" 2>/dev/null || echo "$LINE" >> "$BASHRC"

# -----------------------------------------------------------------------------
# Python / Poetry setup.
# -----------------------------------------------------------------------------
echo ""
echo "Installing Python dependencies with Poetry..."

# Ensure Poetry uses an in-project venv for this repo (local config, not global).
poetry config virtualenvs.in-project true --local

# Recreate the venv if it exists but is clearly broken.
if [ -d ".venv" ] && [ ! -x ".venv/bin/python" ]; then
  echo "Detected broken .venv; removing and recreating..."
  rm -rf .venv
fi

if [ -f "poetry.lock" ]; then
  echo "poetry.lock found; installing locked dependencies..."
  poetry install --no-interaction --no-ansi --with dev
else
  echo "Warning: poetry.lock not found. Resolving dependencies and creating lock file..."
  poetry lock --no-interaction --no-ansi
  poetry install --no-interaction --no-ansi --with dev
fi

# Verify the Python toolchain.
echo ""
echo "Verifying Python tooling..."
poetry run black --version
poetry run ruff --version
poetry run pyright --version
poetry run pytest --version

# -----------------------------------------------------------------------------
# Claude Code tooling (MCP server + CLI).
# -----------------------------------------------------------------------------
# The drm-copilot MCP server is declared in .mcp.json (npx @danmoisan/drm-copilot-mcp)
# and the mcp__drm-copilot__* tools are granted in .claude/settings.json. Pre-install
# it globally so it is available offline and npx does not download it on first use.
# The Claude Code CLI is the client that launches the MCP server, so it is installed
# alongside it.
echo ""
echo "Installing Claude Code tooling (MCP server + CLI)..."
if command -v npm >/dev/null 2>&1; then
  npm install -g @danmoisan/drm-copilot-mcp @anthropic-ai/claude-code
  echo "Installed global npm packages:"
  npm ls -g --depth=0 @danmoisan/drm-copilot-mcp @anthropic-ai/claude-code || true
else
  echo "Warning: npm not found; cannot pre-install the drm-copilot MCP server or Claude Code CLI."
  echo "  The node devcontainer feature should provide npm; rebuild the container if it is missing."
fi

# -----------------------------------------------------------------------------
# PowerShell tooling verification.
# -----------------------------------------------------------------------------
echo ""
echo "Verifying PowerShell tooling..."
pwsh -NoLogo -NoProfile -Command "
    Write-Host 'PowerShell version:'
    \$PSVersionTable.PSVersion
    Write-Host ''
    Write-Host 'Installed modules:'
    Get-Module -ListAvailable PSScriptAnalyzer, Pester | Sort-Object Name, Version -Descending | Format-Table Name, Version
"

# -----------------------------------------------------------------------------
# Git configuration reminder.
# -----------------------------------------------------------------------------
if [ ! -f ~/.gitconfig ]; then
  echo ""
  echo "Git configuration not found. You may want to run:"
  echo "  git config --global user.name 'Your Name'"
  echo "  git config --global user.email 'your.email@example.com'"
fi

# -----------------------------------------------------------------------------
# Completion banner.
# -----------------------------------------------------------------------------
echo ""
echo "==================================="
echo "Dev Container Setup Complete!"
echo "==================================="
echo ""
echo "Common commands:"
echo "  poetry run pytest                         # Run tests"
echo "  poetry run black .                        # Format Python code"
echo "  poetry run ruff check                     # Lint Python code"
echo "  poetry run pyright                        # Type-check Python code"
echo ""
echo "The PySide6 GUI runs headlessly by default (QT_QPA_PLATFORM=offscreen)."
echo "To run the GUI against a virtual display instead, use:"
echo "  QT_QPA_PLATFORM=xcb xvfb-run -a poetry run python -m src"
echo ""
echo "Verify the environment with:"
echo "  bash .devcontainer/verify-container.sh"
echo ""
