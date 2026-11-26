#!/usr/bin/env bash
# Usage: bash install.sh [--copy]. Safe to rerun.

here="$(cd "$(dirname "$0")" && pwd -P)"
dest="$HOME/.claude/skills/devkit"
mode=link
[ "${1:-}" = "--copy" ] && mode=copy

if ! command -v claude >/dev/null 2>&1; then
  echo "pstack: skipped (no claude command)"
elif ls -d "$HOME"/.claude/plugins/cache/*/pstack/* >/dev/null 2>&1; then
  echo "pstack: already installed"
else
  claude plugin marketplace add cursor/plugins || true
  claude plugin install pstack@cursor-plugins --scope user || true
  echo "pstack: installed"
fi

mkdir -p "$HOME/.claude/skills"
if [ -d "$dest" ] && [ "$(cd "$dest" && pwd -P)" = "$here" ] && [ ! -L "$dest" ]; then
  echo "devkit: $dest is this checkout, left as is"
else
  rm -rf "$dest"
  if [ "$mode" = copy ]; then
    cp -R "$here" "$dest" && echo "devkit: copied to $dest"
  else
    ln -sfn "$here" "$dest" && echo "devkit: linked $dest -> $here"
  fi
fi

bash "$here/scripts/bootstrap.sh"
echo "bootstrap: done"
exit 0
