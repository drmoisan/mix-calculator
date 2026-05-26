#!/bin/bash
# verify-container.sh - Verify the mix-calculator dev container environment.
#
# Reports the detected OS, language runtimes, project tooling, the Qt/Xvfb
# support needed by the PySide6 GUI, and the in-project virtual environment.
# Exits non-zero if any expected component is missing.
set -uo pipefail

echo "========================================="
echo "Dev Container Environment Verification"
echo "========================================="
echo ""

# Resolve the workspace root deterministically (do not assume a fixed path).
WORKSPACE_DIR="${WORKSPACE_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Detect environment.
if [ "${CODESPACES:-}" = "true" ]; then
    echo "Environment: GitHub Codespaces"
    ENV_TYPE="codespaces"
else
    echo "Environment: Local Docker"
    ENV_TYPE="local"
fi
echo "Workspace: $WORKSPACE_DIR"
echo ""

# OS check.
echo "Operating System:"
if [ -f /etc/os-release ]; then
    # shellcheck source=/dev/null
    . /etc/os-release
    echo "   Name: $PRETTY_NAME"
    if [ "$ID" = "debian" ] && [ "$VERSION_ID" = "12" ]; then
        echo "   OK: Debian 12 Bookworm (expected)"
        OS_OK=true
    else
        echo "   WARN: Unexpected OS (expected Debian 12 Bookworm)"
        OS_OK=false
    fi
else
    echo "   FAIL: Cannot detect OS"
    OS_OK=false
fi
echo ""

# Python check.
echo "Python:"
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    echo "   Version: $PYTHON_VERSION"
    if [[ "$PYTHON_VERSION" == 3.12.* ]]; then
        echo "   OK: Python 3.12 (expected)"
        PYTHON_OK=true
    else
        echo "   WARN: Unexpected version (expected 3.12.x)"
        PYTHON_OK=false
    fi
else
    echo "   FAIL: Python not found"
    PYTHON_OK=false
fi
echo ""

# Poetry check.
echo "Poetry:"
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version 2>&1 | awk '{print $3}' | tr -d ')')
    echo "   Version: $POETRY_VERSION"
    POETRY_OK=true
else
    echo "   FAIL: Poetry not found"
    POETRY_OK=false
fi
echo ""

# PowerShell check.
echo "PowerShell:"
if command -v pwsh &> /dev/null; then
    echo "   $(pwsh --version 2>&1 | head -n1)"
    PWSH_OK=true
else
    echo "   FAIL: PowerShell not found"
    PWSH_OK=false
fi
echo ""

# Tooling check.
echo "Tools:"
TOOLS=("git" "gh" "node" "xvfb-run")
TOOLS_OK=true
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "   OK: $tool ($($tool --version 2>&1 | head -n1 || echo installed))"
    else
        echo "   FAIL: $tool not found"
        TOOLS_OK=false
    fi
done
echo ""

# Configuration files check.
echo "Configuration Files:"
[ -f "$WORKSPACE_DIR/.devcontainer/local/devcontainer.json" ] \
    && echo "   OK: .devcontainer/local/devcontainer.json (Local config)"
[ -f "$WORKSPACE_DIR/.devcontainer/codespaces/devcontainer.json" ] \
    && echo "   OK: .devcontainer/codespaces/devcontainer.json (Codespaces config)"
[ -f "$WORKSPACE_DIR/.devcontainer/Dockerfile" ] \
    && echo "   OK: .devcontainer/Dockerfile (shared image)"
echo ""

# Virtual environment + PySide6 import check.
echo "Python Virtual Environment:"
if [ -x "$WORKSPACE_DIR/.venv/bin/python" ]; then
    echo "   OK: $("$WORKSPACE_DIR/.venv/bin/python" --version)"
    # Confirm PySide6 imports headlessly with the Qt system libraries present.
    if QT_QPA_PLATFORM=offscreen "$WORKSPACE_DIR/.venv/bin/python" -c "import PySide6" 2>/dev/null; then
        echo "   OK: PySide6 imports (headless Qt libraries present)"
        VENV_OK=true
    else
        echo "   WARN: PySide6 import failed (Qt libraries or dependency missing)"
        VENV_OK=false
    fi
else
    echo "   WARN: .venv not found (run: poetry install)"
    VENV_OK=false
fi
echo ""

# Summary.
echo "========================================="
echo "Summary"
echo "========================================="
if [ "${OS_OK:-false}" = true ] && [ "${PYTHON_OK:-false}" = true ] \
   && [ "${POETRY_OK:-false}" = true ] && [ "${PWSH_OK:-false}" = true ] \
   && [ "${TOOLS_OK:-false}" = true ] && [ "${VENV_OK:-false}" = true ]; then
    echo "All checks passed. Using the $ENV_TYPE configuration."
    exit 0
else
    echo "Some checks did not pass. Review the warnings above."
    echo "To rebuild: F1 -> Dev Containers: Rebuild Container."
    echo "See .devcontainer/README.md for help."
    exit 1
fi
