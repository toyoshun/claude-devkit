# claude-devkit

A Claude Code plugin with shared tools for any repository: pstack routing, a pstack usage record, checks right after each edit, and pstack's principles as an always-on rule. See `README.md` for contents and install steps.

## Rules

- Only put things here that every repository can use unchanged. Anything specific to one repository (its content, domain skills, its own checks) goes in that repository's `.claude/pstack-route.md` and `.claude/devkit.json`.
- Write everything in this repository in English: code, comments, script output, docs, skills and rules. The owner talks to Claude in Japanese; `templates/project-instructions.md` stays Japanese because the owner pastes it into project instructions.
- Hook scripts (`scripts/*.py`) use the standard library only and stay Python 3.9 compatible, because hooks run under the Mac's system python3.
- A failing hook never stops the session.
- `install.sh` and `scripts/bootstrap.sh` are idempotent and run on macOS bash 3.2.
- No secrets, personal data, or any repository's operational data. This repository is public.

## Checks

```bash
uv sync --frozen
bash -n install.sh scripts/bootstrap.sh
uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q
```
