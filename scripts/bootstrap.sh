#!/usr/bin/env bash

(
  root="$(cd "$(dirname "$0")/.." && pwd)"
  claude_dir="$HOME/.claude"

  stamp="$claude_dir/devkit-sync.stamp"
  interval="${DEVKIT_SYNC_INTERVAL_MIN:-180}"
  if [ -d "$root/.git" ] && [ -z "$(find "$stamp" -mmin -"$interval" 2>/dev/null)" ] \
    && [ "$(git -C "$root" symbolic-ref --short -q HEAD)" = main ] \
    && [ -z "$(git -C "$root" status --porcelain --untracked-files=no)" ]; then
    mkdir -p "$claude_dir" && touch "$stamp"
    GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5" \
      git -C "$root" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 pull -q --ff-only || true
  fi

  (
    src=$(ls -d "$HOME"/.claude/plugins/cache/*/pstack/*/skills/poteto-mode 2>/dev/null | sort -V | tail -n1)
    [ -f "$src/SKILL.md" ] || exit 0
    dst="$HOME/.claude/skills/poteto-mode-auto"
    rm -rf "$dst" && mkdir -p "$dst" && cp -R "$src/." "$dst/" || exit 0
    awk -v src="$src" '
      NR<=12 && /^disable-model-invocation:/ {next}
      /^name: poteto-mode$/ {print "name: poteto-mode-auto"; next}
      {print}
      /^---$/ && ++n==2 {print "\n> Model-invocable copy. Resolve relative paths in this file from `" src "/`."}
    ' "$src/SKILL.md" > "$dst/SKILL.md"
  ) || true

  if [ ! -e "$claude_dir/rules/pstack-models.md" ] && [ -f "$root/rules/pstack-models.md" ]; then
    mkdir -p "$claude_dir/rules" && cp "$root/rules/pstack-models.md" "$claude_dir/rules/pstack-models.md"
  fi

  if [ -f "$root/rules/pstack-principles.md" ]; then
    mkdir -p "$claude_dir/rules" && cp "$root/rules/pstack-principles.md" "$claude_dir/rules/pstack-principles.md"
  fi

  if command -v codex >/dev/null 2>&1 && [ ! -e "$claude_dir/rules/pstack-codex.md" ] && [ -f "$root/rules/pstack-codex.md" ]; then
    mkdir -p "$claude_dir/rules" && cp "$root/rules/pstack-codex.md" "$claude_dir/rules/pstack-codex.md"
  fi
) >/dev/null 2>&1 || true
exit 0
