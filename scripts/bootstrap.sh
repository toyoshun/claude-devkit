#!/usr/bin/env bash

(
  root="$(cd "$(dirname "$0")/.." && pwd)"
  claude_dir="$HOME/.claude"

  (
    src=$(ls -d "$HOME"/.claude/plugins/cache/*/pstack/*/skills/poteto-mode 2>/dev/null | sort -V | tail -n1)
    [ -f "$src/SKILL.md" ] || exit 0
    dst="$HOME/.claude/skills/poteto-mode-auto"
    rm -rf "$dst" && mkdir -p "$dst" && cp -R "$src/." "$dst/" || exit 0
    awk -v src="$src" '
      NR<=12 && /^disable-model-invocation:/ {next}
      /^name: poteto-mode$/ {print "name: poteto-mode-auto"; next}
      {print}
      /^---$/ && ++n==2 {print "\n> 自動で呼べる写し。本文の相対パスは `" src "/` を起点に読む。"}
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
