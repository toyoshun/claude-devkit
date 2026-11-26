import json
from pathlib import Path
from typing import Any

import pstack_usage

SKILLS = ("poteto-mode", "no-comments", "unslop", "reflect")


class Env:
    def __init__(self, tmp_path: Path) -> None:
        self.cwd = tmp_path / "repo"
        (self.cwd / ".git").mkdir(parents=True)
        (self.cwd / ".claude" / "skills" / "affiliate-weekly").mkdir(parents=True)
        self.devkit = tmp_path / "devkit"
        for name in ("pstack-route", "goal-check"):
            (self.devkit / "skills" / name).mkdir(parents=True)
        self.cache = tmp_path / "cache"
        for old, version in (("9", "0.9.0"), ("15", "0.15.48")):
            for name in SKILLS:
                skill = self.cache / "x" / "pstack" / version / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(old)
        self.records = tmp_path / "records"
        self.transcript = tmp_path / "s.jsonl"
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call(self, name: str, **tool_input: Any) -> "Env":
        self.calls.append((name, tool_input))
        return self

    def write(self, path: Path, calls: list[tuple[str, dict[str, Any]]]) -> None:
        lines = ["not json"] + [
            json.dumps(
                {"message": {"content": [{"type": "tool_use", "name": n, "input": i}]}}
            )
            for n, i in calls
        ]
        path.write_text("\n".join(lines))

    def run(
        self, active: bool = False, cwd: Path | None = None
    ) -> tuple[str, dict[str, Any]]:
        self.write(self.transcript, self.calls)
        payload = {
            "session_id": "s",
            "transcript_path": str(self.transcript),
            "cwd": str(cwd or self.cwd),
            "stop_hook_active": active,
        }
        out = pstack_usage.run_hook(
            json.dumps(payload), self.cache, self.records, self.devkit
        )
        return out, json.loads((self.records / "s.json").read_text())

    def edit(self, rel: str = "tooling/x.py") -> "Env":
        return self.call("Edit", file_path=str(self.cwd / rel))


def test_edit_without_pstack_blocks_with_route_message(tmp_path: Path) -> None:
    env = Env(tmp_path).edit()
    out, rec = env.run()
    assert json.loads(out)["decision"] == "block"
    reason = json.loads(out)["reason"]
    assert f"{env.devkit}/skills/pstack-route/SKILL.md" in reason
    assert rec["missing"] == ["pstack"]
    assert rec["triggers"] == ["changed", "code"]


def test_read_only_session_never_blocks(tmp_path: Path) -> None:
    env = Env(tmp_path).call("Read", file_path="/etc/hosts")
    env.call("Edit", file_path="/elsewhere/x.py")
    out, rec = env.run()
    assert out == ""
    assert rec["triggers"] == [] and rec["missing"] == []


def test_each_way_of_reading_poteto_mode_clears_pstack(tmp_path: Path) -> None:
    reads = (
        ("Read", {"file_path": "/p/pstack/0.15.48/skills/poteto-mode/SKILL.md"}),
        ("Skill", {"skill": "poteto-mode-auto"}),
        ("Skill", {"skill": "pstack:poteto-mode"}),
        ("Bash", {"command": "cat /p/skills/poteto-mode/playbooks/feature.md"}),
    )
    for i, (name, tool_input) in enumerate(reads):
        env = Env(tmp_path / str(i)).edit().call(name, **tool_input)
        out, rec = env.run()
        assert out == "" and rec["skills"] == ["poteto-mode"]
        assert rec["playbooks"] == (["feature"] if name == "Bash" else [])


def test_project_skill_and_prose_trigger(tmp_path: Path) -> None:
    env = Env(tmp_path).edit("content/a/article.md")
    env.call("Read", file_path=".claude/skills/affiliate-weekly/SKILL.md")
    env.call("Read", file_path=".claude/skills/unknown/SKILL.md")
    _, rec = env.run()
    assert rec["project_skills"] == ["affiliate-weekly"]
    assert rec["skills"] == [] and rec["triggers"] == ["changed", "prose"]


def test_md_edit_asks_for_unslop_when_a_pr_opens(tmp_path: Path) -> None:
    env = Env(tmp_path).edit("docs/a.md").call("mcp__github__create_pull_request")
    env.call("Skill", skill="poteto-mode")
    _, rec = env.run()
    assert "unslop" in rec["missing"] and "no-comments" not in rec["missing"]


