# pstack and Codex

In pstack's parallel phases (arena, interrogate, swarm), give one seat (the `inherit-parent` seat) to Codex.

- Reach Codex through the `codex:codex-rescue` subagent. Never call Codex directly from poteto-mode.
- When Codex is unavailable (the call fails or its login expired), give the seat back to Claude and continue.
- This rule applies only where the `codex` command exists (the local Mac). Environments without it do not get this file.
