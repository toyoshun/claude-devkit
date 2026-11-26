---
name: pstack-route
description: Pick the pstack entry point (a poteto-mode playbook or a standalone skill) for the kind of work, and the pstack skills to chain after it. Use at the start of a thread or task, when the kind of work changes, or when the Stop hook says the pstack chain is incomplete.
---

# pstack routing and chaining

pstack lives at `~/.claude/plugins/cache/cursor-plugins/pstack/<newest version>/` (below, `<pstack>`).
Most pstack skills cannot be called through the Skill tool. Read their files with the **Read tool** and follow them. The Stop hook (`<devkit>/scripts/pstack_usage.py`, where `<devkit>` is `~/.claude/skills/devkit`) records those reads, to show what was picked and to warn about skipped steps.
First read `<pstack>/docs/harness/claude-code.md`.

If the repository has `.claude/pstack-route.md`, read it first. Its rows win over the tables below.

## 1. Pick the entry

Take the first row that matches, from the top. For a playbook, load the `poteto-mode-auto` skill, then read `<pstack>/skills/poteto-mode/playbooks/<name>.md`.

| Work | Entry |
| --- | --- |
| A read-only check that takes minutes (look at settings or state, answer a question) | No pstack |
| Continue an earlier thread or branch | poteto-mode, `session-pickup`. Only gathering your own recent work: `recall` |
| Large work, work across several parts, or work that runs while the owner is away | `figure-it-out` and `show-me-your-work` |
| Write a plan only, no implementation | poteto-mode, `multi-phase-plan` |
| Fix a bug | poteto-mode, `bug-fix`. Add `tdd` when a cheap test is possible |
| Add a feature or mechanism | poteto-mode, `feature` |
| Restructure without changing behavior | poteto-mode, `refactoring` |
| Write or change a skill, `CLAUDE.md`, or a runbook | poteto-mode, `authoring-a-skill` |
| Several options that only building and comparing can settle | poteto-mode, `prototype`. Types and structure only: `architect` |
| Investigate a cause or the current state | poteto-mode, `investigation` |
| Questions on how code works or where it lives | `how`. Why questions: `why`. A plain explanation: `teach` |
| Watch a PR | poteto-mode, `babysit`. Landing a batch of green PRs: `shipping` |
| The owner gave the same correction twice | `correct` |

Write the chosen entry in the checklist header, for example "Entry: poteto-mode / feature".

## 2. Chain after the work

When the entry's work is done, run each matching row from the top. The hook checks the rows marked ★. If one is missing, the hook stops the turn once and names the file to read.

| When | Run |
| --- | --- |
| Before concluding an investigation | Search once in the opposite direction, because a settled conclusion pulls in only the sources that agree with it. Write one sentence: "If this conclusion were wrong, what source or data would exist?" Then look for it. Report what you found and what you did not find, next to the conclusion |
| You changed a tool that reads outside data (web pages, APIs, data files) | Run it on real data and confirm it finds what it should before calling it done. "Found nothing" is also what a broken reader returns, like a smoke alarm that is silent because its battery is dead. Example: for a tool that finds dead links, plant one dead link and check that it shows up. When the code splits into paths (drafts and published, for example), push at least one item through each path |
| You created or changed a skill, rule, hook or check | Decide whether every repository could use it unchanged. If yes, move it to claude-devkit with a PR there (add the repository to the session if it is missing) and keep only a pointer here. If it depends on this repository, keep it here |
| Before review, after changing code or a skill | ★`no-comments`. Add `blast-radius` when the change touches checks or hooks, however small |
| The design is contested, or the change is large | `interrogate` |
| You wrote docs or prose | ★`unslop` (docs and PR text) |
| Opening a PR | ★poteto-mode, `opening-a-pr` (it runs `technical-writing`) |
| Before reporting a result to the owner | ★`goal-check` (this plugin's `skills/goal-check/SKILL.md`): a fresh agent checks the real result against the owner's own words. The hook asks for it once a PR is opened |
| After opening a PR | ★poteto-mode, `babysit`. Whether you may merge on green CI is up to the repository's rules |
| After merging a PR | ★`reflect`. Turn lessons into proposed skill edits: in this repository for lessons about it, in claude-devkit for lessons any repository could use. With no lesson, say so in one line |

The ★ checks live in `RULES` in `<devkit>/scripts/pstack_usage.py`. When you add a row, change this table and `RULES` together.

## 3. Records

Each session writes one file: `/mnt/project-files/pstack-usage/` in the cloud, `~/.claude/pstack-usage/` on a Mac. List them with:

```bash
python3 ~/.claude/skills/devkit/scripts/pstack_usage.py report
```
