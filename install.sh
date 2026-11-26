#!/usr/bin/env bash

here="$(cd "$(dirname "$0")" && pwd -P)"
dest="$HOME/.claude/skills/devkit"
mode=link
[ "${1:-}" = "--copy" ] && mode=copy

if ! command -v claude >/dev/null 2>&1; then
  echo "pstack: claude コマンドがないので入れない"
elif ls -d "$HOME"/.claude/plugins/cache/*/pstack/* >/dev/null 2>&1; then
  echo "pstack: 入っている"
else
  claude plugin marketplace add cursor/plugins || true
  claude plugin install pstack@cursor-plugins --scope user || true
  echo "pstack: 入れた"
fi

mkdir -p "$HOME/.claude/skills"
if [ -d "$dest" ] && [ "$(cd "$dest" && pwd -P)" = "$here" ] && [ ! -L "$dest" ]; then
  echo "devkit: $dest が実体なのでそのまま使う"
else
  rm -rf "$dest"
  if [ "$mode" = copy ]; then
    cp -R "$here" "$dest" && echo "devkit: $dest にコピーした"
  else
    ln -sfn "$here" "$dest" && echo "devkit: $dest から $here へリンクした"
  fi
fi

bash "$here/scripts/bootstrap.sh"
echo "bootstrap: 済んだ"
exit 0
