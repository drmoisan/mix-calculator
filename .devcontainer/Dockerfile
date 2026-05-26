# Dev container image for the mix-calculator project.
#
# Shared by both the local (.devcontainer/local) and Codespaces
# (.devcontainer/codespaces) configurations. The image provides the full
# project toolchain: Python 3.12 + Poetry, PowerShell 7 + Pester/PSScriptAnalyzer
# (used by scripts/dev-tools and the .claude hooks), Node (for the drm-copilot
# MCP server launched via npx), a C toolchain for Nuitka builds, and the Qt
# runtime libraries plus Xvfb needed to run and test the PySide6 GUI headlessly.

# Match the project floor (pyproject requires Python >=3.12,<4.0) and the host
# bootstrap in scripts/dev-tools/Initialize-DevEnvironment.ps1, which targets 3.12.
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# Remove the Yarn apt repository inherited from the base image (its GPG key is
# expired and this project does not use Yarn); leaving it breaks `apt-get update`.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# System packages:
#   - build-essential / patchelf: C toolchain required by Nuitka on Linux.
#   - Qt6 runtime + xcb libraries: required by PySide6 (the wheels bundle Qt but
#     depend on these system libraries to load the platform plugins).
#   - xvfb / x11-utils: provide a virtual X server so the GUI can run and be
#     tested without a physical display.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    wget \
    apt-transport-https \
    build-essential \
    patchelf \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    libdbus-1-3 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libx11-xcb1 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb1 \
    libxcb-cursor0 \
    libxcb-glx0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-util1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    x11-utils \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install PowerShell 7 from the Microsoft package repository. PowerShell is
# required for scripts/dev-tools/*.ps1 and the .claude/hooks/*.ps1 hooks.
RUN wget -q https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y powershell \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry. Pinned for repeatable builds; the project uses an in-project venv.
RUN pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.in-project true

# Install the PowerShell QC modules for all users so they are available to every
# shell without a per-user install. Pester is pinned to the 5.x line per
# .claude/rules/powershell.md.
RUN pwsh -NoLogo -NoProfile -Command " \
    Set-PSRepository -Name PSGallery -InstallationPolicy Trusted; \
    Install-Module -Name PSScriptAnalyzer -Scope AllUsers -Force; \
    Install-Module -Name Pester -MinimumVersion 5.0.0 -Scope AllUsers -Force; \
    "

# Default the interactive shell to PowerShell for convenience.
ENV SHELL=/usr/bin/pwsh

# Project files are mounted at runtime; dependencies are installed by
# post-create.sh via `poetry install`.
