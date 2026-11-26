#!/bin/bash
# Cloud environment setup script for any project. Paste it whole into the environment's setup script.
# It installs claude-devkit (and pstack through it), then each checked-out repo's locked dependencies.
[ -f claude-devkit/install.sh ] || git clone -q --depth 1 https://github.com/toyoshun/claude-devkit /opt/claude-devkit || true
for d in claude-devkit /opt/claude-devkit; do
  if [ -f "$d/install.sh" ]; then bash "$d/install.sh" || true; break; fi
done
for r in */; do
  if [ -f "$r/uv.lock" ] && command -v uv >/dev/null; then (cd "$r" && uv sync --frozen -q) || true; fi
  if [ -f "$r/package-lock.json" ] && command -v npm >/dev/null; then (cd "$r" && npm ci --silent) || true; fi
done
