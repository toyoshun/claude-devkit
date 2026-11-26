"""Stdlib only and 3.9-safe, because the hook runs under the system python3."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple, TypedDict

ALIASES = {"poteto-mode-auto": "poteto-mode"}
SKILL_RE = re.compile(r"([A-Za-z0-9-]+)/SKILL\.md")
PLAYBOOK_RE = re.compile(r"poteto-mode(?:-auto)?/playbooks/([a-z0-9-]+)\.md")
EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
CLOUD_DIR = Path("/mnt/project-files")
DEVKIT = Path(__file__).absolute().parent.parent
PROSE_SUFFIXES = (".md", ".mdx", ".txt")
ROUTER = "pstack-route"
GH_PR_RE = re.compile(r"\bgh\s+pr\s+(create|merge)\b")


class Record(TypedDict):
    session_id: str
    updated: str
    branch: str
    skills: list[str]
    playbooks: list[str]
    project_skills: list[str]
    triggers: list[str]
    missing: list[str]
    warned: list[str]


class Rule(NamedTuple):
    triggers: frozenset[str]
    key: str
    message: str


RULES: tuple[Rule, ...] = (
    Rule(
        frozenset({"changed"}),
        "pstack",
        "You changed files without using pstack. Read {devkit}/skills/"
        "pstack-route/SKILL.md and follow the entry it picks.",
    ),
    Rule(
        frozenset({"pr_opened"}),
        "playbook:opening-a-pr",
        "Read {root}/skills/poteto-mode/playbooks/opening-a-pr.md "
        "and bring the PR title and body in line with it.",
    ),
    Rule(
        frozenset({"pr_opened"}),
        "playbook:babysit",
        "Read {root}/skills/poteto-mode/playbooks/babysit.md "
        "and see the PR's CI and reviews through as it says.",
    ),
    Rule(
        frozenset({"pr_opened"}),
        "goal-check",
        "Read {devkit}/skills/goal-check/SKILL.md and have a fresh agent "
        "check the result against the owner's request before you report it.",
    ),
    Rule(
        frozenset({"code", "pr_opened"}),
        "no-comments",
        "Read {root}/skills/no-comments/SKILL.md "
        "and remove the comments the change added that it does not need.",
    ),
    Rule(
        frozenset({"prose", "pr_opened"}),
        "unslop",
        "Read {root}/skills/unslop/SKILL.md "
        "and remove AI tells from the docs and PR text.",
    ),
    Rule(
        frozenset({"pr_merged"}),
        "reflect",
        "Read {root}/skills/reflect/SKILL.md "
        "and turn this session's lessons into proposed skill edits. "
        "If there is no lesson, say so in one line.",
    ),
)


def plugin_cache() -> Path:
    return Path.home() / ".claude" / "plugins" / "cache"


def record_dir() -> Path:
    override = os.environ.get("PSTACK_USAGE_DIR")
    if override:
        return Path(override)
    if CLOUD_DIR.exists():
        return CLOUD_DIR / "pstack-usage"
    return Path.home() / ".claude" / "pstack-usage"


def pstack_skill_names(cache: Path) -> set[str]:
    return {p.parent.name for p in cache.glob("*/pstack/*/skills/*/SKILL.md")}


def newest_pstack(cache: Path) -> Path | None:
    versions = [p for p in cache.glob("*/pstack/*") if p.is_dir()]

    def key(p: Path) -> tuple[tuple[int, ...], str]:
        return tuple(int(n) for n in re.findall(r"\d+", p.name)), p.name

    return max(versions, key=key, default=None)


def repo_root(path: Path) -> Path | None:
    for parent in (path, *path.parents):
        if (parent / ".git").exists():
            return parent
    return None


def skill_dirs(base: Path) -> set[str]:
    return {p.name for p in base.iterdir() if p.is_dir()} if base.is_dir() else set()


def project_skill_names(repos: list[Path], devkit: Path) -> set[str]:
    names = skill_dirs(devkit / "skills")
    for repo in repos:
        names |= skill_dirs(repo / ".claude" / "skills")
    return names


def git_branch(cwd: str) -> str:
    try:
        out = subprocess.run(  # noqa: S603
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def transcript_files(transcript: Path) -> list[Path]:
    subs = sorted((transcript.with_suffix("") / "subagents").glob("*.jsonl"))
    return [transcript, *subs]


def tool_calls(files: list[Path]) -> list[tuple[str, dict[str, Any], bool]]:
    uses: list[tuple[str, str, dict[str, Any]]] = []
    failed: set[str] = set()
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            message = obj.get("message") if isinstance(obj, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "tool_result" and item.get("is_error"):
                    failed.add(str(item.get("tool_use_id")))
                if item.get("type") == "tool_use":
                    tool_input = item.get("input")
                    name = item.get("name")
                    if isinstance(name, str) and isinstance(tool_input, dict):
                        uses.append((str(item.get("id")), name, tool_input))
    return [
        (name, tool_input, use_id not in failed) for use_id, name, tool_input in uses
    ]


def _add(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _classify(raw: str, pstack: set[str], project: set[str], rec: Record) -> None:
    name = ALIASES.get(raw, raw)
    if name in pstack:
        _add(rec["skills"], name)
    elif name in project:
        _add(rec["project_skills"], name)


def edited_repo(path: str, cwd: str) -> tuple[Path, Path] | None:
    target = Path(os.path.normpath(os.path.join(cwd, path)))
    if (Path.home() / ".claude") in (target, *target.parents):
        return None
    repo = repo_root(target.parent)
    return (target, repo) if repo else None


def _edit_triggers(target: Path) -> set[str]:
    return {"changed", "prose" if target.suffix in PROSE_SUFFIXES else "code"}


def build_record(
    session_id: str,
    transcript: Path,
    cwd: str,
    cache: Path,
    devkit: Path,
    warned: list[str],
) -> Record:
    pstack = pstack_skill_names(cache) | set(ALIASES)
    calls = tool_calls(transcript_files(transcript))
    edits: list[tuple[Path, Path]] = []
    for name, tool_input, _ in calls:
        path = tool_input.get("file_path") or tool_input.get("notebook_path")
        found = edited_repo(str(path), cwd) if name in EDIT_TOOLS and path else None
        if found:
            edits.append(found)
    cwd_repo = repo_root(Path(cwd))
    repos = ([cwd_repo] if cwd_repo else []) + [repo for _, repo in edits]
    project = project_skill_names(repos, devkit)
    branch = git_branch(str(cwd_repo or (edits[0][1] if edits else cwd)))
    rec = Record(
        session_id=session_id,
        updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        branch=branch,
        skills=[],
        playbooks=[],
        project_skills=[],
        triggers=[],
        missing=[],
        warned=list(warned),
    )
    triggers: set[str] = set()
    for target, _ in edits:
        triggers |= _edit_triggers(target)
    for name, tool_input, ok in calls:
        if name == "Skill":
            raw = str(tool_input.get("skill", ""))
            raw = raw.removeprefix("pstack:").removeprefix("devkit:")
            _classify(raw, pstack, project, rec)
        text = ""
        if name == "Read":
            text = str(tool_input.get("file_path", ""))
        elif name == "Bash":
            text = str(tool_input.get("command", ""))
            if "git commit" in text:
                triggers.add("changed")
            for action in GH_PR_RE.findall(text) if ok else ():
                triggers.add("pr_opened" if action == "create" else "pr_merged")
        for playbook in PLAYBOOK_RE.findall(text):
            _add(rec["skills"], "poteto-mode")
            _add(rec["playbooks"], playbook)
        for raw in SKILL_RE.findall(text):
            _classify(raw, pstack, project, rec)
        if ok and name.endswith("create_pull_request"):
            triggers.add("pr_opened")
        if ok and name.endswith("merge_pull_request"):
            triggers.add("pr_merged")
    rec["triggers"] = sorted(triggers)
    rec["missing"] = [
        r.key for r in RULES if r.triggers <= triggers and not met(r.key, rec)
    ]
    return rec


def met(key: str, rec: Record) -> bool:
    kind, _, name = key.partition(":")
    if kind == "playbook":
        return name in rec["playbooks"]
    if key == "pstack":
        return bool(rec["skills"]) or any(s != ROUTER for s in rec["project_skills"])
    return key in rec["skills"] or key in rec["project_skills"]


def block_reason(keys: list[str], devkit: Path, root: Path | None) -> str:
    fill = {"root": str(root) if root else "<pstack>", "devkit": str(devkit)}
    lines = ["The pstack chain is not finished. Before you stop, do the following."]
    lines += [f"- {r.message.format(**fill)}" for r in RULES if r.key in keys]
    return "\n".join(lines)


def run_hook(stdin_text: str, cache: Path, directory: Path, devkit: Path) -> str:
    payload = json.loads(stdin_text)
    session_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(payload["session_id"]))
    cwd = str(payload.get("cwd") or os.getcwd())
    path = directory / f"{session_id}.json"
    try:
        warned = list(json.loads(path.read_text(encoding="utf-8"))["warned"])
    except (OSError, ValueError, KeyError, TypeError):
        warned = []
    rec = build_record(
        session_id,
        Path(payload["transcript_path"]),
        cwd,
        cache,
        devkit,
        warned,
    )
    fresh = [k for k in rec["missing"] if k not in warned]
    blocking = bool(fresh) and not payload.get("stop_hook_active")
    if blocking:
        rec["warned"] = warned + fresh
    directory.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(
        json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)
    if not blocking:
        return ""
    reason = block_reason(fresh, devkit, newest_pstack(cache))
    return json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False)


def report(directory: Path) -> str:
    records: list[dict[str, Any]] = []
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            records.append(data)
    records.sort(key=lambda r: str(r.get("updated", "")), reverse=True)

    def cell(rec: dict[str, Any], key: str) -> str:
        value = rec.get(key) or "-"
        return ",".join(value) if isinstance(value, list) else str(value)

    header = ("updated", "branch", "playbooks", "skills", "project", "missing")
    keys = ("branch", "playbooks", "skills", "project_skills", "missing")
    rows = [
        (str(r.get("updated", ""))[:16].replace("T", " "), *(cell(r, k) for k in keys))
        for r in records
    ]
    table = [header, *rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    return "\n".join(
        "  ".join(row[i].ljust(widths[i]) for i in range(len(header))).rstrip()
        for row in table
    )


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else ""
    if command == "report":
        print(report(record_dir()))
    elif command == "hook":
        try:
            output = run_hook(sys.stdin.read(), plugin_cache(), record_dir(), DEVKIT)
            if output:
                print(output)
        except Exception as exc:  # noqa: BLE001
            print(f"pstack_usage: {exc!r}", file=sys.stderr)
    else:
        print("usage: pstack_usage.py hook|report", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
