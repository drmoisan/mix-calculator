---
name: poetry-virtualenv-quirk
description: Historical VIRTUAL_ENV/Poetry mismatch — resolved by virtualenvs.in-project; the env -u VIRTUAL_ENV prefix is no longer required
metadata:
  type: project
---

RESOLVED as of 2026-05-26. `VIRTUAL_ENV` now points at the in-repo `.venv`
(`c:\Users\DanMoisan\repos\mix-calculator\.venv`), and `poetry run <tool>` resolves to
`.venv\Scripts\python.exe` with or without the `env -u VIRTUAL_ENV` prefix. The prefix is
no longer necessary.

**Why:** Originally (issue #2 feature review) `VIRTUAL_ENV` pointed at a global Python,
causing a mismatch with Poetry's project venv; the `env -u VIRTUAL_ENV` prefix was a
workaround. The durable fix is now in place: `poetry config virtualenvs.in-project = true`
pins the venv to `.venv/` in the repo, and the activated environment agrees with Poetry.
Verified 2026-05-26: `poetry env info`, `which python`, and `poetry run python -c "import
sys; print(sys.executable)"` all resolve to the in-repo `.venv` without the prefix.

**How to apply:** Run `poetry run ...` verification commands directly; no prefix needed.
Keep `virtualenvs.in-project = true`. If `VIRTUAL_ENV` ever diverges from `.venv` again,
`deactivate` and re-activate `.venv/Scripts/activate` rather than reintroducing the prefix.
Note the Bash tool's cwd is the repo root but backslash Windows paths break `cd`; use
forward slashes or absolute paths.