def test_devkit_own_skill_is_recorded_as_project_skill(tmp_path: Path) -> None:
    env = Env(tmp_path).edit()
    env.call("Read", file_path="/h/.claude/skills/devkit/skills/pstack-route/SKILL.md")
    env.call("Skill", skill="devkit:pstack-route")
    _, rec = env.run()
    assert rec["project_skills"] == ["pstack-route"]


def test_edit_outside_a_git_repo_is_ignored(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.call("Edit", file_path=str(tmp_path / "plain" / "x.py"))
    out, rec = env.run()
    assert out == "" and rec["triggers"] == []


def test_edit_under_dot_claude_is_ignored(tmp_path: Path, monkeypatch: Any) -> None:
    home = tmp_path / "home"
    (home / ".claude" / ".git").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home)
    env = Env(tmp_path).call("Edit", file_path=str(home / ".claude" / "x.py"))
    out, rec = env.run()
    assert out == "" and rec["triggers"] == []


def test_cwd_outside_repo_still_sees_repo_of_edited_file(tmp_path: Path) -> None:
    env = Env(tmp_path).edit()
    env.call("Read", file_path="/r/.claude/skills/affiliate-weekly/SKILL.md")
    _, rec = env.run(cwd=tmp_path)
    assert rec["triggers"] == ["changed", "code"]
    assert rec["project_skills"] == ["affiliate-weekly"]


def test_pr_opened_blocks_once_per_missing_key(tmp_path: Path) -> None:
    env = Env(tmp_path).edit().call("mcp__github__create_pull_request")
    env.call("Skill", skill="poteto-mode")
    out, rec = env.run()
    reason = json.loads(out)["reason"]
    assert rec["missing"] == [
        "playbook:opening-a-pr",
        "playbook:babysit",
        "goal-check",
        "no-comments",
    ]
    assert "0.15.48/skills/no-comments/SKILL.md" in reason
    assert "devkit/skills/goal-check/SKILL.md" in reason
    assert "0.9.0" not in reason
    assert rec["warned"] == rec["missing"]
    out2, rec2 = env.run()
    assert out2 == "" and rec2["missing"] == rec["missing"]


def test_goal_check_counts_from_the_skill_tool_or_a_read(tmp_path: Path) -> None:
    for i, (name, tool_input) in enumerate(
        [
            ("Skill", {"skill": "devkit:goal-check"}),
            ("Read", {"file_path": "/d/skills/goal-check/SKILL.md"}),
        ]
    ):
        env = Env(tmp_path / str(i)).edit().call("mcp__github__create_pull_request")
        env.call(name, **tool_input)
        assert "goal-check" not in env.run()[1]["missing"]


def test_stop_hook_active_never_blocks_and_does_not_mark_warned(
    tmp_path: Path,
) -> None:
    env = Env(tmp_path).edit()
    out, rec = env.run(active=True)
    assert out == "" and rec["warned"] == []
    assert json.loads(env.run()[0])["decision"] == "block"


def test_subagent_reads_count(tmp_path: Path) -> None:
    env = Env(tmp_path).edit().call("mcp__x__merge_pull_request")
    subs = tmp_path / "s" / "subagents"
    subs.mkdir(parents=True)
    env.write(
        subs / "a.jsonl",
        [
            ("Read", {"file_path": "/p/skills/poteto-mode/playbooks/babysit.md"}),
            ("Read", {"file_path": "/p/skills/reflect/SKILL.md"}),
        ],
    )
    _, rec = env.run()
    assert rec["playbooks"] == ["babysit"]
    assert rec["skills"] == ["poteto-mode", "reflect"]
    assert rec["missing"] == []


def test_report_lists_newest_first(tmp_path: Path) -> None:
    env = Env(tmp_path).edit()
    env.run()
    (env.records / "old.json").write_text(
        json.dumps({"updated": "2020-01-02T03:04:05Z", "branch": "old"})
    )
    lines = pstack_usage.report(env.records).splitlines()
    assert lines[0].split()[0] == "updated"
    assert "pstack" in lines[1] and lines[2].startswith("2020-01-02 03:04  old")


def test_record_dir_prefers_env(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("PSTACK_USAGE_DIR", str(tmp_path))
    assert pstack_usage.record_dir() == tmp_path
