# Dev Container

This directory contains the Dev Container configuration for the **mix-calculator**
project. There are two configurations that share one image:

| Path | Used by |
|------|---------|
| `.devcontainer/local/devcontainer.json` | Local Docker (VS Code Dev Containers) |
| `.devcontainer/codespaces/devcontainer.json` | GitHub Codespaces |
| `.devcontainer/Dockerfile` | Shared image, referenced by both |
| `.devcontainer/post-create.sh` | Shared post-create setup, run by both |
| `.devcontainer/verify-container.sh` | Environment verification script |

Because there is no `.devcontainer/devcontainer.json` at the top level, VS Code and
Codespaces present a picker so you explicitly choose the local or Codespaces config.

## Quick start

### Local Docker

1. Ensure Docker Desktop is running.
2. Open this folder in VS Code with the
   [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
3. `F1` → **Dev Containers: Reopen in Container** (or **Open Folder in Container**).
4. When prompted, choose **`.devcontainer/local/devcontainer.json`**.
5. Wait for the first build, then verify: `bash .devcontainer/verify-container.sh`.

### GitHub Codespaces

1. On GitHub: **Code** → **Codespaces** → **...** → **Configure and create codespace**.
2. Choose dev container **`.devcontainer/codespaces/devcontainer.json`**.
3. Create the codespace and wait for the build.
4. Verify: `bash .devcontainer/verify-container.sh`.

## What's included

- **Debian 12 (Bookworm)** base image.
- **Python 3.12** with **Poetry** (in-project `.venv`).
- **PowerShell 7** with **PSScriptAnalyzer** and **Pester** — used by
  `scripts/dev-tools/*.ps1` and the `.claude/hooks/*.ps1` hooks.
- **Node (LTS)** — required to launch the `drm-copilot` MCP server via `npx`
  (see `.mcp.json`).
- **build-essential** and **patchelf** — the C toolchain Nuitka needs for builds.
- **Qt6 runtime libraries** and **Xvfb** — so the PySide6 GUI can run and be
  tested without a physical display.
- **git** and **GitHub CLI** (`gh`).

The container defaults to the PowerShell shell. Bash is available from the
terminal profile dropdown.

## Running the PySide6 GUI

The image sets `QT_QPA_PLATFORM=offscreen`, so PySide6 imports and GUI tests run
headlessly out of the box. To run the GUI against a virtual X display instead
(for example to capture a window), use Xvfb:

```bash
QT_QPA_PLATFORM=xcb xvfb-run -a poetry run python -m src
```

## Common commands

```bash
poetry run black .            # Format
poetry run ruff check         # Lint
poetry run pyright            # Type-check
poetry run pytest             # Test
```

PowerShell scripts (for example the dev-environment bootstrap) run with:

```bash
pwsh -NoLogo -File scripts/dev-tools/Initialize-DevEnvironment.ps1 -DryRun
```

## Rebuilding

After changing the Dockerfile, a `devcontainer.json`, or `post-create.sh`:

- Local: `F1` → **Dev Containers: Rebuild Container** (add **Without Cache** for a
  clean rebuild).
- Codespaces: command palette → **Codespaces: Rebuild Container**.

## Troubleshooting

- **Build fails / out of resources (local):** confirm Docker Desktop is running
  with at least 4 GB RAM, then rebuild without cache.
- **`poetry install` fails:** confirm `poetry.lock` is committed, then rerun
  `poetry install` inside the container.
- **PySide6 import fails:** rebuild the container so the Qt system libraries from
  the Dockerfile are present; `verify-container.sh` reports this check.
- **PowerShell modules missing:** they are installed for all users in the image;
  rebuild the container if a rebuild changed the base layers.

## References

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container specification](https://containers.dev/)
