# claude-devkit

A Claude Code plugin with shared pstack tooling that works in any repository.

## Contents

| Path | What it does |
| --- | --- |
| `skills/pstack-route/` | Picks the pstack entry point for the kind of work, and the skills to chain after it |
| `skills/goal-check/` | Before reporting "done", a fresh agent checks the real result against the owner's own words, goal by goal, with evidence |
| `scripts/pstack_usage.py` | Stop hook. Records which pstack skills a session used and flags skipped chain steps. `report` lists the records |
| `scripts/edit_check.py` | PostToolUse hook. Checks the one file just edited: ruff for `*.py`, plus the repository's own checks from `.claude/devkit.json` |
| `scripts/bootstrap.sh` | SessionStart hook. Rebuilds the `poteto-mode-auto` copy and fills `~/.claude/rules/`. It rewrites the principles rule every time and never overwrites existing model or Codex rules |
| `rules/` | `pstack-principles.md` (pstack's principles, short, loaded in every session), pstack model roles, and the Codex rule (installed only where `codex` exists) |
| `templates/` | What to paste when starting a new project: `cloud-setup.sh`, `project-instructions.md`, `kickoff.md` |
| `install.sh` | Installs everything into `~/.claude` |

## Start a new project

The goal is a new project that works like affi-lab from its first thread. Three pastes, all from `templates/`:

1. **Cloud environment.** In the environment's settings, paste `templates/cloud-setup.sh` as the setup script. It installs claude-devkit (which installs pstack) and each repo's locked dependencies (`uv.lock`, `package-lock.json`). The same script works for every project, so one personal environment can serve all of them.
2. **Project instructions.** Paste the block in `templates/project-instructions.md`. It sets the pstack routine, Codex use, the language rule and how to report to the owner.
3. **First message.** Paste the block in `templates/kickoff.md` into the project's first thread. Claude then checks the install, writes `CLAUDE.md`, adds `.claude/pstack-route.md` and `.claude/devkit.json` only when the repo needs them, adds CI if missing, and saves the project's decisions to memory.

On a Mac, the one-time install below is enough for every project. Where the `codex` command exists, `bootstrap.sh` also installs the Codex rule. Personal Mac settings such as a Codex update wrapper stay outside this repository.

## Where new tools go

When any project creates or changes a skill, rule, hook or check, Claude decides whether every repository could use it unchanged. Generic ones come here by PR; repository-specific ones stay in that repository (`.claude/skills/`, `.claude/pstack-route.md`, `.claude/devkit.json`). The principles rule and the `pstack-route` chain both carry this step, so it applies in every project. Other machines pick up the change with `git pull` (Mac) or on the next fresh cloud container.

## Install

Mac:

```bash
git clone https://github.com/toyoshun/claude-devkit ~/dev/claude-devkit
bash ~/dev/claude-devkit/install.sh
```

This links `~/.claude/skills/devkit` to the checkout, so Claude Code loads it as a plugin. `--copy` copies instead of linking. If pstack is missing and the `claude` command exists, it installs pstack too. Update with `git pull` in the checkout; the next session uses the new version.

Cloud environment: use `templates/cloud-setup.sh` (see above), or add this one line to an existing setup script.

```bash
git clone --depth 1 https://github.com/toyoshun/claude-devkit /opt/claude-devkit && bash /opt/claude-devkit/install.sh
```

Rerunning is safe. Rules files are loaded at session start, so run `install.sh` before the first session (a setup script does).

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
