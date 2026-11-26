import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POTETO = "---\nname: poteto-mode\ndisable-model-invocation: true\n---\n\nbody\n"


def install(home: Path, *args: str) -> str:
    env = {**os.environ, "HOME": str(home), "PATH": "/usr/bin:/bin"}
    done = subprocess.run(
        ["bash", str(ROOT / "install.sh"), *args],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout


def fake_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    skill = home / ".claude/plugins/cache/x/pstack/0.15.48/skills/poteto-mode"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(POTETO, encoding="utf-8")
    return home


def test_install_links_plugin_and_writes_rules(tmp_path: Path) -> None:
    home = fake_home(tmp_path)
    install(home)
    claude = home / ".claude"
    assert (claude / "skills/devkit").resolve() == ROOT
    auto = (claude / "skills/poteto-mode-auto/SKILL.md").read_text(encoding="utf-8")
    assert "name: poteto-mode-auto" in auto
    assert "disable-model-invocation" not in auto
    rules = claude / "rules"
    assert (rules / "pstack-principles.md").read_bytes() == (
        ROOT / "rules/pstack-principles.md"
    ).read_bytes()
    assert (rules / "pstack-models.md").is_file()
    assert not (rules / "pstack-codex.md").exists()


def test_rerun_keeps_own_model_rule_and_refreshes_principles(tmp_path: Path) -> None:
    home = fake_home(tmp_path)
    rules = home / ".claude/rules"
    rules.mkdir(parents=True)
    (rules / "pstack-models.md").write_text("mine\n", encoding="utf-8")
    (rules / "pstack-principles.md").write_text("old\n", encoding="utf-8")
    install(home)
    install(home)
    assert (rules / "pstack-models.md").read_text(encoding="utf-8") == "mine\n"
    assert (rules / "pstack-principles.md").read_text(encoding="utf-8") != "old\n"


def test_copy_mode_makes_a_real_directory(tmp_path: Path) -> None:
    home = fake_home(tmp_path)
    install(home)
    install(home, "--copy")
    dest = home / ".claude/skills/devkit"
    assert dest.is_dir() and not dest.is_symlink()
    assert (dest / ".claude-plugin/plugin.json").is_file()
