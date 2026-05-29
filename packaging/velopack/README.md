# Velopack Packaging Assets

This directory holds the build-time inputs and documentation for the
Velopack installer wrapper around the Mix Calculator GUI. The build
orchestrator is `src/build_velopack.py` and the corresponding Poetry
script entry is `build-velopack`.

References:
- Spec: `docs/features/active/2026-05-29-velopack-installer-31/spec.md`
- Research artifact: `artifacts/research/2026-05-29-velopack-installer-landscape.md`

## Pack identity

The following values are fixed across releases. They are hardcoded in
`src.build_velopack.resolve_pack_command` and must not drift, because the
Velopack runtime keys the install location (`%LocalAppData%\<packId>\`)
off `--packId` and resolves updates against the channel manifest keyed
off `--channel`.

| Argument | Value | Notes |
|---|---|---|
| `--packId` | `mix-calculator` | Stable across releases; changing it would orphan all prior installs. |
| `--packTitle` | `Mix Calculator` | Human-readable display name (shortcut + dialogs). |
| `--packAuthors` | `Dan Moisan` | Embedded in package metadata. |
| `--channel` | `win` | Default Windows release channel. |
| `--mainExe` | `app.exe` | Name of the Nuitka standalone entry executable inside `app.dist/`. |

## Icon

`packaging/velopack/icon.ico` is the icon stamped onto `Setup.exe` and
`Update.exe` by `vpk pack --icon`. The current file is a placeholder
256x256 single-image PNG-encoded ICO (32-bit RGBA, teal diagonal stripe
pattern). Replace it with a designed multi-size ICO (16, 32, 48, 256 px)
when one becomes available.

### Replacement procedure

1. Produce a multi-size Windows `.ico` file containing at minimum the
   16x16, 32x32, 48x48, and 256x256 sub-images. The 256x256 sub-image
   should be PNG-compressed inside the ICO container.
2. Overwrite `packaging/velopack/icon.ico` with the new file. Do not
   rename it; the path is hardcoded in `resolve_pack_command`.
3. Verify the first four bytes are `0x00 0x00 0x01 0x00` (the ICO
   magic):
   ```bash
   python -c "import sys; b=open('packaging/velopack/icon.ico','rb').read(4); sys.exit(0 if b==b'\\x00\\x00\\x01\\x00' else 1)"
   ```
4. Run `poetry run build-velopack --dry-run` to confirm the resolved
   `vpk pack` argv still references the icon by its absolute path.

## GitHub Releases token permission

`build-velopack --upload` invokes `vpk upload github` against
`https://github.com/drmoisan/mix-calculator`. The token presented via
the `GITHUB_TOKEN` environment variable must have the `contents: write`
scope on this repository:

- In GitHub Actions, set
  ```yaml
  permissions:
    contents: write
  ```
  in the workflow or job; `${{ secrets.GITHUB_TOKEN }}` then satisfies
  the requirement automatically.
- For local invocation, generate a personal access token with the
  `repo` write scope and export it as `GITHUB_TOKEN` in the shell.

The script logs the upload command with the token replaced by
`<REDACTED>` so the token never appears in stdout, log files, or CI
captures.

## Outputs

A successful non-dry, non-upload `build-velopack` run produces the
following under `dist/velopack/`:

- `mix-calculator-Setup.exe` (bootstrap installer for end users)
- `mix-calculator-<version>-full.nupkg`
- `mix-calculator-<version>-delta.nupkg` (only when a prior release
  exists in the same `--outputDir`)
- `mix-calculator-Portable.zip`
- `releases.win.json` (channel manifest read by `UpdateManager` at
  runtime)
- `assets.win.json` (build asset catalog)
- `RELEASES` (legacy Squirrel-compatible manifest)

When `--upload` is set, the same artifacts are published to a GitHub
Release at tag `v<version>` with release name `mix-calculator <version>`.
