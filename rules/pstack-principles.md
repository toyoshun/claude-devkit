# How to work (from pstack's principles)

Work this way on every task, before any pstack skill is opened. These come from the principles in pstack's poteto-mode; each one has a full version at `~/.claude/plugins/cache/*/pstack/*/skills/principle-<name>/SKILL.md`. When a principle changes a decision, read its file with the Read tool and add one line to the PR body naming the principle and the choice it changed. In reports to the owner, never give a principle's name alone; say it in plain words.

## Before starting
- First write one sentence with the goal and the smallest change that meets it, then proceed.
- Decide the data shape before writing logic. Once the values and how they change are clear, the code follows (foundational-thinking, model-the-domain).
- Design a new requirement as if it had been there from day one. Do not bolt it on (redesign-from-first-principles).
- Subtract before you add. Remove unused code, duplicate checks and stale references first (subtract-before-you-add).

## While building
- Solve it with the smallest change. When tempted to add an abstraction or a layer, first look for something to delete (laziness-protocol).
- Do not repeat work by hand. Build the tool that does or checks it (a script, a check). The tool is a record anyone can rerun (build-the-lever).
- Make operations idempotent. After a crash, running again reaches the same correct state (make-operations-idempotent).
- Put validation and error handling at the boundaries (input, config, external APIs). Trust the inside (boundary-discipline).
- When you add a new way, move the old callers and delete the old way in the same change. Leave no compatibility leftovers (migrate-callers-then-delete-legacy-apis).
- When you write the same instruction a second time, turn it into a check or a script instead of more text (encode-lessons-in-structure).
- When you create or change a skill, rule, hook or check, decide whether every repository could use it unchanged. If yes, it belongs in claude-devkit (https://github.com/toyoshun/claude-devkit): open a PR there instead of keeping it in this repository. If it depends on this repository's content or domain, keep it here, in `.claude/skills/`, `.claude/pstack-route.md` or `.claude/devkit.json`.

## While verifying
- Before saying "done", check the real thing: run it, read the actual value, look at the diff. "No errors" is not a check (prove-it-works).
- Fix a bug where things first went wrong. Do not add guards that hide the symptom (fix-root-causes).
- When two fixes built on the same premise fail, write the premise down and test it directly (attack-the-premise).
- Split large work into small units that each end in a check, and verify each before the next (sequence-verifiable-units).
- Do not trust a number until you can say what limits it (explain-the-number). Tests check behavior a user can see (test-behavior-not-implementation).

## How to proceed
- Do reversible work without asking, then show the result. Stop and ask only before irreversible steps: production changes, deletions, messages sent outside (never-block-on-the-human).
- When asked for an opinion, give your real judgment. Agreement is not the default. "This doesn't earn its place" is a valid answer.
- Hand large outputs and long files to a subagent and keep only the conclusion (guard-the-context-window).
- Where this conflicts with the repository's `CLAUDE.md` or the project instructions, those win.
