"""A repo adds checks in `.claude/devkit.json`:

    {"edit_checks": [{"glob": "docs/*.md", "run": ["python3", "tools/lint.py"]}]}

Each matching entry runs from the repo root with the relative path appended.
Stdlib only and 3.9-safe, because the hook runs under the system python3.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

TIMEOUT = 30
PYTHONS = ("python", "python3")


def repo_root(path: Path) -> Path | None:
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    return None


def ruff_commands(root: Path, rel: str) -> list[list[str]]:
    venv = root / ".venv" / "bin" / "ruff"
    ruff = str(venv) if venv.exists() else shutil.which("ruff")
    if not ruff:
        return []
    return [
        [ruff, "check", "--fix", "--silent", "--", rel],
        [ruff, "format", "--quiet", "--", rel],
        [ruff, "check", "--quiet", "--output-format", "concise", "--", rel],
    ]


def repo_commands(root: Path, rel: str) -> list[list[str]]:
    try:
        config = json.loads((root / ".claude" / "devkit.json").read_text("utf-8"))
        entries = config["edit_checks"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    commands: list[list[str]] = []
    for entry in entries if isinstance(entries, list) else []:
        run = entry.get("run") if isinstance(entry, dict) else None
        glob = entry.get("glob") if isinstance(entry, dict) else None
        if not (isinstance(glob, str) and fnmatch(rel, glob)):
            continue
        if not (isinstance(run, list) and run and all(isinstance(a, str) for a in run)):
            continue
        argv: list[str] = list(run)
        venv_python = root / ".venv" / "bin" / "python"
        if argv[0] in PYTHONS and venv_python.exists():
            argv[0] = str(venv_python)
        commands.append([*argv, rel])
    return commands


def run_command(argv: list[str], root: Path) -> str:
    try:
        done = subprocess.run(  # noqa: S603
            argv,
            cwd=root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout + done.stderr


def edited_file(stdin_text: str) -> Path | None:
    try:
        payload: Any = json.loads(stdin_text)
        return Path(payload["tool_input"]["file_path"]).resolve()
    except (ValueError, KeyError, TypeError, OSError, RuntimeError):
        return None


def findings(stdin_text: str) -> str:
    target = edited_file(stdin_text)
    root = repo_root(target) if target else None
    if not target or not root or not target.is_file():
        return ""
    rel = target.relative_to(root).as_posix()
    if rel.startswith(".venv/"):
        return ""
    commands = ruff_commands(root, rel) if rel.endswith(".py") else []
    commands += repo_commands(root, rel)
    output = [run_command(argv, root) for argv in commands]
    return "".join(output).strip()


def main() -> int:
    message = findings(sys.stdin.buffer.read().decode("utf-8", "replace"))
    if not message:
        return 0
    sys.stderr.buffer.write(f"{message}\n".encode())
    sys.stderr.flush()
    return 2


if __name__ == "__main__":
    sys.exit(main())
