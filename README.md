# claude-devkit

A Claude Code plugin with shared pstack tooling that works in any repository.

## Contents

| Path | What it does |
| --- | --- |
| `skills/pstack-route/` | Picks the pstack entry point for the kind of work, and the skills to chain after it |
| `scripts/pstack_usage.py` | Stop hook. Records which pstack skills a session used and flags skipped chain steps. `report` lists the records |
| `scripts/edit_check.py` | PostToolUse hook. Checks the one file just edited: ruff for `*.py`, plus the repository's own checks from `.claude/devkit.json` |
| `scripts/bootstrap.sh` | SessionStart hook. Rebuilds the `poteto-mode-auto` copy and fills `~/.claude/rules/`. It rewrites the principles rule every time and never overwrites existing model or Codex rules |
| `rules/` | `pstack-principles.md` (pstack's principles, short, loaded in every session), pstack model roles, and the Codex rule (installed only where `codex` exists) |
| `templates/project-instructions.md` | Text to paste into a new Claude project's instructions |
| `install.sh` | Installs everything into `~/.claude` |

## Install

Mac:

```bash
git clone https://github.com/toyoshun/claude-devkit ~/dev/claude-devkit
bash ~/dev/claude-devkit/install.sh
```

This links `~/.claude/skills/devkit` to the checkout, so Claude Code loads it as a plugin. `--copy` copies instead of linking. If pstack is missing and the `claude` command exists, it installs pstack too. Update with `git pull` in the checkout; the next session uses the new version.

Cloud environment: add one line to the environment's setup script.

```bash
git clone --depth 1 https://github.com/toyoshun/claude-devkit /opt/claude-devkit && bash /opt/claude-devkit/install.sh
```

Rerunning is safe. Rules files are loaded at session start, so run `install.sh` before the first session (a setup script does).

For a new Claude project, paste `templates/project-instructions.md` into the project instructions.

## Per-repository additions

- `.claude/pstack-route.md`: entry rows and chain rows for that repository only. The `pstack-route` skill reads it first, and its rows win.
- `.claude/devkit.json`: extra checks after each edit. Each matching file's relative path is appended to `run`, which runs from the repository root. `python3` uses `.venv/bin/python` when it exists.

```json
{
  "edit_checks": [
    {"glob": "docs/*.md", "run": ["python3", "tools/lint.py"]}
  ]
}
```

A check that prints anything exits 2, which shows the output to Claude without stopping the work.

## Records

One file per session: `/mnt/project-files/pstack-usage/` in the cloud, `~/.claude/pstack-usage/` on a Mac. Set `PSTACK_USAGE_DIR` to change it.

```bash
python3 ~/.claude/skills/devkit/scripts/pstack_usage.py report
```
